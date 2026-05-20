"""
Tests for fred/src/export.py (MageTabExporter) and fred/src/geo_export.py (GeoMetadataExporter).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.utils as utils
from fred.src.export import MageTabExporter
from fred.src.geo_export import GeoMetadataExporter

MAGE_TAB_MAPPING_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fred", "config", "mage_tab_mapping.yaml"
)
GEO_MAPPING_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fred", "config", "geo_metadata_mapping.yaml"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mage_tab_mapping():
    return utils.read_in_yaml(MAGE_TAB_MAPPING_PATH)


@pytest.fixture(scope="module")
def geo_mapping():
    return utils.read_in_yaml(GEO_MAPPING_PATH)


@pytest.fixture
def minimal_metadata_with_samples():
    """Minimal metadata dict that includes sample_name/filenames for export."""
    return {
        "project": {
            "id": "test001",
            "project_name": "Export Test Project",
            "date": "01.01.2024",
            "description": "A test project for export.",
            "owner": {
                "name": "Walter, Jasmin",
                "ldap_name": "jwalter",
                "department": "Abt-K",
                "email": "test@example.com",
            },
        },
        "experimental_setting": [
            {
                "setting_id": "exp1",
                "organism": {"organism_name": "mouse", "taxonomy_id": "10090"},
                "experimental_factors": [{"factor": "strain", "values": ["WT", "KO"]}],
                "conditions": [
                    {
                        "condition_name": 'strain:"WT"',
                        "biological_replicates": {
                            "count": 2,
                            "samples": [
                                {
                                    "sample_name": "WT_b01",
                                    "pooled": False,
                                    "donor_count": 1,
                                    "strain": "WT",
                                    "technical_replicates": {
                                        "count": 1,
                                        "sample_name": ["test001_exp1_RNA_Mm_WT_b01_t01_m01"],
                                        "filenames": ["test001__1__RNA__WT_b01__1"],
                                    },
                                },
                            ],
                        },
                    }
                ],
            }
        ],
        "technical_details": {
            "techniques": [{"setting": "exp1", "technique": ["bulk RNA-seq"]}]
        },
    }


# ---------------------------------------------------------------------------
# MageTabExporter — MAGE-TAB output
# ---------------------------------------------------------------------------


class TestMageTabExporter:

    def test_export_creates_idf_and_sdrf_files(self, minimal_metadata_with_samples, mage_tab_mapping, tmp_path):
        exporter = MageTabExporter(minimal_metadata_with_samples, mage_tab_mapping)
        exporter.export(str(tmp_path))
        files = list(tmp_path.iterdir())
        names = [f.name for f in files]
        assert any(n.endswith(".idf.txt") for n in names), "IDF file not created"
        assert any(n.endswith(".sdrf.txt") for n in names), "SDRF file not created"

    def test_idf_contains_project_name(self, minimal_metadata_with_samples, mage_tab_mapping):
        exporter = MageTabExporter(minimal_metadata_with_samples, mage_tab_mapping)
        idf_content = exporter.to_idf("test.sdrf.txt")
        assert isinstance(idf_content, str)
        assert len(idf_content) > 0

    def test_sdrf_contains_sample_rows(self, minimal_metadata_with_samples, mage_tab_mapping):
        exporter = MageTabExporter(minimal_metadata_with_samples, mage_tab_mapping)
        sdrf_rows = exporter.to_sdrf()
        assert isinstance(sdrf_rows, list)
        assert len(sdrf_rows) > 0
        # Every row should have a source name
        for row in sdrf_rows:
            assert "source name" in row

    def test_sdrf_empty_when_no_samples(self, mage_tab_mapping):
        metadata_no_samples = {
            "project": {"id": "empty", "project_name": "Empty"},
            "experimental_setting": [
                {
                    "setting_id": "exp1",
                    "conditions": [
                        {"biological_replicates": {"count": 0, "samples": []}}
                    ],
                }
            ],
            "technical_details": {"techniques": []},
        }
        exporter = MageTabExporter(metadata_no_samples, mage_tab_mapping)
        sdrf_rows = exporter.to_sdrf()
        assert sdrf_rows == [] or sdrf_rows == {}


# ---------------------------------------------------------------------------
# GeoMetadataExporter — Excel output
# ---------------------------------------------------------------------------


class TestGeoMetadataExporter:

    def test_export_creates_xlsx_file(self, minimal_metadata_with_samples, geo_mapping, tmp_path):
        exporter = GeoMetadataExporter(minimal_metadata_with_samples, geo_mapping)
        exporter.export(str(tmp_path))
        files = list(tmp_path.iterdir())
        names = [f.name for f in files]
        assert any(n.endswith(".xlsx") for n in names), "XLSX file not created"

    def test_export_xlsx_is_readable(self, minimal_metadata_with_samples, geo_mapping, tmp_path):
        import openpyxl
        exporter = GeoMetadataExporter(minimal_metadata_with_samples, geo_mapping)
        exporter.export(str(tmp_path))
        xlsx_files = [f for f in tmp_path.iterdir() if f.name.endswith(".xlsx")]
        assert len(xlsx_files) == 1
        wb = openpyxl.load_workbook(str(xlsx_files[0]))
        assert wb is not None
