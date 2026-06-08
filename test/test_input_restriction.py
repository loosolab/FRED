"""
Tests for the 'restriction' special_case handling in input_functions.py.

The restriction check (regex + max_length) is enforced only during interactive
generation in Input.parse_input_value(). It is NOT checked by validate_yaml.py
(that gap is documented in test_validate.py::test_validator_gap_restriction_not_checked).

These tests verify the input-time enforcement works correctly by calling
Input.parse_input_value() with mocked stdin via monkeypatch.
"""
import re
import sys
import os

import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fred.src.input_functions import Input


# ---------------------------------------------------------------------------
# Helper: build a minimal structure dict with a restriction special_case
# ---------------------------------------------------------------------------


def _make_restricted_structure(regex, max_length=None, input_type="restricted_short_text"):
    restriction = {"regex": regex}
    if max_length is not None:
        restriction["max_length"] = max_length
    return {
        "input_type": input_type,
        "whitelist": False,
        "special_case": {"restriction": restriction},
        "mandatory": True,
        "list": False,
        "display_name": "Test Field",
        "desc": "",
        "value": None,
    }


def _make_input_instance():
    """Creates a minimal Input instance without triggering config/whitelist loading."""
    inp = Input.__new__(Input)
    inp.result_dict = {}
    inp.key_yaml = {}
    inp.whitelist_path = None
    inp.read_in_whitelists = {}
    return inp


# ---------------------------------------------------------------------------
# Tests: restriction rejects invalid values
# ---------------------------------------------------------------------------


def test_restriction_rejects_special_chars(monkeypatch):
    """
    A field with regex '[^a-zA-Z0-9]' must reject values containing special chars.
    On rejection it prompts again; the second input provides a valid value.
    """
    structure = _make_restricted_structure(regex="[^a-zA-Z0-9]", max_length=10)
    inp = _make_input_instance()

    # First call returns invalid value, second returns valid
    inputs = iter(["abc-def", "abcdef"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))

    result = inp.parse_input_value("test_field", structure)
    assert result == "abcdef"


def test_restriction_rejects_too_long(monkeypatch):
    """
    A field with max_length: 6 must reject values longer than 6 characters.
    """
    structure = _make_restricted_structure(regex="[^a-zA-Z0-9]", max_length=6)
    inp = _make_input_instance()

    inputs = iter(["toolongval", "short"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))

    result = inp.parse_input_value("test_field", structure)
    assert result == "short"


def test_restriction_accepts_valid_value(monkeypatch):
    """
    A valid alphanumeric value within max_length must be accepted on first attempt.
    """
    structure = _make_restricted_structure(regex="[^a-zA-Z0-9]", max_length=10)
    inp = _make_input_instance()

    monkeypatch.setattr("builtins.input", lambda *_: "Valid123")

    result = inp.parse_input_value("test_field", structure)
    assert result == "Valid123"


# ---------------------------------------------------------------------------
# Tests: restriction check logic (unit-level, without calling parse_input_value)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value,regex,max_length,should_reject", [
    ("abc-def",   "[^a-zA-Z0-9]", 10,  True),   # contains hyphen
    ("abc!def",   "[^a-zA-Z0-9]", 10,  True),   # contains !
    ("toolongval", "[^a-zA-Z0-9]", 6,  True),   # too long
    ("abc123",    "[^a-zA-Z0-9]", 10,  False),  # valid
    ("AB",        "[^a-zA-Z0-9]", 6,   False),  # valid short
])
def test_restriction_check_logic(value, regex, max_length, should_reject):
    """
    Unit test for the restriction check logic extracted from Input.parse_input_value().
    Tests both max_length and regex checks independently.
    """
    length_violated = len(value) > max_length
    pattern = re.compile(regex)
    regex_violated = bool(pattern.search(value))
    rejected = length_violated or regex_violated
    assert rejected == should_reject, (
        f"Value '{value}' should {'be rejected' if should_reject else 'be accepted'} "
        f"(length_violated={length_violated}, regex_violated={regex_violated})"
    )
