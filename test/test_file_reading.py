"""
Tests for fred/src/file_reading.py — directory iteration and YAML reading.
"""
import copy
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


# ---------------------------------------------------------------------------
# version gate (validate())
# ---------------------------------------------------------------------------


def test_validate_worker_flags_version_mismatch(key_yaml, tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_fred_version", lambda: "3.0.0")
    path = tmp_path / "test_metadata.yaml"
    utils.save_as_yaml({"project": {"id": "test_stale"}, "version": "2.0.0"}, str(path))

    metafile, corrupted, error_reports, error_count, warning_reports, warning_count, _ = (
        file_reading.validate(
            str(path), FILENAME_SUFFIX, key_yaml, False, None, key_yaml, skip_validation=False
        )
    )

    assert corrupted is True
    assert error_count == 1
    assert "fred migrate 3.0.0" in error_reports[0][0]


def test_validate_worker_bypasses_version_gate_when_skip_validation(key_yaml, tmp_path, monkeypatch):
    # skip_validation=True is the flag fred/migrations/v3_0_0/migrate.py relies
    # on to deliberately process pre-migration files -- it must bypass the
    # version gate too, not just schema/whitelist validation
    monkeypatch.setattr(utils, "get_fred_version", lambda: "3.0.0")
    path = tmp_path / "test_metadata.yaml"
    utils.save_as_yaml({"project": {"id": "test_stale"}, "version": "2.0.0"}, str(path))

    metafile, corrupted, error_reports, error_count, warning_reports, warning_count, _ = (
        file_reading.validate(
            str(path), FILENAME_SUFFIX, key_yaml, False, None, key_yaml, skip_validation=True
        )
    )

    assert corrupted is False
    assert error_count == 0
    assert metafile["project"]["id"] == "test_stale"


def test_version_mismatch_excluded_from_dir_results(key_yaml, valid_metadata_minimal, tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_fred_version", lambda: "3.0.0")
    good = copy.deepcopy(valid_metadata_minimal)
    stale = copy.deepcopy(valid_metadata_minimal)
    stale["project"]["id"] = "test_stale"
    stale["version"] = "2.0.0"
    utils.save_as_yaml(good, str(tmp_path / "test001_metadata.yaml"))
    utils.save_as_yaml(stale, str(tmp_path / "test_stale_metadata.yaml"))

    with patch("fred.src.utils.get_whitelist", return_value=None):
        metafiles, reports = file_reading.iterate_dir_metafiles(
            key_yaml,
            [str(tmp_path)],
            filename=FILENAME_SUFFIX,
            logical_validation=False,
        )

    # the stale file is excluded from the results, but the good neighbor is
    # still processed normally
    ids = {m["project"]["id"] for m in metafiles}
    assert ids == {"test001"}
    assert reports["corrupt_files"]["count"] == 1
    assert reports["error_count"] >= 1
