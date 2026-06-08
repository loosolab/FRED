"""
Tests for fred/src/validate_yaml.py.

Also documents validator gaps:
  - restriction special_case is NOT checked by the validator
  - value_unit structure (string vs. dict) is NOT checked by the validator
  - generated:end fields are correctly skipped as non-mandatory
"""
import copy
from unittest.mock import patch

import pytest

import fred.src.validate_yaml as validate_yaml
import fred.src.utils as utils

FILENAME = "_metadata"


# ---------------------------------------------------------------------------
# validate_file — happy path
# ---------------------------------------------------------------------------


def test_validate_valid_minimal_file(key_yaml, valid_metadata_minimal):
    valid, missing, inv_keys, inv_entries, inv_values, logical_warn = (
        validate_yaml.validate_file(
            valid_metadata_minimal,
            key_yaml,
            FILENAME,
            logical_validation=False,
        )
    )
    assert valid is True
    assert missing == []
    assert inv_keys == []
    assert inv_entries == []
    assert inv_values == []


# ---------------------------------------------------------------------------
# validate_file — missing mandatory keys
# ---------------------------------------------------------------------------


def test_validate_missing_mandatory_keys(key_yaml, invalid_metadata_missing_keys):
    valid, missing, inv_keys, inv_entries, inv_values, _ = validate_yaml.validate_file(
        invalid_metadata_missing_keys,
        key_yaml,
        FILENAME,
        logical_validation=False,
    )
    assert valid is False
    assert len(missing) > 0


def test_validate_specific_missing_key(key_yaml, valid_metadata_minimal):
    # Remove 'date' which is mandatory
    metadata = copy.deepcopy(valid_metadata_minimal)
    del metadata["project"]["date"]
    valid, missing, _, _, _, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    assert valid is False
    assert any("date" in k for k in missing)


# ---------------------------------------------------------------------------
# validate_file — invalid keys
# ---------------------------------------------------------------------------


def test_validate_invalid_key_detected(key_yaml, invalid_metadata_wrong_key):
    valid, _, inv_keys, _, _, _ = validate_yaml.validate_file(
        invalid_metadata_wrong_key,
        key_yaml,
        FILENAME,
        logical_validation=False,
    )
    assert valid is False
    assert any("nonexistent_key" in k for k in inv_keys)


# ---------------------------------------------------------------------------
# validate_file — invalid value types
# ---------------------------------------------------------------------------


def test_validate_invalid_date_format(key_yaml, valid_metadata_minimal):
    metadata = copy.deepcopy(valid_metadata_minimal)
    metadata["project"]["date"] = "not-a-date"
    valid, _, _, _, inv_values, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    assert valid is False
    assert any("date" in str(v) for v in inv_values)


# ---------------------------------------------------------------------------
# validate_file — logical validation toggle
# ---------------------------------------------------------------------------


def test_validate_logical_skip(key_yaml, valid_metadata_minimal):
    _, _, _, _, _, logical_warn = validate_yaml.validate_file(
        valid_metadata_minimal, key_yaml, FILENAME, logical_validation=False
    )
    assert logical_warn == []


# ---------------------------------------------------------------------------
# test_for_mandatory — unit tests
# ---------------------------------------------------------------------------


def test_for_mandatory_all_present(key_yaml, valid_metadata_minimal):
    missing = validate_yaml.test_for_mandatory(
        valid_metadata_minimal, key_yaml, [], generated=True
    )
    assert missing == []


def test_for_mandatory_detects_missing(key_yaml, valid_metadata_minimal):
    metadata = copy.deepcopy(valid_metadata_minimal)
    del metadata["project"]["date"]
    missing = validate_yaml.test_for_mandatory(metadata, key_yaml, [], generated=True)
    assert any("date" in k for k in missing)


# ---------------------------------------------------------------------------
# generated:end fields — must NOT be flagged as missing mandatory keys
# ---------------------------------------------------------------------------


def test_generated_end_fields_not_flagged_as_missing(key_yaml, valid_metadata_minimal):
    """
    Fields with special_case.generated == 'end' (e.g. publication title, year, author)
    are auto-filled at the end of generate() and must not produce mandatory-missing errors.
    """
    # Add a publication with only pubmed_id; leave title/year/author/journal absent
    metadata = copy.deepcopy(valid_metadata_minimal)
    metadata["project"]["publication"] = [{"pubmed_id": 32214235}]
    valid, missing, _, _, _, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    # generated:end fields (title, year, etc.) must not appear in missing
    generated_end_fields = ["title", "year", "author", "journal", "volume", "issue", "pages"]
    for field in generated_end_fields:
        assert not any(field in k for k in missing), (
            f"generated:end field '{field}' incorrectly flagged as missing"
        )


# ---------------------------------------------------------------------------
# Validator gaps — documented with comments explaining the missing check
# ---------------------------------------------------------------------------


def test_validator_gap_restriction_not_checked(key_yaml, valid_metadata_minimal):
    """
    VALIDATOR GAP: The 'restriction' special_case (regex + max_length) is only
    enforced in input_functions.py during interactive generation — NOT in
    validate_yaml.py. A manually edited YAML with an invalid restricted value
    will pass validation silently.

    Example: project.id allows only [a-zA-Z0-9] and max 10 chars.
    """
    metadata = copy.deepcopy(valid_metadata_minimal)
    metadata["project"]["id"] = "invalid-id!"  # violates restriction regex
    valid, _, _, _, _, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    # BUG: validator does NOT catch this violation → valid remains True
    assert valid is True, (
        "If this fails, the validator now checks restriction — remove this gap test "
        "and add a proper positive test."
    )


def test_validator_gap_value_unit_string_not_caught(key_yaml, valid_metadata_value_unit_factor):
    """
    VALIDATOR GAP: The validator does not check whether value_unit fields
    (e.g. time_point) contain a structured dict {value, unit} or a plain string.
    A string like "1days" (produced by the known autogenerate bug) passes validation.

    Related bug: autogenerate.get_samples() stores value_unit as "1days" instead of
    {value: 1, unit: "days"}. Both the bug AND this validator gap need to be fixed.
    """
    import copy
    metadata = copy.deepcopy(valid_metadata_value_unit_factor)
    # Inject the buggy format produced by get_samples()
    for cond in metadata["experimental_setting"][0]["conditions"]:
        for sample in cond["biological_replicates"]["samples"]:
            sample["time_point"] = "1days"  # string instead of dict

    valid, _, _, _, inv_values, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    # BUG: validator does NOT catch the structural mismatch
    # If this assertion fails, the validator was fixed — update accordingly.
    assert valid is True, (
        "If this fails, the validator now checks value_unit structure — remove this gap test."
    )


# ---------------------------------------------------------------------------
# print_validation_report — output formatting
# ---------------------------------------------------------------------------


def test_report_contains_key_names(key_yaml, valid_metadata_minimal):
    metadata = copy.deepcopy(valid_metadata_minimal)
    del metadata["project"]["date"]
    _, missing, inv_keys, inv_entries, inv_values, _ = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    report = validate_yaml.print_validation_report(missing, inv_keys, inv_entries, inv_values)
    assert "date" in report


def test_full_report_includes_project_id(key_yaml, valid_metadata_minimal):
    metadata = copy.deepcopy(valid_metadata_minimal)
    del metadata["project"]["date"]
    _, missing, inv_keys, inv_entries, inv_values, logical_warn = validate_yaml.validate_file(
        metadata, key_yaml, FILENAME, logical_validation=False
    )
    report = validate_yaml.print_full_report(metadata, (missing, inv_keys, inv_entries, inv_values), logical_warn)
    assert "test001" in report
