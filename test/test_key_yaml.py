"""
Tests for fred/structure/keys.yaml schema integrity.
Migrated from the original sys.exit()-style script to pytest.
"""
import pytest

import fred.src.utils as utils

ALL_KEYS = {
    "mandatory": "bool",
    "list": "bool",
    "display_name": "str",
    "desc": "str",
    "value": "value",
}

INNER_KEYS = {
    "whitelist": "bool",
    "input_type": [
        "short_text",
        "long_text",
        "select",
        "number",
        "bool",
        "date",
        "restricted_short_text",
    ],
}


# ---------------------------------------------------------------------------
# Helpers (logic copied from original script, using assert instead of sys.exit)
# ---------------------------------------------------------------------------


def _check_property(prop_input, prop, keys):
    """Return (error: bool, expected_type_description: str)."""
    expected = keys[prop]
    if expected == "bool":
        return not isinstance(prop_input, bool), "of type 'bool'"
    elif expected == "str":
        if prop != "desc" and not isinstance(prop_input, str):
            return True, "of type 'str'"
    elif expected == "int":
        return not isinstance(prop_input, int), "of type 'int'"
    elif expected == "value":
        valid = prop_input is None or isinstance(prop_input, (dict, str, bool, int))
        return not valid, "dict or scalar (None, str, bool, int)"
    elif isinstance(expected, list):
        return prop_input not in expected, " / ".join(f"'{x}'" for x in expected)
    return False, ""


def _assert_properties(part, path, keys):
    for prop in keys:
        assert prop in part, f"Property '{prop}' missing for key '{path}'"
        error, desc = _check_property(part[prop], prop, keys)
        assert not error, (
            f"Wrong value '{part[prop]}' for property '{prop}' at '{path}'. Expected {desc}"
        )


def _walk_key_yaml(part, path):
    _assert_properties(part, path, ALL_KEYS)
    if isinstance(part["value"], dict):
        for sub_key, sub_val in part["value"].items():
            _walk_key_yaml(sub_val, f"{path}:{sub_key}")
    else:
        _assert_properties(part, path, INNER_KEYS)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_keys_yaml_structure(key_yaml):
    """Every key in keys.yaml must have the required properties with correct types."""
    for key, value in key_yaml.items():
        _walk_key_yaml(value, key)


@pytest.mark.parametrize("top_key", ["project", "experimental_setting", "technical_details"])
def test_top_level_keys_present(key_yaml, top_key):
    """The three mandatory top-level sections must exist in keys.yaml."""
    assert top_key in key_yaml
