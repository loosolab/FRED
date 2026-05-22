"""
Tests for fred/src/find_metafiles.py — search logic with Boolean operators.
"""
import sys
import os
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.find_metafiles as find_metafiles
import fred.src.file_reading as file_reading


# ---------------------------------------------------------------------------
# Minimal metadata dict for search tests (no file I/O needed)
# ---------------------------------------------------------------------------

MOUSE_METADATA = {
    "project": {
        "id": "test001",
        "project_name": "Mouse RNA-seq",
        "description": "A test project",
        "date": "01.01.2024",
        "owner": {"name": "Walter, Jasmin", "email": "test@example.com"},
    },
    "experimental_setting": [
        {
            "setting_id": "exp1",
            "organism": {"organism_name": "mouse", "taxonomy_id": "10090"},
        }
    ],
    "path": "/tmp/test001_metadata.yaml",
}

HUMAN_METADATA = {
    "project": {
        "id": "test002",
        "project_name": "Human ATAC-seq",
        "description": "Another test project",
        "date": "01.01.2024",
        "owner": {"name": "Doe, John", "email": "doe@example.com"},
    },
    "experimental_setting": [
        {
            "setting_id": "exp1",
            "organism": {"organism_name": "human", "taxonomy_id": "9606"},
        }
    ],
    "path": "/tmp/test002_metadata.yaml",
}


# ---------------------------------------------------------------------------
# parse_search_parameters — unit tests (no file I/O)
# ---------------------------------------------------------------------------


def test_simple_match():
    result = find_metafiles.parse_search_parameters(MOUSE_METADATA, "organism_name:mouse")
    assert result is True


def test_simple_no_match():
    result = find_metafiles.parse_search_parameters(MOUSE_METADATA, "organism_name:human")
    assert result is False


def test_and_operator_both_match():
    result = find_metafiles.parse_search_parameters(
        MOUSE_METADATA, "organism_name:mouse and project_name:Mouse RNA-seq"
    )
    assert result is True


def test_and_operator_one_missing():
    result = find_metafiles.parse_search_parameters(
        MOUSE_METADATA, "organism_name:mouse and organism_name:human"
    )
    assert result is False


def test_or_operator_first_matches():
    result = find_metafiles.parse_search_parameters(
        MOUSE_METADATA, "organism_name:mouse or organism_name:human"
    )
    assert result is True


def test_or_operator_second_matches():
    result = find_metafiles.parse_search_parameters(
        HUMAN_METADATA, "organism_name:mouse or organism_name:human"
    )
    assert result is True


def test_or_operator_neither_matches():
    result = find_metafiles.parse_search_parameters(
        MOUSE_METADATA, "organism_name:zebrafish or organism_name:rat"
    )
    assert result is False


def test_not_operator_inverts_match():
    result = find_metafiles.parse_search_parameters(MOUSE_METADATA, "not organism_name:human")
    assert result is True


def test_not_operator_inverts_no_match():
    result = find_metafiles.parse_search_parameters(MOUSE_METADATA, "not organism_name:mouse")
    assert result is False


def test_nested_brackets_or_and(key_yaml, tmp_metadata_dir):
    """find_projects handles nested brackets in search string."""
    with patch("fred.src.utils.get_whitelist", return_value=None):
        result = find_metafiles.find_projects(
            key_yaml,
            str(tmp_metadata_dir),
            "organism_name:mouse or organism_name:human",
            return_dict=True,
            skip_validation=True,
        )
    assert isinstance(result, list)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# find_projects — integration with tmp_metadata_dir
# ---------------------------------------------------------------------------


def test_find_projects_returns_match(key_yaml, tmp_metadata_dir):
    with patch("fred.src.utils.get_whitelist", return_value=None):
        result = find_metafiles.find_projects(
            key_yaml,
            str(tmp_metadata_dir),
            "organism_name:mouse",
            return_dict=True,
            skip_validation=True,
        )
    assert isinstance(result, list)
    assert len(result) == 1
    assert "test001" in result[0]


def test_find_projects_no_match(key_yaml, tmp_metadata_dir):
    with patch("fred.src.utils.get_whitelist", return_value=None):
        result = find_metafiles.find_projects(
            key_yaml,
            str(tmp_metadata_dir),
            "organism_name:zebrafish",
            return_dict=True,
            skip_validation=True,
        )
    assert result == []


def test_find_projects_returns_path_when_return_dict_false(key_yaml, tmp_metadata_dir):
    with patch("fred.src.utils.get_whitelist", return_value=None):
        result = find_metafiles.find_projects(
            key_yaml,
            str(tmp_metadata_dir),
            "organism_name:mouse",
            return_dict=False,
            skip_validation=True,
        )
    assert len(result) == 1
    # value should be a path string, not a dict
    path_val = list(result[0].values())[0]
    assert isinstance(path_val, str)
    assert path_val.endswith(".yaml")
