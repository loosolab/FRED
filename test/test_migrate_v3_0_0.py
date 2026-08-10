"""
Tests for fred/migrations/v3_0_0/migrate.py -- specifically that the version
key gets stamped on every processed file, even one with no organism/sample
content changes, so it doesn't stay stuck below the version gate forever.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.utils as utils
from fred.migrations.v3_0_0 import migrate


class _Args:
    def __init__(self, path):
        self.path = path
        self.config = "unused-because-_load_fred_context-is-mocked"
        self.apply = True
        self.regenerate_sample_names = False
        self.alias_file = "does-not-exist.yaml"
        self.output = "print"
        self.filename = "migration_report"


def _write_already_canonical_metafile(path):
    metafile = {
        "project": {"id": "test_stamp"},
        "experimental_setting": [
            {
                "setting_id": "exp1",
                "organism": {"organism_name": "Mus musculus", "taxonomy_id": "10090"},
                "conditions": [
                    {
                        "biological_replicates": {
                            "samples": [
                                {
                                    "sample_name": "s1",
                                    "number_of_measurements": 1,
                                    "technical_replicates": {},
                                }
                            ]
                        }
                    }
                ],
            }
        ],
        "version": "2.0.0",
    }
    utils.save_as_yaml(metafile, str(path))
    return metafile


def test_no_content_change_still_gets_version_stamped(tmp_path, key_yaml, monkeypatch):
    metafile_path = tmp_path / "test_stamp_metadata.yaml"
    _write_already_canonical_metafile(metafile_path)

    monkeypatch.setattr(
        migrate,
        "_load_fred_context",
        lambda config_path: (key_yaml, "unused-whitelist-path", "_metadata", str(tmp_path)),
    )
    monkeypatch.setattr(migrate, "get_organism_entries", lambda whitelist_path: {"Mus musculus": "10090"})
    monkeypatch.setattr(migrate, "get_abbrev_entries", lambda whitelist_path: {})
    monkeypatch.setattr(migrate, "get_abbrev_technique_entries", lambda whitelist_path: {})
    monkeypatch.setattr(utils, "get_fred_version", lambda: "3.0.0")

    migration = migrate.OrganismNameMigration()
    args = _Args(str(tmp_path))
    migration.run(args)

    result = utils.read_in_yaml(str(metafile_path))
    assert result["version"] == "3.0.0"
    # the organism was already canonical -- no organism/sample content change
    assert result["experimental_setting"][0]["organism"]["organism_name"] == "Mus musculus"


def test_dry_run_does_not_write_version(tmp_path, key_yaml, monkeypatch):
    metafile_path = tmp_path / "test_stamp_metadata.yaml"
    _write_already_canonical_metafile(metafile_path)

    monkeypatch.setattr(
        migrate,
        "_load_fred_context",
        lambda config_path: (key_yaml, "unused-whitelist-path", "_metadata", str(tmp_path)),
    )
    monkeypatch.setattr(migrate, "get_organism_entries", lambda whitelist_path: {"Mus musculus": "10090"})
    monkeypatch.setattr(migrate, "get_abbrev_entries", lambda whitelist_path: {})
    monkeypatch.setattr(migrate, "get_abbrev_technique_entries", lambda whitelist_path: {})
    monkeypatch.setattr(utils, "get_fred_version", lambda: "3.0.0")

    migration = migrate.OrganismNameMigration()
    args = _Args(str(tmp_path))
    args.apply = False
    migration.run(args)

    result = utils.read_in_yaml(str(metafile_path))
    assert result["version"] == "2.0.0"
