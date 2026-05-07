import os

import openpyxl
from openpyxl.styles import Font

from fred.src.export import (
    _resolve_path_str,
    _resolve_idf_spec,
)


def _factor_value_to_str(v):
    """Convert an experimental_factors value item to a readable string."""
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get("gene_name") or next(iter(v.values()), None)
    return str(v)


def _build_inverted_index(mapping_section):
    """Invert {geo_term: [fred_values]} → {fred_value: geo_term}."""
    idx = {}
    for term, fred_list in (mapping_section or {}).items():
        for fred_val in (fred_list or []):
            idx[fred_val] = term
    return idx


def _build_tech_lookup_list(metadata):
    """Returns {setting_id: [technique_names]} from technical_details."""
    tech_details = metadata.get("technical_details") or {}
    lookup = {}
    for entry in (tech_details.get("techniques") or []):
        sid = entry.get("setting")
        if sid:
            lookup[sid] = [t for t in (entry.get("technique") or []) if t]
    return lookup


class GeoMetadataExporter:

    def __init__(self, metadata, mapping, setting_filter=None):
        self.metadata = metadata
        self.mapping = mapping
        self.setting_filter = setting_filter

    def _active_settings(self):
        for setting in self.metadata.get("experimental_setting") or []:
            sid = setting.get("setting_id", "")
            if self.setting_filter and sid not in self.setting_filter:
                continue
            yield setting

    def _build_library_indices(self):
        return (
            _build_inverted_index(self.mapping.get("library_strategy_mapping")),
            _build_inverted_index(self.mapping.get("library_source_mapping")),
        )

    def _overall_design(self, settings_data):
        """Auto-generate *experimental design from experimental_factors."""
        parts = []
        multi = len(settings_data) > 1
        for setting, techniques in settings_data:
            sid = setting.get("setting_id", "")
            tech_str = ", ".join(techniques) if techniques else "unknown technique"
            factor_parts = []
            for f in setting.get("experimental_factors") or []:
                fname = f.get("factor", "")
                all_vals = []
                for val_dict in (f.get("values") or []):
                    if isinstance(val_dict, dict):
                        for v in val_dict.values():
                            if isinstance(v, list):
                                all_vals.extend(
                                    s for s in (_factor_value_to_str(x) for x in v)
                                    if s is not None
                                )
                            elif v is not None:
                                s = _factor_value_to_str(v)
                                if s is not None:
                                    all_vals.append(s)
                if fname and all_vals:
                    factor_parts.append(f"{fname} ({', '.join(all_vals)})")
            design = f"Samples analyzed by {tech_str}"
            if factor_parts:
                design += f" with experimental factors: {'; '.join(factor_parts)}"
            if multi:
                design = f"{sid}: {design}"
            parts.append(design)
        return " | ".join(parts)

    def _collect_sample_rows(self, strategy_idx, molecule_idx, project, tech_lookup):
        char_map = self.mapping.get("sample_characteristics") or {}
        rows = []

        for setting in self._active_settings():
            sid = setting.get("setting_id", "")
            techniques = tech_lookup.get(sid, [])
            org = ((setting.get("organism") or {}).get("organism_name") or "")
            primary_tech = techniques[0] if techniques else ""
            strategy = strategy_idx.get(primary_tech, primary_tech)
            molecule = molecule_idx.get(primary_tech, "")

            for condition in setting.get("conditions") or []:
                for sample in (condition.get("biological_replicates") or {}).get("samples") or []:
                    ctx = {"sample": sample, "setting": setting, "project": project}
                    tech_reps = sample.get("technical_replicates") or {}
                    filenames = tech_reps.get("filenames") or []

                    chars = {}
                    for char_name, path_spec in char_map.items():
                        val = _resolve_path_str(path_spec, ctx)
                        if val:
                            chars[char_name] = val

                    rows.append({
                        "*library name": sample.get("sample_name", ""),
                        "*title": sample.get("sample_name", ""),
                        "*organism": org,
                        "**tissue": _resolve_path_str("sample.tissue", ctx),
                        "**cell type": _resolve_path_str("sample.cell_type", ctx),
                        "*molecule": molecule,
                        "*single or paired-end": "paired-end",
                        "*instrument model": "[TO BE FILLED]",
                        "description": "",
                        "library strategy": strategy,
                        "processed data file": "",
                        "_raw_files": filenames,
                        "_chars": chars,
                    })

        return rows

    def to_workbook(self):
        bold = Font(bold=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Metadata"

        project = self.metadata.get("project") or {}
        ctx_project = {"project": project}
        tech_lookup = _build_tech_lookup_list(self.metadata)
        strategy_idx, molecule_idx = self._build_library_indices()

        settings_data = [
            (s, tech_lookup.get(s.get("setting_id", ""), []))
            for s in self._active_settings()
        ]

        # === STUDY ===
        ws.append(["STUDY"])
        ws.cell(ws.max_row, 1).font = bold

        for field, spec in (self.mapping.get("study") or {}).items():
            values = _resolve_idf_spec(spec, ctx_project)
            val = values[0] if values else ""
            ws.append([field, val or ""])
            if field == "*summary (abstract)":
                overall = self._overall_design(settings_data)
                ws.append(["*experimental design", overall])

        ws.append([""])

        # === PROTOCOLS ===
        ws.append(["PROTOCOLS"])
        ws.cell(ws.max_row, 1).font = bold

        for field, value in (self.mapping.get("protocols") or {}).items():
            ws.append([field, value])

        ws.append([""])

        # === SAMPLES ===
        ws.append(["SAMPLES"])
        ws.cell(ws.max_row, 1).font = bold

        sample_rows = self._collect_sample_rows(strategy_idx, molecule_idx, project, tech_lookup)

        max_raw = max((len(r.get("_raw_files", [])) for r in sample_rows), default=1)
        char_map = self.mapping.get("sample_characteristics") or {}
        active_chars = [
            c for c in char_map
            if any(r.get("_chars", {}).get(c) for r in sample_rows)
        ]

        headers = [
            "*library name", "*title", "*organism", "**tissue", "**cell type",
            "*molecule", "*single or paired-end", "*instrument model",
            "description", "library strategy", "processed data file",
        ] + ["raw file"] * max_raw + active_chars

        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            ws.cell(ws.max_row, col_idx).font = bold

        for r in sample_rows:
            raw_files = r.get("_raw_files", [])
            raw_padded = raw_files + [""] * (max_raw - len(raw_files))
            char_vals = [r.get("_chars", {}).get(c, "") for c in active_chars]
            ws.append([
                r["*library name"], r["*title"], r["*organism"],
                r["**tissue"], r["**cell type"], r["*molecule"],
                r["*single or paired-end"], r["*instrument model"],
                r["description"], r["library strategy"], r["processed data file"],
            ] + raw_padded + char_vals)

        return wb

    def export(self, output_dir, filename=None):
        project_id = (self.metadata.get("project") or {}).get("id", "export")
        base = filename or project_id
        output_dir = str(output_dir) if output_dir else "."
        os.makedirs(output_dir, exist_ok=True)

        xlsx_path = os.path.join(output_dir, base + ".xlsx")
        self.to_workbook().save(xlsx_path)
        return xlsx_path
