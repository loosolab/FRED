import copy
import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.wi_object_to_yaml as oty
import src.web_interface.git_whitelists as git_whitelists
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.validation as validation
import src.web_interface.html_output as html_output
import src.web_interface.file_io as file_io
import src.web_interface.editing as editing
import src.web_interface.searching as searching
import os


# This script contains all functions for generation of objects for the web
# interface

def get_empty_wi_object():

    git_whitelists.get_whitelists()

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))

    return yto.get_empty_wi_object(key_yaml)


def get_single_whitelist(ob):

    return whitelist_parsing.get_single_whitelist(ob)


def get_factors(organism):

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))

    return fac_cond.get_factors(organism, key_yaml)


def get_conditions(factors, organism_name):

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))

    return fac_cond.get_conditions(factors, organism_name, key_yaml)


def validate_object(wi_object, finish=False):
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    new_object = copy.deepcopy(wi_object)
    return validation.validate_object(new_object, key_yaml, finish)


def get_summary(wi_object):

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))

    return html_output.get_summary(wi_object, key_yaml)


def save_object(dictionary, path, filename):
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    object, id = file_io.save_object(key_yaml, dictionary, path, filename)
    return object, id


def save_filenames(file_str, path):

    return file_io.save_filenames(file_str, path)


def get_meta_info(path, project_id):
    html_str, metafile = searching.get_meta_info(path, project_id)
    return html_str


def get_search_mask():
    git_whitelists.get_whitelists()
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    return searching.get_search_mask(key_yaml)


def find_metadata(path, search_string):

    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    return searching.find_metadata(key_yaml, path, search_string)


def edit_wi_object(path, project_id):
    git_whitelists.get_whitelists()
    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    return editing.edit_wi_object(path, project_id, key_yaml)


# TODO: not needed -> in summary
def parse_object(wi_object):

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', 'keys.yaml'))
    return oty.parse_object(wi_object, key_yaml)