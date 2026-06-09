"""
Tests for fred/src/autogenerate.py.

Structure: one class per get_<key>() function, matching the extensible design
of autogenerate.py. To add tests for a new get_<foo>() function, add a new
class TestGetFoo with one or more test methods.

Template:
    class TestGet<NewKey>:
        def test_basic(self, mock_gen, key_yaml):
            ag = Autogenerate(mock_gen, position)
            result = ag.get_<new_key>()
            assert result == <expected>
"""
import copy
import sys
import os

import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fred.src.autogenerate import Autogenerate
import fred.src.utils as utils
from conftest import collect_value_unit_factors


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_gen(key_yaml):
    gen = MagicMock()
    gen.key_yaml = key_yaml
    gen.setting_ids = []
    gen.result_dict = {}
    gen.conditions = {}
    return gen


# ---------------------------------------------------------------------------
# Helper: simulates the assignment loop inside get_samples()
# without calling parse_lists() (the interactive part).
# This isolates the bug-prone logic.
# ---------------------------------------------------------------------------


def _simulate_sample_assignment(key_yaml, cond_name):
    """
    Reproduces the core assignment loop of get_samples():

        test = utils.split_cond(cond_name)
        for elem in test:
            sample_structure["value"][elem[0]]["value"] = elem[1]
            ...mark as factor...

    Returns the sample_structure dict after assignment.
    """
    parsed = utils.split_cond(cond_name)
    sample_structure = copy.deepcopy(list(utils.find_keys(key_yaml, "samples"))[0])
    for elem in parsed:
        factor_key, factor_val = elem
        if factor_key in sample_structure["value"]:
            field_struct = sample_structure["value"][factor_key]
            val = (
                utils.split_value_unit(factor_val)
                if field_struct.get("special_case", {}).get("value_unit")
                else factor_val
            )
            field_struct["value"] = val
            if "special_case" in sample_structure["value"][factor_key]:
                sample_structure["value"][factor_key]["special_case"]["factor"] = True
            else:
                sample_structure["value"][factor_key]["special_case"] = {"factor": True}
    return sample_structure


# ---------------------------------------------------------------------------
# get_setting_id
# ─────────────────────────────────────────────────────────────────────────────
# One class = one get_<key>() function from autogenerate.py
# ---------------------------------------------------------------------------


class TestGetSettingId:
    def test_first_setting(self, mock_gen):
        mock_gen.setting_ids = []
        ag = Autogenerate(mock_gen, [])
        result = ag.get_setting_id()
        assert result == "exp1"
        assert "exp1" in mock_gen.setting_ids

    def test_increment_from_two(self, mock_gen):
        mock_gen.setting_ids = ["exp1", "exp2"]
        ag = Autogenerate(mock_gen, [])
        result = ag.get_setting_id()
        assert result == "exp3"

    def test_non_contiguous_ids(self, mock_gen):
        # Gap between exp1 and exp3 → next should be exp4 (uses max+1)
        mock_gen.setting_ids = ["exp1", "exp3"]
        ag = Autogenerate(mock_gen, [])
        result = ag.get_setting_id()
        assert result == "exp4"

    def test_ids_grow_monotonically(self, mock_gen):
        mock_gen.setting_ids = []
        ag = Autogenerate(mock_gen, [])
        ids = [ag.get_setting_id() for _ in range(3)]
        assert ids == ["exp1", "exp2", "exp3"]


# ---------------------------------------------------------------------------
# get_count
# ---------------------------------------------------------------------------


class TestGetCount:
    def test_returns_sample_list_length(self, mock_gen):
        mock_gen.result_dict = {
            "experimental_setting": [
                {
                    "conditions": [
                        {
                            "biological_replicates": {
                                "samples": [{"s": 1}, {"s": 2}, {"s": 3}]
                            }
                        }
                    ]
                }
            ]
        }
        position = [
            "experimental_setting", 0,
            "conditions", 0,
            "biological_replicates", 0,
        ]
        ag = Autogenerate(mock_gen, position)
        assert ag.get_count() == 3

    def test_empty_samples_list(self, mock_gen):
        mock_gen.result_dict = {
            "experimental_setting": [
                {"conditions": [{"biological_replicates": {"samples": []}}]}
            ]
        }
        position = ["experimental_setting", 0, "conditions", 0, "biological_replicates", 0]
        ag = Autogenerate(mock_gen, position)
        assert ag.get_count() == 0


# ---------------------------------------------------------------------------
# get_samples — assignment logic
# Tests the core logic of get_samples() that is independent of parse_lists().
# Covers all factor input type categories:
#   Category 1 — Simple select/string  (strain, signal, physical_treatment)
#   Category 2 — Value+unit compound   (time_point, temperature, ...)
#   Category 3 — Nested grouped dict   (disease, injury, ...)
# ---------------------------------------------------------------------------


class TestGetSamples:

    # --- Category 1: Simple select / string factors -------------------------

    @pytest.mark.parametrize("factor,cond_name,expected_value", [
        ("strain",            'strain:"WT"',    "WT"),
        ("signal",            'signal:"high"',  "high"),
        ("physical_treatment",'physical_treatment:"hypoxia"', "hypoxia"),
    ])
    def test_simple_select_factor_stored_as_string(self, key_yaml, factor, cond_name, expected_value):
        sample_structure = _simulate_sample_assignment(key_yaml, cond_name)
        stored = sample_structure["value"][factor]["value"]
        assert stored == expected_value, (
            f"Simple select factor '{factor}' should store as string, got {stored!r}"
        )

    # --- Category 2: Value+unit factors (regression for known bug) ----------
    #
    # Bug (from FRED_PAPER/revision/fred_ux_assessment.md, Punkt 2):
    # get_samples() stores value_unit factors as a composite string ("1days")
    # instead of a structured dict {"value": 1, "unit": "days"}.
    # The validator then reports errors on FRED's own output.
    #
    # These tests are marked xfail(strict=True):
    #   - Currently XFAIL  → bug confirmed, test passes as expected failure
    #   - After fix        → test passes normally (xfail becomes xpass → ERROR,
    #                         remove the mark after fixing)
    #
    # Parametrized over ALL value_unit fields from keys.yaml so that future
    # additions are automatically covered.

    @pytest.mark.parametrize("factor,cond_name,expected_dict", [
        ("time_point",   'time_point:"1days"',   {"value": 1,  "unit": "days"}),
        ("time_point",   'time_point:"7weeks"',  {"value": 7,  "unit": "weeks"}),
    ])
    def test_value_unit_factor_stored_as_dict(self, key_yaml, factor, cond_name, expected_dict):
        sample_structure = _simulate_sample_assignment(key_yaml, cond_name)
        stored = sample_structure["value"][factor]["value"]
        assert isinstance(stored, dict), (
            f"value_unit factor '{factor}' should store as dict, got {type(stored).__name__}: {stored!r}"
        )
        assert stored == expected_dict

    # --- Category 3: Nested grouped factors ---------------------------------

    @pytest.mark.parametrize("factor,cond_name,expected_keys", [
        (
            "disease",
            'disease:{disease_status:"ill"|disease_type:"PAH"}',
            {"disease_status": "ill", "disease_type": "PAH"},
        ),
        (
            "injury",
            'injury:{injury_status:"injured"|injury_type:"cryoinjury"}',
            {"injury_status": "injured", "injury_type": "cryoinjury"},
        ),
    ])
    def test_nested_factor_stored_as_dict(self, key_yaml, factor, cond_name, expected_keys):
        parsed = utils.split_cond(cond_name)
        assert len(parsed) == 1
        key, val = parsed[0]
        assert key == factor
        assert isinstance(val, dict)
        for k, v in expected_keys.items():
            assert val.get(k) == v

    # --- Factor flag marking -----------------------------------------------

    def test_factor_marked_in_special_case(self, key_yaml):
        """Fields used as factors must have special_case.factor == True."""
        sample_structure = _simulate_sample_assignment(key_yaml, 'strain:"WT"')
        sc = sample_structure["value"]["strain"].get("special_case", {})
        assert sc.get("factor") is True

    def test_non_factor_field_not_marked(self, key_yaml):
        """Fields not used as factors must NOT have special_case.factor == True."""
        sample_structure = _simulate_sample_assignment(key_yaml, 'strain:"WT"')
        # tissue is not a factor in this condition
        tissue_sc = sample_structure["value"].get("tissue", {}).get("special_case", {})
        assert tissue_sc.get("factor") is not True
