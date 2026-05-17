import io
import os
import re
import warnings
import zipfile

import openpyxl

from fred.src.export import (
    _resolve_path_str,
    _resolve_idf_spec,
)

# Row at which we insert extra rows when >13 samples (0-indexed = 51, 1-indexed = 52)
_INSERT_ROW_0IDX = 51
_TEMPLATE_SAMPLE_ROWS = 13


def _patch_sheet1_xml(xml_bytes: bytes) -> bytes:
    """Fix drawing references that openpyxl replaces with its own rIds."""
    xml = xml_bytes.decode("utf-8")
    # openpyxl omits xmlns:r on the worksheet element; add it so rId refs are valid
    xml = xml.replace(
        'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        1,
    )
    # openpyxl: <legacyDrawing xmlns:r="..." r:id="anysvml"/>
    # template:  <drawing r:id="rId2"/><legacyDrawing r:id="rId3"/>
    xml = re.sub(
        r'<legacyDrawing\s.*?/>',
        '<drawing r:id="rId2"/><legacyDrawing r:id="rId3"/>',
        xml,
        flags=re.DOTALL,
    )
    return xml.encode("utf-8")


def _shift_xml_rows(content: bytes, tag: str, offset: int) -> bytes:
    """Increment every <tag>N</tag> value that is >= _INSERT_ROW_0IDX by offset."""
    pattern = re.compile(r'(<' + re.escape(tag) + r'>)(\d+)(</' + re.escape(tag) + r'>)')

    def _replace(m):
        n = int(m.group(2))
        return m.group(1) + str(n + offset if n >= _INSERT_ROW_0IDX else n) + m.group(3)

    return pattern.sub(_replace, content.decode("utf-8")).encode("utf-8")


def _shift_vml_anchors(content: bytes, offset: int) -> bytes:
    """Shift row values inside VML <x:Anchor> elements (format: c1,dx1,r1,dy1,c2,dx2,r2,dy2)."""
    def _replace(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) == 8:
            for idx in (2, 6):  # row1 and row2 positions
                n = int(parts[idx])
                if n >= _INSERT_ROW_0IDX:
                    parts[idx] = str(n + offset)
        return "<x:Anchor>" + ", ".join(parts) + "</x:Anchor>"

    return re.sub(r"<x:Anchor>(.*?)</x:Anchor>", _replace,
                  content.decode("utf-8"), flags=re.DOTALL).encode("utf-8")

# Fixed cell rows for STUDY section (column B = 2)
_STUDY_ROW = {
    "*title": 12,
    "*summary (abstract)": 13,
    # "*experimental design" → row 14, always auto-generated
    "contributor": 15,  # first slot; multiple values → B15, B16, …
}

# Fixed cell rows for PROTOCOLS section (column B = 2)
_PROTOCOL_ROW = {
    "growth protocol": 57,
    "treatment protocol": 58,
    "*extract protocol": 59,
    "*library construction protocol": 60,
    "*data processing step": 62,
    "*genome build/assembly": 67,
    "*processed data files format and content": 68,
}

# SAMPLES layout constants
_SAMPLES_HEADER_ROW = 38
_SAMPLES_DATA_ROW = 39
_SAMPLES_FIRST_DYN_COL = 5    # column E — first dynamic column (tissue/cell_line/cell_type)

# Library columns written after all characteristics, in this order
_SAMPLES_LIBRARY_FIELDS = [
    "*molecule",
    "*single or paired-end",
    "*instrument model",
    "description",
    "processed data file",
    "processed data file",
]


def _format_contributor(name: str) -> str:
    """Convert FRED 'Lastname[, First[ Middle]]' → GEO 'First[, Middle], Lastname'.

    FRED convention: surname first, given names after the first comma.
    Spaces within the given-name segment are treated as separators between
    first name and middle name(s).
    If the name has no comma it is returned unchanged (not in expected format).
    """
    if not name:
        return name
    parts = [p.strip() for p in name.split(",") if p.strip()]
    if len(parts) < 2:
        # No comma — assume "Firstname [Middle...] Lastname" (space-separated)
        tokens = name.split()
        if len(tokens) < 2:
            return name
        lastname = tokens[-1]
        given_tokens = tokens[:-1]
    else:
        lastname = parts[0]
        given_tokens = " ".join(parts[1:]).split()
    if not given_tokens:
        return name
    first = given_tokens[0]
    middles = [t[0].upper() for t in given_tokens[1:]]
    return ", ".join([first] + middles + [lastname])


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
                    tech_names = tech_reps.get("sample_name") or []
                    filenames = tech_reps.get("filenames") or []

                    chars = {}
                    for char_name, path_spec in char_map.items():
                        val = _resolve_path_str(path_spec, ctx)
                        if val:
                            chars[char_name] = val

                    for i, tech_name in enumerate(tech_names):
                        filename = filenames[i] if i < len(filenames) else ""
                        rows.append({
                            "*library name": tech_name,
                            "*title": filename,
                            "library strategy": strategy,
                            "*organism": org,
                            "**tissue": _resolve_path_str("sample.tissue", ctx),
                            "**cell line": _resolve_path_str("sample.cell_line", ctx),
                            "**cell type": _resolve_path_str("sample.cell_type", ctx),
                            "*molecule": molecule,
                            "_raw_files": [filename] if filename else [],
                            "_chars": chars,
                        })

        return rows

    def to_workbook(self):
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "seq_template.xlsx"
        )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning,
                                    message="Data Validation extension")
            wb = openpyxl.load_workbook(template_path)
        ws = wb["Metadata"]

        project = self.metadata.get("project") or {}
        ctx_project = {"project": project}
        tech_lookup = _build_tech_lookup_list(self.metadata)
        strategy_idx, molecule_idx = self._build_library_indices()
        settings_data = [
            (s, tech_lookup.get(s.get("setting_id", ""), []))
            for s in self._active_settings()
        ]

        # === STUDY ===
        for field, spec in (self.mapping.get("study") or {}).items():
            base_row = _STUDY_ROW.get(field)
            if base_row is None:
                continue
            values = _resolve_idf_spec(spec, ctx_project) or []
            if field == "contributor":
                values = [_format_contributor(v) for v in values]
            for i, v in enumerate(values):
                ws.cell(base_row + i, 2, v)
        ws.cell(14, 2, self._overall_design(settings_data))

        # === PROTOCOLS (written after SAMPLES insert so row numbers are final) ===
        # Deferred: see below after sample row count is known

        # === SAMPLES ===
        sample_rows = self._collect_sample_rows(
            strategy_idx, molecule_idx, project, tech_lookup
        )

        # The template has 13 pre-allocated data rows (39–51) before PROTOCOLS at 54.
        # For larger datasets insert extra rows at 52 so PROTOCOLS shift down naturally.
        extra_rows = max(0, len(sample_rows) - _TEMPLATE_SAMPLE_ROWS)
        self._extra_rows = extra_rows
        if extra_rows > 0:
            ws.insert_rows(52, extra_rows)

        # Adjust protocol row numbers if rows were inserted
        adjusted_protocol_row = (
            {k: v + extra_rows for k, v in _PROTOCOL_ROW.items()}
            if extra_rows > 0
            else _PROTOCOL_ROW
        )

        char_map = self.mapping.get("sample_characteristics") or {}
        active_chars = [
            c for c in char_map
            if any(r["_chars"].get(c) for r in sample_rows)
        ]
        n_chars = len(active_chars)
        max_raw = max((len(r["_raw_files"]) for r in sample_rows), default=1)

        # Determine which geo fixed columns (tissue/cell_line/cell_type) to include.
        # If none have data: include all three with "TO FILL".
        # Otherwise: include only those with data.
        has_tissue    = any(r["**tissue"]    for r in sample_rows)
        has_cell_line = any(r["**cell line"] for r in sample_rows)
        has_cell_type = any(r["**cell type"] for r in sample_rows)
        none_present  = not (has_tissue or has_cell_line or has_cell_type)
        _geo_fixed = [
            ("**tissue",    "**tissue"),
            ("**cell line", "**cell line"),
            ("**cell type", "**cell type"),
        ]
        _has = {"**tissue": has_tissue, "**cell line": has_cell_line, "**cell type": has_cell_type}
        geo_chars = _geo_fixed if none_present else [(h, k) for h, k in _geo_fixed if _has[h]]

        first_char_col = _SAMPLES_FIRST_DYN_COL + len(geo_chars)
        first_lib_col  = first_char_col + n_chars
        first_raw_col  = first_lib_col + len(_SAMPLES_LIBRARY_FIELDS)

        # Clear template's pre-existing headers from column E onwards before writing ours
        for col in range(_SAMPLES_FIRST_DYN_COL, _SAMPLES_FIRST_DYN_COL + 60):
            ws.cell(_SAMPLES_HEADER_ROW, col).value = None

        # Write dynamic headers in row 38, starting at column E
        for i, (header, _) in enumerate(geo_chars):
            ws.cell(_SAMPLES_HEADER_ROW, _SAMPLES_FIRST_DYN_COL + i, header)
        for i, char_name in enumerate(active_chars):
            ws.cell(_SAMPLES_HEADER_ROW, first_char_col + i, char_name)
        for i, lib_field in enumerate(_SAMPLES_LIBRARY_FIELDS):
            ws.cell(_SAMPLES_HEADER_ROW, first_lib_col + i, lib_field)
        for i in range(max_raw):
            ws.cell(_SAMPLES_HEADER_ROW, first_raw_col + i,
                    "*raw file" if i == 0 else "raw file")

        # Write data rows
        for row_idx, r in enumerate(sample_rows, start=_SAMPLES_DATA_ROW):
            ws.cell(row_idx, 1, r["*library name"])
            ws.cell(row_idx, 2, r["*title"])
            ws.cell(row_idx, 3, r["library strategy"])
            ws.cell(row_idx, 4, r["*organism"])
            for i, (_, key) in enumerate(geo_chars):
                ws.cell(row_idx, _SAMPLES_FIRST_DYN_COL + i,
                        "TO FILL" if none_present else r[key])
            for i, char_name in enumerate(active_chars):
                ws.cell(row_idx, first_char_col + i, r["_chars"].get(char_name, ""))
            ws.cell(row_idx, first_lib_col,     r["*molecule"])
            ws.cell(row_idx, first_lib_col + 1, "paired-end")
            ws.cell(row_idx, first_lib_col + 2, "[TO BE FILLED]")
            # description (first_lib_col + 3) and processed data files: left empty
            for fi, fname in enumerate(r["_raw_files"]):
                ws.cell(row_idx, first_raw_col + fi, fname)

        # Write PROTOCOLS with adjusted row numbers
        for field, value in (self.mapping.get("protocols") or {}).items():
            row = adjusted_protocol_row.get(field)
            if row:
                ws.cell(row, 2, value)

        return wb

    def export(self, output_dir, filename=None):
        project_id = (self.metadata.get("project") or {}).get("id", "export")
        base = filename or project_id
        output_dir = str(output_dir) if output_dir else "."
        os.makedirs(output_dir, exist_ok=True)
        xlsx_path = os.path.join(output_dir, base + ".xlsx")

        template_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "seq_template.xlsx"
        )

        # Generate openpyxl workbook (sets self._extra_rows as side-effect)
        wb = self.to_workbook()
        buf = io.BytesIO()
        wb.save(buf)
        extra = getattr(self, "_extra_rows", 0)

        # Zip surgery: preserve template drawings/VML/comments; only replace
        # sheet1.xml (openpyxl uses inlineStr, no sharedStrings needed).
        with (
            zipfile.ZipFile(io.BytesIO(buf.getvalue())) as openpyxl_zip,
            zipfile.ZipFile(template_path) as tmpl_zip,
            zipfile.ZipFile(xlsx_path, "w", zipfile.ZIP_DEFLATED) as out_zip,
        ):
            for name in tmpl_zip.namelist():
                if name == "xl/worksheets/sheet1.xml":
                    continue
                data = tmpl_zip.read(name)
                if extra > 0:
                    if name == "xl/drawings/vmlDrawing1.vml":
                        data = _shift_xml_rows(data, "x:Row", extra)
                        data = _shift_vml_anchors(data, extra)
                    elif name == "xl/drawings/drawing1.xml":
                        data = _shift_xml_rows(data, "xdr:row", extra)
                out_zip.writestr(name, data)

            # Patched sheet1.xml: restore drawing rId references lost by openpyxl
            out_zip.writestr(
                "xl/worksheets/sheet1.xml",
                _patch_sheet1_xml(openpyxl_zip.read("xl/worksheets/sheet1.xml")),
            )

        return xlsx_path
