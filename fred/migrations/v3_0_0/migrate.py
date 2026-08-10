"""
FRED 3.0.0 migration: update organism_name values in existing metadata files.

The 'organism' whitelist (and its dependents 'gene', 'abbrev/gene_name',
'abbrev/organism_name') were migrated from informal/legacy names (e.g.
"human", or the intermediate "Homo_sapiens") to the current canonical form
(e.g. "Homo sapiens", split via the whitelist's "delimiter" field). Metadata
files generated before this migration still have the old organism_name value
stored, which no longer matches the current whitelist.

This migration only touches:
- experimental_setting[i].organism.organism_name (and taxonomy_id, kept in
  sync with the resolved organism_name)
- optionally (--regenerate-sample-names), technical_replicates.sample_name

Real-world old metadata turned out to use an even older sample_name template
than the current utils.create_sample_names (no setting_id, and the informal
organism_name embedded directly instead of a looked-up abbreviation), so
--regenerate-sample-names fully recomputes each sample's technical_replicates
.sample_name list from scratch using the current template and the already
-migrated organism_name, rather than patching a single token in place. Old
and new lists are matched up by sorting both and zipping them positionally;
if the recomputed count doesn't match what's stored, that sample is left
untouched and flagged for manual review instead of guessing.

condition_name and technical_replicates.filenames never contain organism
information and are never touched.
"""

import csv
import datetime
import os
import pathlib
import shutil

import openpyxl
from tabulate import tabulate

from fred.migrations.base import Migration
from fred.src import file_reading, git_whitelists, utils, validate_yaml

# terminal width used to size table columns so printed reports fit the
# terminal instead of overflowing/wrapping unpredictably (same approach as
# fred.src.find_metafiles)
try:
    _TERMINAL_COLUMNS = os.get_terminal_size().columns
except OSError:
    _TERMINAL_COLUMNS = 80


def _load_fred_context(config_path):
    (
        whitelist_repo,
        whitelist_branch,
        whitelist_path,
        name,
        token,
        structure_path,
        update_whitelists,
        output_path,
        filename,
        email,
    ) = utils.parse_config(config_path)
    git_whitelists.get_whitelists(
        whitelist_path, whitelist_repo, whitelist_branch, update_whitelists, name, token
    )
    structure = utils.read_in_yaml(structure_path)
    return structure, whitelist_path, filename, output_path


def _load_aliases(alias_file):
    if not os.path.isfile(alias_file):
        return {}
    aliases = utils.read_in_yaml(str(alias_file))
    return {str(k).strip().lower(): v for k, v in aliases.items()}


def get_organism_entries(whitelist_path):
    """Returns {organism_name: taxonomy_id} from the current organism whitelist."""
    organism_whitelist = utils.get_whitelist("organism", {}, whitelist_path=whitelist_path)
    delimiter = organism_whitelist.get("delimiter", " ")
    entries = {}
    for raw in organism_whitelist["whitelist"]:
        parsed = utils.header_value_to_dict(raw, organism_whitelist["headers"], delimiter)
        entries[parsed["organism_name"]] = parsed["taxonomy_id"]
    return entries


def get_abbrev_entries(whitelist_path):
    """Returns {organism_name: abbreviation} from the current abbrev/organism_name whitelist."""
    abbrev_whitelist = utils.get_whitelist(
        os.path.join("abbrev", "organism_name"), {}, whitelist_path=whitelist_path
    )
    return abbrev_whitelist["whitelist"]


def get_abbrev_technique_entries(whitelist_path):
    """Returns {technique: abbreviation} from the current abbrev/technique whitelist."""
    abbrev_whitelist = utils.get_whitelist(
        os.path.join("abbrev", "technique"), {}, whitelist_path=whitelist_path
    )
    return abbrev_whitelist["whitelist"]


def _get_used_techniques(metafile, setting_id):
    techniques = list(utils.find_keys(metafile, "techniques"))
    if not techniques:
        return None
    for entry in techniques[0]:
        if entry.get("setting") == setting_id:
            return entry.get("technique")
    return None


def _load_sample_field_defaults(defaults_file):
    """
    Loads the {field_name: default_value} table from `defaults_file` (see
    config/sample_field_defaults.yaml) -- sample-level fields that became
    mandatory in FRED 3.0.0 but may be missing from older metadata. Extend
    that file if a future schema change makes more sample fields mandatory.
    """
    if not os.path.isfile(defaults_file):
        return {}
    return utils.read_in_yaml(str(defaults_file))


def backfill_sample_fields(metafile, sample_field_defaults):
    """
    Adds any key in sample_field_defaults to every sample that's missing it,
    using the schema's own default value -- runs independently of organism
    migration/sample_name regeneration, since it's a separate completeness
    fix for now-mandatory fields.

    Returns a list of change dicts: {setting_id, sample, field, new, _ref}
    """
    changes = []
    for setting in metafile.get("experimental_setting", []) or []:
        setting_id = setting.get("setting_id", "?")
        for condition in setting.get("conditions", []) or []:
            samples = (condition.get("biological_replicates") or {}).get("samples", []) or []
            for sample in samples:
                for field, default in sample_field_defaults.items():
                    if field not in sample:
                        changes.append(
                            {
                                "setting_id": setting_id,
                                "sample": sample.get("sample_name", "?"),
                                "field": field,
                                "new": default,
                                "_ref": sample,
                            }
                        )
    return changes


def regenerate_sample_names(metafile, setting, new_organism_name, abbrev_entries, abbrev_tech_entries):
    """
    Recomputes technical_replicates.sample_name for every sample in `setting`
    from scratch, using the current sample-name template (matching
    utils.create_sample_names) and the already-resolved new_organism_name --
    rather than trying to patch the old string in place, since real old
    metadata turned out to use a different, older template entirely (no
    setting_id, informal organism_name embedded directly).

    Old and new lists are matched up by sorting both and zipping them
    positionally (both are `sorted(set(...))`-shaped, same as
    utils.create_sample_names produces, so this lines up correctly as long
    as the counts match). If the recomputed count doesn't match what's
    stored, that sample is left untouched and flagged instead of guessing.

    Returns (renames, warnings):
      renames: list of dicts {setting_id, old, new, _ref, _index}
      warnings: list of dicts {setting_id, value}
    """
    renames = []
    warnings = []
    setting_id = setting.get("setting_id", "?")
    project_id = (metafile.get("project") or {}).get("id", "")

    new_abbrev = abbrev_entries.get(new_organism_name)
    if new_abbrev is None:
        warnings.append(
            {
                "setting_id": setting_id,
                "value": f"no abbreviation found for '{new_organism_name}' in "
                f"abbrev/organism_name whitelist, sample_name left unchanged",
            }
        )
        return renames, warnings

    used_techs = _get_used_techniques(metafile, setting_id)
    if not used_techs:
        warnings.append(
            {
                "setting_id": setting_id,
                "value": "no technique found for this setting, sample_name left unchanged",
            }
        )
        return renames, warnings

    for condition in setting.get("conditions", []) or []:
        samples = (condition.get("biological_replicates") or {}).get("samples", []) or []
        for sample in samples:
            tech = sample.get("technical_replicates") or {}
            old_names = tech.get("sample_name")
            if not old_names:
                continue

            # both fields default to 1 in keys.yaml (technical_replicates.count
            # is mandatory but defaults to 1; number_of_measurements is
            # optional, "generated: fill" with value: 1 -- "typically 1" per
            # its own desc), so a missing field means 1, not 0.
            tech_count = tech.get("count") or 1
            measurements = sample.get("number_of_measurements") or 1
            b_name = sample.get("sample_name", "")

            new_names = []
            for used_tech in used_techs:
                abbrev_tech = abbrev_tech_entries.get(used_tech, used_tech)
                for t_count in range(1, tech_count + 1):
                    for m_count in range(1, measurements + 1):
                        new_names.append(
                            f"{project_id}_{setting_id}_{abbrev_tech}_{new_abbrev}_"
                            f"{b_name}_t{t_count:02d}_m{m_count:02d}"
                        )
            new_sorted = sorted(set(new_names))
            old_sorted = sorted(set(old_names))

            if len(new_sorted) != len(old_sorted):
                warnings.append(
                    {
                        "setting_id": setting_id,
                        "value": f"recomputed {len(new_sorted)} sample_name(s) for "
                        f"sample '{b_name}' but {len(old_sorted)} are stored -- "
                        f"left unchanged, please review manually",
                    }
                )
                continue

            for old, new in zip(old_sorted, new_sorted):
                if old != new:
                    renames.append(
                        {
                            "setting_id": setting_id,
                            "old": old,
                            "new": new,
                            "_ref": old_names,
                            "_index": old_names.index(old),
                        }
                    )

    return renames, warnings


def resolve_organism_name(value, organism_entries, aliases):
    """
    Resolve a stored organism_name value against the current whitelist.
    Returns (canonical_name, taxonomy_id), or None if it cannot be resolved.
    Never guesses across different organisms: every step below still
    requires an exact match once naming-convention differences (informal
    alias, underscore-vs-space, letter case) are normalized away.
    """
    if value in organism_entries:
        return value, organism_entries[value]

    alias_hit = aliases.get(value.strip().lower())
    if alias_hit and alias_hit in organism_entries:
        return alias_hit, organism_entries[alias_hit]

    normalized = value.replace("_", " ")
    if normalized in organism_entries:
        return normalized, organism_entries[normalized]

    # Case-insensitive fallback, e.g. real data had "caenorhabditis_elegans"
    # (lowercase Latin-with-underscore) against the whitelist's
    # "Caenorhabditis elegans" -- same organism, only casing differs.
    lowered = normalized.strip().lower()
    for canonical_name, taxonomy_id in organism_entries.items():
        if canonical_name.lower() == lowered:
            return canonical_name, taxonomy_id

    return None


class FileMigrationPlan:
    def __init__(self, path):
        self.path = path
        self.organism_changes = []
        self.sample_name_changes = []
        self.field_backfills = []
        # organism_name values that could not be mapped to the current
        # whitelist at all -- feeds the final "no match" summary.
        self.unresolved_organisms = []
        # anything else that stopped a change from being applied (e.g. a
        # sample's recomputed sample_name count doesn't match what's stored)
        # -- reported, but kept separate from the organism "no match" summary.
        self.warnings = []
        self.publication_flag = False
        # filled in by the runner after planning: "no changes", "dry-run",
        # "applied" or "skipped (backup exists)"
        self.status = "no changes"
        self.backup_path = None

    @property
    def has_changes(self):
        return bool(self.organism_changes or self.sample_name_changes or self.field_backfills)


def plan_file(
    metafile,
    organism_entries,
    abbrev_entries,
    abbrev_tech_entries,
    aliases,
    sample_field_defaults,
    do_regenerate_sample_names,
):
    plan = FileMigrationPlan(metafile.get("path"))
    plan.publication_flag = bool((metafile.get("project") or {}).get("publication"))
    plan.field_backfills = backfill_sample_fields(metafile, sample_field_defaults)

    for setting in metafile.get("experimental_setting", []) or []:
        setting_id = setting.get("setting_id", "?")
        organism = setting.get("organism")
        if not isinstance(organism, dict) or "organism_name" not in organism:
            continue

        old_name = organism["organism_name"]
        resolved = resolve_organism_name(old_name, organism_entries, aliases)
        if resolved is None:
            plan.unresolved_organisms.append({"setting_id": setting_id, "value": old_name})
            continue

        new_name, new_taxonomy_id = resolved
        old_taxonomy_id = organism.get("taxonomy_id")
        name_changed = new_name != old_name
        taxonomy_changed = str(old_taxonomy_id) != str(new_taxonomy_id)

        if name_changed or taxonomy_changed:
            plan.organism_changes.append(
                {
                    "setting_id": setting_id,
                    "old_name": old_name,
                    "new_name": new_name,
                    "old_taxonomy_id": old_taxonomy_id,
                    "new_taxonomy_id": new_taxonomy_id,
                    "_ref": organism,
                }
            )

        if do_regenerate_sample_names:
            # Deliberately independent of name_changed: organism_name may
            # already be current (e.g. fixed in an earlier run), but the
            # sample_name entries can still be stale and need regenerating.
            renames, warnings = regenerate_sample_names(
                metafile, setting, new_name, abbrev_entries, abbrev_tech_entries
            )
            plan.sample_name_changes.extend(renames)
            plan.warnings.extend(warnings)

    return plan


def apply_plan(plan):
    for change in plan.organism_changes:
        change["_ref"]["organism_name"] = change["new_name"]
        change["_ref"]["taxonomy_id"] = change["new_taxonomy_id"]
    for change in plan.sample_name_changes:
        change["_ref"][change["_index"]] = change["new"]
    for change in plan.field_backfills:
        change["_ref"][change["field"]] = change["new"]


def build_changes_rows(plans):
    rows = [["File", "Setting", "Field", "Old value", "New value"]]
    for plan in plans:
        for change in plan.organism_changes:
            rows.append(
                [plan.path, change["setting_id"], "organism_name", change["old_name"], change["new_name"]]
            )
            if str(change["old_taxonomy_id"]) != str(change["new_taxonomy_id"]):
                rows.append(
                    [
                        plan.path,
                        change["setting_id"],
                        "taxonomy_id",
                        change["old_taxonomy_id"],
                        change["new_taxonomy_id"],
                    ]
                )
        for change in plan.sample_name_changes:
            rows.append(
                [plan.path, change["setting_id"], "sample_name", change["old"], change["new"]]
            )
        for change in plan.field_backfills:
            rows.append(
                [
                    plan.path,
                    change["setting_id"],
                    f"{change['field']} [{change['sample']}]",
                    "(missing)",
                    change["new"],
                ]
            )
    return rows


def build_warning_rows(plans):
    rows = [["File", "Setting", "Warning"]]
    for plan in plans:
        for warning in plan.warnings:
            rows.append([plan.path, warning["setting_id"], warning["value"]])
    return rows


def build_unresolved_summary_rows(plans):
    """
    Aggregates unresolved organism_name values across all processed files:
    one row per distinct value, with the number of occurrences and the
    files/settings it was found in.
    """
    summary = {}
    for plan in plans:
        for entry in plan.unresolved_organisms:
            key = entry["value"]
            summary.setdefault(key, []).append(f"{plan.path} [{entry['setting_id']}]")

    rows = [["organism_name (no match)", "Occurrences", "Found in"]]
    for value, locations in sorted(summary.items(), key=lambda item: -len(item[1])):
        rows.append([value, len(locations), "; ".join(locations)])
    return rows


def build_file_status_rows(plans):
    rows = [["File", "Status", "Backup"]]
    for plan in plans:
        rows.append([plan.path, plan.status, plan.backup_path or ""])
    return rows


def build_sample_name_mapping_rows(plans):
    rows = [["File", "Setting", "Old sample_name", "New sample_name"]]
    for plan in plans:
        for change in plan.sample_name_changes:
            rows.append([plan.path, change["setting_id"], change["old"], change["new"]])
    return rows


def write_sample_name_mapping_csv(plans, output_path):
    rows = build_sample_name_mapping_rows(plans)
    with open(output_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def print_table(rows, empty_message, column_fractions=None):
    """
    Prints `rows` (first row = header) as a fancy_grid table, sized to fit
    the current terminal width. `column_fractions` is a list of fractions
    (one per column, roughly summing to 1) controlling each column's max
    width relative to the terminal width; defaults to an even split.
    """
    if len(rows) <= 1:
        print(empty_message)
        return
    num_columns = len(rows[0])
    if column_fractions is None:
        column_fractions = [1 / num_columns] * num_columns
    maxcolwidths = [max(int(_TERMINAL_COLUMNS * fraction), 10) for fraction in column_fractions]
    print(tabulate(rows, tablefmt="fancy_grid", headers="firstrow", maxcolwidths=maxcolwidths))


def write_xlsx_report(plans, output_path):
    workbook = openpyxl.Workbook()

    sheet = workbook.active
    sheet.title = "Changes"
    for row in build_changes_rows(plans):
        sheet.append(row)

    warnings_sheet = workbook.create_sheet("Warnings")
    for row in build_warning_rows(plans):
        warnings_sheet.append(row)

    unresolved_sheet = workbook.create_sheet("Unresolved organisms")
    for row in build_unresolved_summary_rows(plans):
        unresolved_sheet.append(row)

    files_sheet = workbook.create_sheet("Files")
    for row in build_file_status_rows(plans):
        files_sheet.append(row)

    mapping_sheet = workbook.create_sheet("Sample name mapping")
    for row in build_sample_name_mapping_rows(plans):
        mapping_sheet.append(row)

    workbook.save(output_path)


class OrganismNameMigration(Migration):
    version = "3.0.0"

    def add_arguments(self, parser):
        parser.add_argument(
            "-p",
            "--path",
            type=pathlib.Path,
            required=True,
            help="Path to a metadata file or a directory to search recursively",
        )
        parser.add_argument(
            "-c",
            "--config",
            type=pathlib.Path,
            default=os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "config.yaml",
            ),
            help="Config file",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually write changes (default: dry-run, report only)",
        )
        parser.add_argument(
            "--regenerate-sample-names",
            action="store_true",
            default=False,
            help="Also fully recompute technical_replicates.sample_name using the "
            "current template and the migrated organism_name; writes a separate "
            "old->new mapping file",
        )
        parser.add_argument(
            "--alias-file",
            type=pathlib.Path,
            default=os.path.join(os.path.dirname(__file__), "config", "organism_aliases.yaml"),
            help="Path to the informal-name alias table",
        )
        parser.add_argument(
            "--sample-field-defaults-file",
            type=pathlib.Path,
            default=os.path.join(
                os.path.dirname(__file__), "config", "sample_field_defaults.yaml"
            ),
            help="Path to the {field: default_value} table used to backfill "
            "sample fields that became mandatory but are missing",
        )
        parser.add_argument(
            "-o",
            "--output",
            default="print",
            choices=["print", "xlsx"],
            help="Print the report as a table (default) or save it as an Excel file",
        )
        parser.add_argument(
            "-f",
            "--filename",
            default="migration_report",
            help="Base filename (without extension) for the xlsx report",
        )

    def run(self, args):
        structure, whitelist_path, filename, output_path = _load_fred_context(args.config)
        aliases = _load_aliases(args.alias_file)
        sample_field_defaults = _load_sample_field_defaults(args.sample_field_defaults_file)
        organism_entries = get_organism_entries(whitelist_path)
        abbrev_entries = get_abbrev_entries(whitelist_path)
        abbrev_tech_entries = get_abbrev_technique_entries(whitelist_path)

        path = str(args.path)
        if os.path.isdir(path):
            metafiles, _ = file_reading.iterate_dir_metafiles(
                structure,
                [path],
                filename=filename,
                whitelist_path=whitelist_path,
                skip_validation=True,
                return_false=True,
            )
        else:
            metafile = utils.read_in_yaml(path)
            metafile["path"] = path
            metafiles = [metafile]

        plans = []
        for metafile in metafiles:
            file_path = metafile.pop("path")
            plan = plan_file(
                metafile,
                organism_entries,
                abbrev_entries,
                abbrev_tech_entries,
                aliases,
                sample_field_defaults,
                args.regenerate_sample_names,
            )
            plan.path = file_path
            plans.append(plan)

            if not args.apply:
                plan.status = "no changes needed" if not plan.has_changes else "dry-run (not applied)"
                continue

            # A file with no organism/sample_name/field changes still needs
            # to be stamped with the current FRED version below -- otherwise
            # it would remain stuck below the version gate forever, even
            # though its content already conforms to the current schema.
            # Only content-transforming changes get a backup; the version
            # stamp alone is a trivial, always-safe addition.
            if plan.has_changes:
                backup_path = f"{file_path}.bak"
                if os.path.exists(backup_path):
                    plan.status = "skipped (backup already exists)"
                    plan.backup_path = backup_path
                    continue
                shutil.copy2(file_path, backup_path)
                apply_plan(plan)
                plan.backup_path = backup_path
                status_prefix = "applied"
            else:
                status_prefix = "version stamped (no other changes needed)"

            metafile["version"] = utils.get_fred_version()
            utils.save_as_yaml(metafile, file_path)

            revalidated = utils.read_in_yaml(file_path)
            valid, *_ = validate_yaml.validate_file(
                revalidated, structure, filename, whitelist_path=whitelist_path
            )
            plan.status = status_prefix if valid else f"{status_prefix} (still invalid, please review)"

        if args.output == "xlsx":
            # Same reasoning as the sample_name mapping file below: an
            # --apply report documents an action actually taken and gets a
            # timestamp so it's never silently overwritten by a later run;
            # a dry-run report is just a preview and reuses the plain name.
            if args.apply:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                report_filename = f"{args.filename}_{timestamp}.xlsx"
            else:
                report_filename = f"{args.filename}.xlsx"
            report_path = os.path.join(output_path or ".", report_filename)
            write_xlsx_report(plans, report_path)
            print(f"Migration report saved to '{report_path}'.")
        else:
            print_table(
                build_changes_rows(plans),
                "No changes needed in any processed file.",
                column_fractions=[0.3, 0.1, 0.1, 0.25, 0.25],
            )
            print()
            print_table(
                build_warning_rows(plans),
                "No warnings.",
                column_fractions=[0.3, 0.1, 0.6],
            )
            print()
            print_table(
                build_file_status_rows(plans),
                "No files processed.",
                column_fractions=[0.4, 0.3, 0.3],
            )

        print()
        print_table(
            build_unresolved_summary_rows(plans),
            "No unresolved organism_name values -- every organism could be matched.",
            column_fractions=[0.2, 0.1, 0.7],
        )

        if args.regenerate_sample_names and any(plan.sample_name_changes for plan in plans):
            # Dry-run mappings are just a preview and safe to overwrite on
            # each re-run. An --apply mapping documents renames that were
            # actually written to disk, so it gets a timestamp instead of
            # silently replacing an earlier run's record.
            if args.apply:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                mapping_filename = f"{args.filename}_sample_name_mapping_{timestamp}.csv"
            else:
                mapping_filename = f"{args.filename}_sample_name_mapping.csv"
            mapping_path = os.path.join(output_path or ".", mapping_filename)
            write_sample_name_mapping_csv(plans, mapping_path)
            print()
            print(f"Sample name mapping (old -> new) saved to '{mapping_path}'.")

        if any(plan.has_changes for plan in plans) and not args.apply:
            print()
            print("Dry-run complete. Re-run with --apply to write these changes.")
        if any(plan.unresolved_organisms for plan in plans):
            print()
            print(
                "Some organism_name values could not be resolved automatically. "
                f"Add them to the alias file ('{args.alias_file}') and re-run, "
                "or fix them manually."
            )


MIGRATION = OrganismNameMigration()
