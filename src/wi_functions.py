import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.git_whitelists as git_whitelists
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.wi_object_to_yaml as oty
import src.web_interface.validation as validation
import src.web_interface.html_output as html_output
import src.web_interface.file_io as file_io
import src.web_interface.editing as editing
import src.web_interface.searching as searching
import os


# This script contains all functions for generation of objects for the web
# interface
disabled_fields = []


def get_empty_wi_object():

    git_whitelists.get_whitelists()

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', '..', 'keys.yaml'))

    return yto.get_empty_wi_object(key_yaml)


def get_single_whitelist(ob):

    return whitelist_parsing.get_single_whitelist(ob)


def get_factors(organism):

    return fac_cond.get_factors(organism)


def get_conditions(factors, organism_name):

    return fac_cond.get_conditions(factors, organism_name)


def parse_object(wi_object):

    return oty.parse_object(wi_object)


def validate_object(wi_object):

    return validation.validate_object(wi_object)


def get_summary(wi_object):

    return html_output.get_summary(wi_object)


def save_object(dictionary, path, filename):

    return file_io.save_object(dictionary, path, filename)


def save_filenames(file_str, path):

    return file_io.save_filenames(file_str, path)


def get_meta_info(path, project_id):

    return searching.get_meta_info(path, project_id)


def get_search_mask():

    return searching.get_search_mask()


def find_metadata(path, search_string):

    return searching.find_metadata(path, search_string)


def edit_wi_object(path, project_id):

    return editing.edit_wi_object(path, project_id)
