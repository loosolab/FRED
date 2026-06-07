"""
Tests for fred/src/wi_functions.py (Python API for web interface).

Coverage: pure query-parsing logic, file-I/O functions, structure-based
functions, and mock-based tests for functions with external dependencies.
"""
import copy
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fred.src.utils as utils
import fred.src.wi_functions as wi


# ===========================================================================
# Priority 1 — Pure logic (no external dependencies)
# ===========================================================================


class TestGetTextKeys:
    """get_text_keys() extracts keys with text-like input_types from a structure dict."""

    STRUCTURE = {
        "project_name": {"input_type": "short_text"},
        "organism": {"input_type": "select"},
        "notes": {"input_type": "long_text"},
        "date": {"input_type": "date"},
        "project": {
            "value": {
                "id": {"input_type": "restricted_short_text"},
                "count": {"input_type": "number"},
            }
        },
    }

    def test_finds_short_text_fields(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "project_name" in keys

    def test_finds_select_fields(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "organism" in keys

    def test_finds_long_text_fields(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "notes" in keys

    def test_finds_restricted_short_text_with_nested_prefix(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "project.id" in keys

    def test_skips_date_input_type(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "date" not in keys

    def test_skips_number_input_type(self):
        keys = wi.get_text_keys(self.STRUCTURE)
        assert "project.count" not in keys

    def test_empty_structure_returns_empty_list(self):
        assert wi.get_text_keys({}) == []


class TestGetAllQuery:
    """get_all_query() builds a MongoDB $regex query fragment per key."""

    def test_returns_one_entry_per_key(self):
        result = wi.get_all_query(["project.id", "project.project_name"], "test")
        assert len(result) == 2

    def test_includes_value_in_regex(self):
        result = wi.get_all_query(["project.id"], "myvalue")
        assert "myvalue" in result[0]

    def test_each_entry_is_string(self):
        result = wi.get_all_query(["a", "b", "c"], "x")
        assert all(isinstance(r, str) for r in result)

    def test_empty_keys_returns_empty_list(self):
        assert wi.get_all_query([], "test") == []

    def test_result_contains_regex_keyword(self):
        result = wi.get_all_query(["project.id"], "test")
        assert "$regex" in result[0]


class TestParseStringToQueryDict:
    """parse_string_to_query_dict() converts a search string to a MongoDB JSON query string."""

    STRUCTURE = {}  # empty — triggers the simple else-branch (no merge special_case)

    def test_simple_key_value_returns_valid_json(self):
        result = wi.parse_string_to_query_dict('project:id:"test001"', self.STRUCTURE)
        d = json.loads(result)
        assert "project.id" in d
        assert d["project.id"]["$regex"] == "test001"

    def test_and_operator_produces_and_query(self):
        result = wi.parse_string_to_query_dict(
            'project:id:"A" and project:project_name:"B"', self.STRUCTURE
        )
        d = json.loads(result)
        assert "$and" in d
        assert len(d["$and"]) == 2

    def test_or_operator_produces_or_query(self):
        result = wi.parse_string_to_query_dict(
            'project:id:"A" or project:id:"B"', self.STRUCTURE
        )
        d = json.loads(result)
        assert "$or" in d
        assert len(d["$or"]) == 2

    def test_not_operator_produces_not_query(self):
        result = wi.parse_string_to_query_dict('not project:id:"A"', self.STRUCTURE)
        d = json.loads(result)
        assert "$not" in d

    def test_escapes_open_paren(self):
        result = wi.parse_string_to_query_dict('project:id:"test(1)"', self.STRUCTURE)
        assert "\\\\(" in result

    def test_escapes_close_paren(self):
        result = wi.parse_string_to_query_dict('project:id:"test(1)"', self.STRUCTURE)
        assert "\\\\)" in result

    def test_result_is_string(self):
        result = wi.parse_string_to_query_dict('project:id:"x"', self.STRUCTURE)
        assert isinstance(result, str)


class TestParseSearchStringToQuery:
    """parse_search_string_to_query() wraps a search string and returns a Python dict."""

    STRUCTURE = {}

    def test_simple_query_returns_dict(self):
        result = wi.parse_search_string_to_query('project:id:"test001"', self.STRUCTURE)
        assert isinstance(result, dict)
        assert "project.id" in result

    def test_already_braced_query_parsed_correctly(self):
        result = wi.parse_search_string_to_query(
            '(project:id:"test001")', self.STRUCTURE
        )
        assert isinstance(result, dict)
        assert "project.id" in result

    def test_and_query(self):
        result = wi.parse_search_string_to_query(
            'project:id:"A" and project:project_name:"B"', self.STRUCTURE
        )
        assert "$and" in result

    def test_or_query(self):
        result = wi.parse_search_string_to_query(
            'project:id:"A" or project:id:"B"', self.STRUCTURE
        )
        assert "$or" in result


# ===========================================================================
# Priority 2 — File I/O (no git, no subprocess)
# ===========================================================================


class TestReadMetadata:
    def test_returns_dict(self, metadata_yaml_file):
        result = wi.read_metadata(str(metadata_yaml_file))
        assert isinstance(result, dict)

    def test_contains_project_key(self, metadata_yaml_file):
        result = wi.read_metadata(str(metadata_yaml_file))
        assert "project" in result

    def test_project_id_matches_fixture(self, metadata_yaml_file):
        result = wi.read_metadata(str(metadata_yaml_file))
        assert result["project"]["id"] == "test001"


class TestGetMetadataSearchView:
    def test_extracts_id(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert result["id"] == "test001"

    def test_extracts_project_name(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert result["project_name"] == "Test Project"

    def test_extracts_owner_name(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert result["owner"] == "Walter, Jasmin"

    def test_extracts_date(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert result["date"] == "01.01.2024"

    def test_organisms_list_contains_mouse(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert isinstance(result["organisms"], list)
        assert "mouse" in result["organisms"]

    def test_technique_list_contains_rna_seq(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert isinstance(result["technique"], list)
        assert "bulk RNA-seq" in result["technique"]

    def test_no_nerd_field_returns_none(self, metadata_yaml_file):
        result = wi.get_metadata_search_view(str(metadata_yaml_file))
        assert result["nerd"] is None

    def test_nerd_field_returns_name_list(self, tmp_path, valid_metadata_minimal):
        meta = copy.deepcopy(valid_metadata_minimal)
        meta["project"]["nerd"] = [{"name": "Mustermann, Max", "ldap_name": "mmust"}]
        path = tmp_path / "nerd_metadata.yaml"
        utils.save_as_yaml(meta, str(path))
        result = wi.get_metadata_search_view(str(path))
        assert result["nerd"] == ["Mustermann, Max"]

    def test_missing_description_returns_none(self, tmp_path, valid_metadata_minimal):
        meta = copy.deepcopy(valid_metadata_minimal)
        del meta["project"]["description"]
        path = tmp_path / "nodesc_metadata.yaml"
        utils.save_as_yaml(meta, str(path))
        result = wi.get_metadata_search_view(str(path))
        assert result["description"] is None

    def test_missing_owner_returns_none(self, tmp_path, valid_metadata_minimal):
        meta = copy.deepcopy(valid_metadata_minimal)
        del meta["project"]["owner"]
        path = tmp_path / "noowner_metadata.yaml"
        utils.save_as_yaml(meta, str(path))
        result = wi.get_metadata_search_view(str(path))
        assert result["owner"] is None


class TestGetMetadata:
    def test_returns_two_tuple(self, metadata_yaml_file):
        result = wi.get_metadata(str(metadata_yaml_file))
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_full_metadata_has_correct_project_id(self, metadata_yaml_file):
        full, _ = wi.get_metadata(str(metadata_yaml_file))
        assert full["project"]["id"] == "test001"

    def test_search_view_is_dict_with_id(self, metadata_yaml_file):
        _, search_view = wi.get_metadata(str(metadata_yaml_file))
        assert isinstance(search_view, dict)
        assert search_view["id"] == "test001"


class TestAddNerd:
    NERD = {
        "name": "Mustermann, Max",
        "ldap_name": "mmust",
        "department": "AG-test",
        "email": "max@test.com",
    }

    def test_returns_true_on_success(self, metadata_yaml_file):
        result = wi.add_nerd(str(metadata_yaml_file), self.NERD)
        assert result is True

    def test_nerd_written_to_file(self, metadata_yaml_file):
        wi.add_nerd(str(metadata_yaml_file), self.NERD)
        saved = utils.read_in_yaml(str(metadata_yaml_file))
        assert "nerd" in saved["project"]
        ldap_names = [n["ldap_name"] for n in saved["project"]["nerd"]]
        assert "mmust" in ldap_names

    def test_returns_false_on_duplicate_ldap(self, metadata_yaml_file):
        wi.add_nerd(str(metadata_yaml_file), self.NERD)
        result = wi.add_nerd(str(metadata_yaml_file), self.NERD)
        assert result is False

    def test_no_duplicate_entry_in_file(self, metadata_yaml_file):
        wi.add_nerd(str(metadata_yaml_file), self.NERD)
        wi.add_nerd(str(metadata_yaml_file), self.NERD)
        saved = utils.read_in_yaml(str(metadata_yaml_file))
        ldap_names = [n["ldap_name"] for n in saved["project"]["nerd"]]
        assert ldap_names.count("mmust") == 1

    def test_creates_nerd_list_when_key_missing(self, tmp_path, valid_metadata_minimal):
        meta = copy.deepcopy(valid_metadata_minimal)
        path = tmp_path / "nonerd_metadata.yaml"
        utils.save_as_yaml(meta, str(path))
        result = wi.add_nerd(str(path), self.NERD)
        assert result is True
        saved = utils.read_in_yaml(str(path))
        assert len(saved["project"]["nerd"]) == 1

    def test_second_nerd_can_be_added(self, metadata_yaml_file):
        wi.add_nerd(str(metadata_yaml_file), self.NERD)
        second = {**self.NERD, "name": "Doe, Jane", "ldap_name": "jdoe"}
        result = wi.add_nerd(str(metadata_yaml_file), second)
        assert result is True
        saved = utils.read_in_yaml(str(metadata_yaml_file))
        assert len(saved["project"]["nerd"]) == 2


class TestSaveObject:
    def test_writes_yaml_file(self, tmp_path, valid_metadata_minimal):
        wi.save_object(valid_metadata_minimal, str(tmp_path), "_metadata", False)
        files = list(tmp_path.iterdir())
        assert any(f.name.endswith(".yaml") for f in files)

    def test_returns_filename_and_project_id(self, tmp_path, valid_metadata_minimal):
        filename, project_id = wi.save_object(
            valid_metadata_minimal, str(tmp_path), "_metadata", False
        )
        assert isinstance(filename, str)
        assert project_id == "test001"

    def test_generated_filename_contains_project_id(self, tmp_path, valid_metadata_minimal):
        filename, _ = wi.save_object(
            valid_metadata_minimal, str(tmp_path), "_metadata", False
        )
        assert "test001" in filename

    def test_edit_state_uses_provided_filename(self, tmp_path, valid_metadata_minimal):
        custom_name = "custom_file.yaml"
        returned_name, _ = wi.save_object(
            valid_metadata_minimal, str(tmp_path), custom_name, True
        )
        assert returned_name == custom_name
        assert (tmp_path / custom_name).exists()


class TestSaveFilenames:
    def test_writes_txt_file(self, tmp_path):
        file_str = ("test001", "test001_file1\ntest001_file2\n")
        result = wi.save_filenames(file_str, str(tmp_path))
        assert result == "test001_samples.txt"
        assert (tmp_path / "test001_samples.txt").exists()

    def test_file_content_matches_input(self, tmp_path):
        content = "test001_exp1_file1\ntest001_exp1_file2\n"
        wi.save_filenames(("test001", content), str(tmp_path))
        assert (tmp_path / "test001_samples.txt").read_text() == content

    def test_returns_none_when_file_str_is_none(self, tmp_path):
        result = wi.save_filenames(None, str(tmp_path))
        assert result is None


# ===========================================================================
# Priority 3 — Functions with structure/pgm_object fixtures
# ===========================================================================


class TestGetEmptyWiObject:
    def test_returns_dict(self, minimal_pgm_object):
        result = wi.get_empty_wi_object(minimal_pgm_object, {})
        assert isinstance(result, dict)

    def test_has_project_key(self, minimal_pgm_object):
        result = wi.get_empty_wi_object(minimal_pgm_object, {})
        assert "project" in result

    def test_has_experimental_setting_key(self, minimal_pgm_object):
        result = wi.get_empty_wi_object(minimal_pgm_object, {})
        assert "experimental_setting" in result

    def test_has_technical_details_key(self, minimal_pgm_object):
        result = wi.get_empty_wi_object(minimal_pgm_object, {})
        assert "technical_details" in result

    def test_all_factors_is_empty_list(self, minimal_pgm_object):
        result = wi.get_empty_wi_object(minimal_pgm_object, {})
        assert result["all_factors"] == []


class TestIsEmpty:
    def test_empty_object_returns_true(self, minimal_pgm_object):
        empty_obj = wi.get_empty_wi_object(minimal_pgm_object, {})
        result = wi.is_empty(minimal_pgm_object, empty_obj, {})
        assert result["empty"] is True

    def test_result_contains_required_keys(self, minimal_pgm_object):
        empty_obj = wi.get_empty_wi_object(minimal_pgm_object, {})
        result = wi.is_empty(minimal_pgm_object, empty_obj, {})
        assert "empty" in result
        assert "object" in result

    def test_modified_object_returns_false(self, minimal_pgm_object):
        empty_obj = wi.get_empty_wi_object(minimal_pgm_object, {})
        filled_obj = copy.deepcopy(empty_obj)
        filled_obj["all_factors"] = ["something"]
        result = wi.is_empty(minimal_pgm_object, filled_obj, {})
        assert result["empty"] is False


class TestGetMetaInfoFromObject:
    def test_returns_tuple(self, valid_metadata_minimal):
        result = wi.get_meta_info_from_object(copy.deepcopy(valid_metadata_minimal))
        assert isinstance(result, tuple)

    def test_first_element_is_string(self, valid_metadata_minimal):
        html_str, _ = wi.get_meta_info_from_object(copy.deepcopy(valid_metadata_minimal))
        assert isinstance(html_str, str)

    def test_html_contains_project_id(self, valid_metadata_minimal):
        html_str, _ = wi.get_meta_info_from_object(copy.deepcopy(valid_metadata_minimal))
        assert "test001" in html_str

    def test_handles_missing_project_id(self, valid_metadata_minimal):
        meta = copy.deepcopy(valid_metadata_minimal)
        del meta["project"]["id"]
        html_str, _ = wi.get_meta_info_from_object(meta)
        assert isinstance(html_str, str)


class TestGetSearchMask:
    def test_returns_dict(self, minimal_pgm_object):
        result = wi.get_search_mask(minimal_pgm_object)
        assert isinstance(result, dict)

    def test_has_keys_entry(self, minimal_pgm_object):
        result = wi.get_search_mask(minimal_pgm_object)
        assert "keys" in result

    def test_keys_is_list(self, minimal_pgm_object):
        result = wi.get_search_mask(minimal_pgm_object)
        assert isinstance(result["keys"], list)

    def test_all_keys_entry_is_first(self, minimal_pgm_object):
        result = wi.get_search_mask(minimal_pgm_object)
        assert result["keys"][0]["key_name"] == "All keys"


class TestEditWiObject:
    # edit_wi_object calls utils.get_short_name() which calls get_whitelist() and
    # subscripts the result. With an empty read_in_whitelists={} this raises TypeError
    # because no whitelist is found. These tests require a populated whitelist object
    # (from a real FRED_whitelists checkout) to pass.

    @pytest.mark.xfail(reason="requires populated whitelist object — get_short_name fails with empty {}")
    def test_returns_dict(self, metadata_yaml_file, minimal_pgm_object):
        result = wi.edit_wi_object(str(metadata_yaml_file), minimal_pgm_object, {})
        assert isinstance(result, dict)

    @pytest.mark.xfail(reason="requires populated whitelist object — get_short_name fails with empty {}")
    def test_has_project_key(self, metadata_yaml_file, minimal_pgm_object):
        result = wi.edit_wi_object(str(metadata_yaml_file), minimal_pgm_object, {})
        assert "project" in result

    @pytest.mark.xfail(reason="requires populated whitelist object — get_short_name fails with empty {}")
    def test_has_experimental_setting_key(self, metadata_yaml_file, minimal_pgm_object):
        result = wi.edit_wi_object(str(metadata_yaml_file), minimal_pgm_object, {})
        assert "experimental_setting" in result

    @pytest.mark.xfail(reason="requires populated whitelist object — get_short_name fails with empty {}")
    def test_has_whitelists_key(self, metadata_yaml_file, minimal_pgm_object):
        result = wi.edit_wi_object(str(metadata_yaml_file), minimal_pgm_object, {})
        assert "whitelists" in result


class TestParseObject:
    def test_returns_dict(self, minimal_pgm_object):
        empty_obj = wi.get_empty_wi_object(minimal_pgm_object, {})
        result = wi.parse_object(minimal_pgm_object, empty_obj, {})
        assert isinstance(result, dict)

    def test_has_project_key(self, minimal_pgm_object):
        empty_obj = wi.get_empty_wi_object(minimal_pgm_object, {})
        result = wi.parse_object(minimal_pgm_object, empty_obj, {})
        assert "project" in result


# ===========================================================================
# Priority 4 — Mock-based tests (external dependencies)
# ===========================================================================


class TestFetchWhitelists:
    def test_calls_get_whitelists_with_correct_args(self, minimal_pgm_object):
        with patch("fred.src.wi_functions.gwi.get_whitelists") as mock_get:
            mock_get.return_value = "v1.2.3"
            wi.fetch_whitelists(minimal_pgm_object)
            mock_get.assert_called_once_with(
                minimal_pgm_object["whitelist_path"],
                minimal_pgm_object["whitelist_repo"],
                minimal_pgm_object["whitelist_branch"],
                minimal_pgm_object["update_whitelists"],
            )

    def test_returns_version_from_get_whitelists(self, minimal_pgm_object):
        with patch("fred.src.wi_functions.gwi.get_whitelists") as mock_get:
            mock_get.return_value = "v1.0"
            result = wi.fetch_whitelists(minimal_pgm_object)
            assert result == "v1.0"


class TestGetFactors:
    def test_delegates_to_fac_cond_get_factors(self, minimal_pgm_object):
        with patch("fred.src.wi_functions.fac_cond.get_factors") as mock_get:
            mock_get.return_value = [{"factor": "strain"}]
            result = wi.get_factors(minimal_pgm_object, "mouse", {})
            mock_get.assert_called_once_with(
                "mouse", minimal_pgm_object["structure"], {}
            )
            assert result == [{"factor": "strain"}]


class TestGetConditions:
    def test_delegates_to_fac_cond_get_conditions(self, minimal_pgm_object):
        factors = [{"factor": "strain", "values": ["WT", "KO"]}]
        with patch("fred.src.wi_functions.fac_cond.get_conditions") as mock_get:
            mock_get.return_value = [{"condition": "WT"}]
            result = wi.get_conditions(minimal_pgm_object, factors, "mouse", {})
            mock_get.assert_called_once_with(
                factors, "mouse", minimal_pgm_object["structure"], {}
            )
            assert result == [{"condition": "WT"}]


class TestGetPlotFromObject:
    def test_returns_list(self, valid_metadata_minimal, minimal_pgm_object):
        mock_plot = MagicMock()
        mock_plot.to_html.return_value = "<div>plot</div>"
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.return_value = [("exp1", mock_plot, None)]
            result = wi.get_plot_from_object(minimal_pgm_object, valid_metadata_minimal)
            assert isinstance(result, list)

    def test_list_entry_has_title_and_plot_keys(self, valid_metadata_minimal, minimal_pgm_object):
        mock_plot = MagicMock()
        mock_plot.to_html.return_value = "<div>plot</div>"
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.return_value = [("exp1", mock_plot, None)]
            result = wi.get_plot_from_object(minimal_pgm_object, valid_metadata_minimal)
            assert len(result) == 1
            assert "title" in result[0]
            assert "plot" in result[0]

    def test_returns_empty_list_when_heatmap_raises(
        self, valid_metadata_minimal, minimal_pgm_object
    ):
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.side_effect = Exception("heatmap error")
            result = wi.get_plot_from_object(minimal_pgm_object, valid_metadata_minimal)
            assert result == []


class TestDownloadPlot:
    def test_returns_empty_list_when_plot_is_none(
        self, valid_metadata_minimal, minimal_pgm_object, tmp_path
    ):
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.return_value = [("exp1", None, None)]
            result = wi.download_plot(
                minimal_pgm_object, valid_metadata_minimal, str(tmp_path)
            )
            assert result == []

    def test_returns_png_filename_when_plot_exists(
        self, valid_metadata_minimal, minimal_pgm_object, tmp_path
    ):
        mock_plot = MagicMock()
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.return_value = [("exp1", mock_plot, None)]
            result = wi.download_plot(
                minimal_pgm_object, valid_metadata_minimal, str(tmp_path)
            )
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].endswith(".png")

    def test_calls_write_image_on_plot(
        self, valid_metadata_minimal, minimal_pgm_object, tmp_path
    ):
        mock_plot = MagicMock()
        with patch("fred.src.wi_functions.create_heatmap.get_heatmap") as mock_hm:
            mock_hm.return_value = [("exp1", mock_plot, None)]
            wi.download_plot(minimal_pgm_object, valid_metadata_minimal, str(tmp_path))
            mock_plot.write_image.assert_called_once()


class TestWebinterface:
    def test_to_dict_returns_dict_with_structure_key(self, tmp_path):
        keys_yaml_path = os.path.join(
            os.path.dirname(__file__), "..", "fred", "structure", "keys.yaml"
        )
        config = {
            "structure": keys_yaml_path,
            "whitelist_path": str(tmp_path),
            "output_path": str(tmp_path),
            "filename": "_metadata",
            "whitelist_repository": "https://example.com/wl.git",
            "update_whitelists": False,
        }
        config_path = tmp_path / "test_config.yaml"
        utils.save_as_yaml(config, str(config_path))
        with patch("fred.src.wi_functions.fetch_whitelists") as mock_fw:
            mock_fw.return_value = "v1.0"
            obj = wi.Webinterface(str(config_path))
            d = obj.to_dict()
            assert isinstance(d, dict)
            assert "structure" in d

    def test_structure_is_loaded_after_init(self, tmp_path):
        keys_yaml_path = os.path.join(
            os.path.dirname(__file__), "..", "fred", "structure", "keys.yaml"
        )
        config = {
            "structure": keys_yaml_path,
            "whitelist_path": str(tmp_path),
            "output_path": str(tmp_path),
            "filename": "_metadata",
            "whitelist_repository": "https://example.com/wl.git",
            "update_whitelists": False,
        }
        config_path = tmp_path / "test_config2.yaml"
        utils.save_as_yaml(config, str(config_path))
        with patch("fred.src.wi_functions.fetch_whitelists") as mock_fw:
            mock_fw.return_value = "v1.0"
            obj = wi.Webinterface(str(config_path))
            assert isinstance(obj.structure, dict)
            assert len(obj.structure) > 0
