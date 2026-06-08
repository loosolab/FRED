"""
Tests for fred/src/utils.py — pure utility functions.
Covers: YAML I/O, find_keys, split_value_unit, split_cond,
        get_condition_combinations, get_combis.
"""
import pytest

import fred.src.utils as utils


# ---------------------------------------------------------------------------
# YAML roundtrip
# ---------------------------------------------------------------------------


def test_yaml_roundtrip(tmp_path):
    data = {"project": {"id": "test001", "name": "Test"}, "list_field": [1, 2, 3]}
    path = str(tmp_path / "test.yaml")
    utils.save_as_yaml(data, path)
    loaded = utils.read_in_yaml(path)
    assert loaded == data


# ---------------------------------------------------------------------------
# find_keys
# ---------------------------------------------------------------------------


def test_find_keys_nested():
    node = {"a": {"b": {"target": "found_it"}}}
    result = list(utils.find_keys(node, "target"))
    assert result == ["found_it"]


def test_find_keys_in_list():
    node = {"items": [{"key": "v1"}, {"key": "v2"}]}
    result = list(utils.find_keys(node, "key"))
    assert result == ["v1", "v2"]


def test_find_keys_missing_returns_empty():
    node = {"a": {"b": 1}}
    result = list(utils.find_keys(node, "nonexistent"))
    assert result == []


def test_find_keys_multiple_occurrences():
    node = {"a": {"id": 1}, "b": {"id": 2}}
    result = list(utils.find_keys(node, "id"))
    assert set(result) == {1, 2}


# ---------------------------------------------------------------------------
# split_value_unit
# ---------------------------------------------------------------------------


def test_split_value_unit_integer():
    result = utils.split_value_unit("2weeks")
    assert result == {"value": 2, "unit": "weeks"}


def test_split_value_unit_float():
    result = utils.split_value_unit("2.5years")
    assert result == {"value": 2.5, "unit": "years"}


def test_split_value_unit_single_digit():
    result = utils.split_value_unit("1days")
    assert result == {"value": 1, "unit": "days"}


def test_split_value_unit_multi_char_unit():
    result = utils.split_value_unit("37celsius")
    assert result == {"value": 37, "unit": "celsius"}


# ---------------------------------------------------------------------------
# split_cond
# ---------------------------------------------------------------------------


def test_split_cond_simple_scalar():
    result = utils.split_cond('strain:"WT"')
    assert result == [("strain", "WT")]


def test_split_cond_two_scalars():
    result = utils.split_cond('strain:"WT"-time_point:"1days"')
    assert len(result) == 2
    assert result[0] == ("strain", "WT")
    assert result[1] == ("time_point", "1days")


def test_split_cond_value_with_hyphen():
    # Value containing a hyphen should not be split
    result = utils.split_cond('strain:"C57BL-6"')
    assert result == [("strain", "C57BL-6")]


def test_split_cond_nested_grouped_factor():
    cond = 'disease:{disease_status:"ill"|disease_type:"PAH"}'
    result = utils.split_cond(cond)
    assert len(result) == 1
    key, val = result[0]
    assert key == "disease"
    assert isinstance(val, dict)
    assert val["disease_status"] == "ill"
    assert val["disease_type"] == "PAH"


def test_split_cond_nested_control_only():
    cond = 'disease:{disease_status:"healthy"}'
    result = utils.split_cond(cond)
    assert len(result) == 1
    key, val = result[0]
    assert key == "disease"
    assert val["disease_status"] == "healthy"


def test_split_cond_nested_factor_and_scalar():
    cond = 'strain:"WT"-disease:{disease_status:"ill"}'
    result = utils.split_cond(cond)
    assert len(result) == 2
    assert result[0] == ("strain", "WT")
    key, val = result[1]
    assert key == "disease"
    assert val["disease_status"] == "ill"


# ---------------------------------------------------------------------------
# get_condition_combinations
# ---------------------------------------------------------------------------


def test_get_condition_combinations_single_factor_two_values():
    factors = [{"factor": "strain", "values": ["WT", "KO"]}]
    result = utils.get_condition_combinations(factors)
    assert 'strain:"WT"' in result
    assert 'strain:"KO"' in result
    assert len(result) == 2


def test_get_condition_combinations_two_factors_cross_product():
    factors = [
        {"factor": "strain", "values": ["WT", "KO"]},
        {"factor": "signal", "values": ["high", "low"]},
    ]
    result = utils.get_condition_combinations(factors)
    assert 'strain:"WT"-signal:"high"' in result
    assert 'strain:"WT"-signal:"low"' in result
    assert 'strain:"KO"-signal:"high"' in result
    assert 'strain:"KO"-signal:"low"' in result


def test_get_condition_combinations_value_unit_factor():
    factors = [{"factor": "time_point", "values": [{"value": 2, "unit": "weeks"}]}]
    result = utils.get_condition_combinations(factors)
    assert len(result) == 1
    assert "2weeks" in result[0]


def test_get_condition_combinations_three_factors():
    factors = [
        {"factor": "strain", "values": ["WT", "KO"]},
        {"factor": "signal", "values": ["high", "low"]},
        {"factor": "physical_treatment", "values": ["hypoxia", "normoxia"]},
    ]
    result = utils.get_condition_combinations(factors)
    # Should include all pairwise and three-way combinations
    assert any("strain" in r and "signal" in r and "physical_treatment" in r for r in result)


def test_get_condition_combinations_already_prefixed_value():
    # If value already starts with 'factor:', don't add prefix again
    factors = [{"factor": "strain", "values": ['strain:"WT"']}]
    result = utils.get_condition_combinations(factors)
    # Should NOT produce 'strain:"strain:"WT""'
    assert all(r.count('strain:"WT"') == 1 for r in result)


# ---------------------------------------------------------------------------
# get_combis
# ---------------------------------------------------------------------------


def test_get_combis_simple_list_single_value(key_yaml):
    # tissue is a list:True field — each value is a standalone combination
    values = ["heart"]
    result = utils.get_combis(values, "tissue", {}, key_yaml)
    assert any("heart" in r for r in result)


def test_get_combis_simple_list_two_values(key_yaml):
    # With two values, should include both singles and the combination
    values = ["heart", "lung"]
    result = utils.get_combis(values, "tissue", {}, key_yaml)
    assert any("heart" in r for r in result)
    assert any("lung" in r for r in result)
    # Should also include combined value
    assert any("heart" in r and "lung" in r for r in result)


def test_get_combis_grouped_factor_with_control(key_yaml):
    # disease has control={disease_status: "healthy"}
    # "healthy" should appear in the results but be separated from ill conditions
    values = {
        "disease_status": ["healthy", "ill"],
        "control": {"disease_status": "healthy"},
    }
    result = utils.get_combis(values, "disease", {}, key_yaml)
    assert isinstance(result, list)
    assert len(result) > 0
    # healthy (control) should appear in results
    assert any("healthy" in r for r in result)


def test_get_combis_value_unit_format(key_yaml):
    # time_point with value_unit special_case — combis should use string format
    values = ['time_point:"1days"']
    result = utils.get_combis(values, "time_point", {}, key_yaml)
    assert isinstance(result, list)
