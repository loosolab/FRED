import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.utils as utils

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
KEYS_YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "fred", "structure", "keys.yaml")


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def key_yaml():
    return utils.read_in_yaml(KEYS_YAML_PATH)


# ---------------------------------------------------------------------------
# Metadata dict fixtures (loaded from fixture YAML files)
# ---------------------------------------------------------------------------


def _load_fixture(filename):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_metadata_minimal():
    return _load_fixture("valid_metadata_minimal.yaml")


@pytest.fixture
def valid_metadata_scalar_factor():
    return _load_fixture("valid_metadata_scalar_factor.yaml")


@pytest.fixture
def valid_metadata_value_unit_factor():
    return _load_fixture("valid_metadata_value_unit_factor.yaml")


@pytest.fixture
def valid_metadata_nested_factor():
    return _load_fixture("valid_metadata_nested_factor.yaml")


@pytest.fixture
def invalid_metadata_missing_keys():
    return _load_fixture("invalid_metadata_missing_keys.yaml")


@pytest.fixture
def invalid_metadata_wrong_key():
    return _load_fixture("invalid_metadata_wrong_key.yaml")


# ---------------------------------------------------------------------------
# File-system fixture: writes valid_metadata_minimal into a tmp dir
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_metadata_dir(tmp_path, valid_metadata_minimal):
    meta = valid_metadata_minimal.copy()
    meta["path"] = str(tmp_path / "test001_metadata.yaml")
    utils.save_as_yaml(meta, str(tmp_path / "test001_metadata.yaml"))
    return tmp_path


@pytest.fixture
def metadata_yaml_file(tmp_path, valid_metadata_minimal):
    """Writes valid_metadata_minimal as YAML into tmp_path and returns the file path."""
    path = tmp_path / "test001_metadata.yaml"
    utils.save_as_yaml(valid_metadata_minimal, str(path))
    return path


@pytest.fixture
def minimal_pgm_object(key_yaml, tmp_path):
    """Minimal pgm_object dict (like Webinterface.__dict__) for wi_functions tests."""
    return {
        "whitelist_repo": None,
        "whitelist_branch": "main",
        "whitelist_path": str(tmp_path / "whitelists"),
        "username": None,
        "password": None,
        "structure": key_yaml,
        "update_whitelists": False,
        "output_path": str(tmp_path),
        "filename": "_metadata",
        "email": None,
        "whitelist_version": None,
    }


# ---------------------------------------------------------------------------
# Schema introspection helpers (used for parametrization)
# ---------------------------------------------------------------------------


def _collect_by_special_case(node, match_key, path="", results=None):
    """Recurse through keys.yaml and collect leaf field names matching a special_case key."""
    if results is None:
        results = []
    if isinstance(node, dict):
        if "special_case" in node and match_key in node.get("special_case", {}):
            # path is the field name at this level
            results.append(path)
        for k, v in node.items():
            if k == "value" and isinstance(v, dict):
                # stay at same path level — "value" is just the sub-schema container
                _collect_by_special_case(v, match_key, path, results)
            elif isinstance(v, dict):
                _collect_by_special_case(v, match_key, k, results)
    return results


def collect_value_unit_factors(key_yaml):
    """
    Returns names of all fields in keys.yaml that have special_case.value_unit.
    Used to parametrize tests over all value+unit compound fields.
    Examples: time_point, age, treatment_duration, treatment_amount,
              temperature, concentration, body_mass_index
    """
    raw = _collect_by_special_case(key_yaml, "value_unit")
    # deduplicate (same field name may appear under multiple parent paths)
    return list(dict.fromkeys(raw))


def collect_factor_desc_fields(key_yaml):
    """
    Returns names of all fields in keys.yaml that have a 'factor_desc' property.
    These are the fields that can be used as experimental factors.
    Examples: gene_editing, injury, medical_treatment, disease, strain, signal, time_point, ...
    """
    results = []

    def recurse(node, path=""):
        if isinstance(node, dict):
            if "factor_desc" in node:
                results.append(path)
            for k, v in node.items():
                if k == "value" and isinstance(v, dict):
                    recurse(v, path)
                elif isinstance(v, dict):
                    recurse(v, k)

    recurse(key_yaml)
    return list(dict.fromkeys(results))
