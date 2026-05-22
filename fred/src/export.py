import csv
import os
import re
from datetime import datetime


def _normalize_date(value, fmt):
    """Parse value with the given strptime format and return YYYY-MM-DD. Returns value unchanged on failure."""
    if not fmt or not value:
        return value
    try:
        return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
    except ValueError:
        return value


def _build_tech_type_index(mapping):
    """Invert technology_type_mapping → {fred_technique: mage_tab_term}."""
    index = {}
    for mage_term, fred_list in (mapping.get("technology_type_mapping") or {}).items():
        for fred_technique in (fred_list or []):
            index[fred_technique] = mage_term
    return index


def _build_tech_lookup(metadata, tech_type_index):
    """Returns {setting_id: "mage_tab_tech_type"} from technical_details."""
    tech_details = metadata.get("technical_details") or {}
    techniques = tech_details.get("techniques") or []
    lookup = {}
    for entry in techniques:
        sid = entry.get("setting")
        tech_list = entry.get("technique") or []
        if sid:
            mapped = [tech_type_index.get(t, t) for t in tech_list if t]
            # Deduplicate while preserving order (e.g. two sequencing techniques → one term)
            seen = set()
            unique = [t for t in mapped if not (t in seen or seen.add(t))]
            lookup[sid] = ";".join(unique)
    return lookup


def _extract_factor_name(col_header):
    """'Factor Value[injury]' → 'injury'"""
    m = re.match(r"Factor Value\[(.+)\]", col_header)
    return m.group(1) if m else col_header


def _walk(node, keys):
    """
    Traverse a nested dict/list structure along a sequence of keys.
    When a list is encountered, each element is traversed and results are collected.
    When a list value is encountered during collection, inner lists are joined with ', '.
    Returns the final node (may be a list, dict, scalar, or None).
    """
    for key in keys:
        if node is None:
            return None
        if isinstance(node, list):
            collected = []
            for item in node:
                if not isinstance(item, dict):
                    continue
                val = item.get(key)
                if val is None:
                    continue
                if isinstance(val, list):
                    # Inner list (e.g. author names per publication) → join as one string
                    joined = ", ".join(str(v) for v in val if v is not None)
                    if joined:
                        collected.append(joined)
                else:
                    collected.append(val)
            node = collected if collected else None
        elif isinstance(node, dict):
            node = node.get(key)
        else:
            # scalar — can't go deeper; return current value (remaining keys ignored)
            return node
    return node


def _node_to_str(node):
    """Convert a resolved node to a single string. Lists are joined with ';'."""
    if node is None:
        return ""
    if isinstance(node, list):
        return ";".join(str(item) for item in node if item is not None and not isinstance(item, (dict, list)))
    return str(node)


def _node_to_list(node):
    """Convert a resolved node to a list of strings (one entry per list element)."""
    if node is None:
        return []
    if isinstance(node, list):
        return [str(item) for item in node if item is not None and not isinstance(item, (dict, list))]
    return [str(node)]


def _resolve_single_str(path, scope_context):
    """
    Resolve a dotted path to a single string.
    Unknown scope prefix → treat as literal.
    """
    parts = path.split(".")
    scope = parts[0]
    keys = parts[1:]

    if scope not in scope_context:
        return path  # literal

    node = _walk(scope_context[scope], keys)
    return _node_to_str(node)


def _resolve_single_list(path, scope_context):
    """
    Resolve a dotted path to a list of strings.
    Used for IDF fields where each publication → one tab column.
    Unknown scope prefix → [literal].
    """
    parts = path.split(".")
    scope = parts[0]
    keys = parts[1:]

    if scope not in scope_context:
        return [path]  # literal

    node = _walk(scope_context[scope], keys)
    return _node_to_list(node)


def _resolve_path_str(path_spec, scope_context):
    """Resolve a path spec (str or list[str]) to a single string (SDRF use)."""
    if isinstance(path_spec, list):
        parts = [_resolve_single_str(p, scope_context) for p in path_spec]
        return " ".join(p for p in parts if p)
    return _resolve_single_str(path_spec, scope_context)


def _resolve_idf_spec(spec, scope_context):
    """
    Resolve an IDF field spec.
    Returns list[str] (one entry per tab column) or None to skip the row.

    spec may be:
      str           → path or literal
      list[str]     → multi-path (space-joined single value)
      dict          → {literal: "...", condition: "path"}
    """
    if isinstance(spec, dict):
        cond = spec.get("condition", "")
        if cond:
            cond_val = _resolve_single_str(cond, scope_context)
            if not cond_val:
                return None  # condition not met
        literal = spec.get("literal", "")
        return [literal] if literal else None

    if isinstance(spec, list):
        val = _resolve_path_str(spec, scope_context)
        return [val] if val else None

    # Single path string — may resolve to a list (e.g. publication.pubmed_id)
    values = _resolve_single_list(spec, scope_context)
    return values if values else None


class MageTabExporter:

    def __init__(self, metadata, mapping, setting_filter=None):
        self.metadata = metadata
        self.mapping = mapping
        self.scopes = mapping.get("scopes", {})
        self.setting_filter = setting_filter

    def _active_settings(self):
        for setting in self.metadata.get("experimental_setting") or []:
            sid = setting.get("setting_id", "")
            if self.setting_filter and sid not in self.setting_filter:
                continue
            yield setting

    def _project_ctx(self):
        return {"project": self.metadata.get("project") or {}}

    def _get_active_factor_names(self):
        """Return factor names that have at least one value in the active settings."""
        seen = set()
        active = []
        for col_header, path_spec in (self.mapping.get("factor_values") or {}).items():
            factor_name = _extract_factor_name(col_header)
            if factor_name in seen:
                continue
            for setting in self._active_settings():
                found = False
                for condition in setting.get("conditions") or []:
                    for sample in (condition.get("biological_replicates") or {}).get("samples") or []:
                        ctx = {"sample": sample, "setting": setting,
                               "project": self.metadata.get("project") or {}}
                        if _resolve_path_str(path_spec, ctx):
                            found = True
                            break
                    if found:
                        break
                if found:
                    active.append(factor_name)
                    seen.add(factor_name)
                    break
        return active

    def to_idf(self, sdrf_filename):
        lines = []
        ctx = self._project_ctx()
        date_fmt = self.mapping.get("date_input_format", "")

        for field_name, spec in (self.mapping.get("idf") or {}).items():
            values = _resolve_idf_spec(spec, ctx)
            if values:
                if "date" in field_name.lower():
                    values = [_normalize_date(v, date_fmt) for v in values]
                lines.append(field_name + "\t" + "\t".join(values))

        active_factors = self._get_active_factor_names()
        if active_factors:
            lines.append("Experimental Factor Name\t" + "\t".join(active_factors))
            lines.append("Experimental Factor Type\t" + "\t".join(active_factors))

        lines.append("SDRF File\t" + sdrf_filename)
        return "\n".join(lines) + "\n"

    def to_sdrf(self):
        tech_type_index = _build_tech_type_index(self.mapping)
        tech_lookup = _build_tech_lookup(self.metadata, tech_type_index)
        char_map = self.mapping.get("characteristics") or {}
        fv_map   = self.mapping.get("factor_values") or {}
        all_settings = list(self._active_settings())
        multi_setting = len(all_settings) > 1

        rows = []
        for setting in all_settings:
            sid = setting.get("setting_id", "")
            tech = tech_lookup.get(sid, "")
            for condition in setting.get("conditions") or []:
                bio_reps = (condition.get("biological_replicates") or {}).get("samples") or []
                for bio_idx, sample in enumerate(bio_reps, start=1):
                    tech_reps = sample.get("technical_replicates") or {}
                    tech_names = tech_reps.get("sample_name") or []
                    filenames  = tech_reps.get("filenames") or []
                    ctx = {"sample": sample, "setting": setting,
                           "project": self.metadata.get("project") or {}}
                    for tech_idx, assay_name in enumerate(tech_names, start=1):
                        filename = filenames[tech_idx - 1] if (tech_idx - 1) < len(filenames) else ""
                        # MAGE-TAB column order:
                        # source name → characteristics → assay name → technology type
                        #   → comment columns → factor value columns (must be last)
                        row = {"source name": sample.get("sample_name", "")}
                        row["characteristics[biological replicate]"] = str(bio_idx)
                        for col, path_spec in char_map.items():
                            row[col] = _resolve_path_str(path_spec, ctx)
                        row["assay name"] = assay_name
                        row["technology type"] = tech
                        row["comment[technical replicate]"] = str(tech_idx)
                        row["comment[data file]"] = filename
                        if multi_setting:
                            row["comment[experimental setting]"] = sid
                        for col, path_spec in fv_map.items():
                            row[col] = _resolve_path_str(path_spec, ctx)
                        rows.append(row)

        if not rows:
            return rows

        # All columns are kept — empty ones remain as empty strings so that
        # required columns (e.g. characteristics[organism part]) are always present.
        all_cols = list(rows[0].keys())
        return [{col: row.get(col, "") for col in all_cols} for row in rows]

    def export(self, output_dir, filename=None):
        project_id = (self.metadata.get("project") or {}).get("id", "export")
        base = filename or project_id
        output_dir = str(output_dir) if output_dir else "."
        os.makedirs(output_dir, exist_ok=True)

        idf_filename = base + ".idf.txt"
        sdrf_filename = base + ".sdrf.txt"
        idf_path = os.path.join(output_dir, idf_filename)
        sdrf_path = os.path.join(output_dir, sdrf_filename)

        sdrf_rows = self.to_sdrf()

        with open(idf_path, "w", newline="", encoding="utf-8") as f:
            f.write(self.to_idf(sdrf_filename))

        if sdrf_rows:
            headers = list(sdrf_rows[0].keys())
            with open(sdrf_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t",
                                        extrasaction="ignore")
                writer.writeheader()
                writer.writerows(sdrf_rows)
        else:
            open(sdrf_path, "w", encoding="utf-8").close()

        return idf_path, sdrf_path
