"""
Tests for fred/src/file_reading.py — directory iteration and YAML reading.
"""
import sys
import os
from unittest.mock import patch

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.file_reading as file_reading
import fred.src.utils as utils

FILENAME_SUFFIX = "_metadata"


# ---------------------------------------------------------------------------
# iterate_dir_metafiles
# ---------------------------------------------------------------------------


def test_finds_metadata_yaml_file(key_yaml, tmp_metadata_dir):
    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, reports = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_metadata_dir)],
            filename=FILENAME_SUFFIX,
            return_false=True,
            skip_validation=True,
        )
    assert len(metafiles) == 1
    assert metafiles[0]["project"]["id"] == "test001"


def test_skips_non_metadata_yaml_files(key_yaml, tmp_path):
    # Create a YAML file that does NOT match the *_metadata.yaml pattern
    other = tmp_path / "config.yaml"
    other.write_text("key: value\n")
    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, _ = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_path)],
            filename=FILENAME_SUFFIX,
            return_false=True,
            skip_validation=True,
        )
    assert metafiles == []


def test_empty_directory_returns_empty_lists(key_yaml, tmp_path):
    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, reports = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_path)],
            filename=FILENAME_SUFFIX,
            return_false=True,
            skip_validation=True,
        )
    assert metafiles == []


def test_corrupt_yaml_reported(key_yaml, tmp_path):
    # Write a file that matches the naming pattern but contains invalid YAML
    corrupt = tmp_path / "bad_metadata.yaml"
    corrupt.write_text("project: {unclosed: [bracket\n")
    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, reports = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_path)],
            filename=FILENAME_SUFFIX,
            return_false=True,
            skip_validation=True,
        )
    # Corrupt file should not appear in valid metafiles
    assert all(m.get("project", {}).get("id") != "bad" for m in metafiles)


def test_finds_multiple_metadata_files(key_yaml, tmp_path):
    # Write two valid metadata files
    for i in range(1, 3):
        data = {
            "project": {
                "id": f"test00{i}",
                "project_name": f"Project {i}",
                "date": "01.01.2024",
                "description": f"Project {i} description",
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
                    "experimental_factors": [{"factor": "strain", "values": ["WT"]}],
                    "conditions": [
                        {
                            "condition_name": 'strain:"WT"',
                            "biological_replicates": {"count": 0, "samples": []},
                        }
                    ],
                }
            ],
            "technical_details": {
                "techniques": [{"setting": "exp1", "technique": ["bulk RNA-seq"]}]
            },
        }
        path = tmp_path / f"test00{i}_metadata.yaml"
        utils.save_as_yaml(data, str(path))

    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, _ = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_path)],
            filename=FILENAME_SUFFIX,
            return_false=True,
            skip_validation=True,
        )
    assert len(metafiles) == 2
    ids = {m["project"]["id"] for m in metafiles}
    assert ids == {"test001", "test002"}
