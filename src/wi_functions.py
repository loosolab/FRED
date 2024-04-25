import copy
import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.wi_object_to_yaml as oty
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.validation as validation
import src.web_interface.html_output as html_output
import src.web_interface.file_io as file_io
import src.web_interface.editing as editing
import src.web_interface.searching as searching
import os
import git


# This script contains all functions for generation of objects for the web
# interface

class Webinterface:

    def __init__(self, config):
        self.whitelist_repo, self.whitelist_branch, self.whitelist_path, \
        self.username, self.password, structure, self.update_whitelists, \
        self.output_path, self.filename = utils.parse_config(config)
        if not os.path.exists(self.whitelist_path) or self.update_whitelists:
            self.fetch_whitelists()
        print(os.path.isfile(structure), os.path.dirname(structure))
        self.structure = utils.read_in_yaml(structure)

    def to_dict(self):
        return self.__dict__
    

def fetch_whitelists(pgm_object):
    print('Fetching whitelists...\n')
    if not os.path.exists(pgm_object.whitelist_path):
        repo = git.Repo.clone_from(pgm_object.whitelist_repo,
                                   pgm_object.whitelist_path,
                                   branch=pgm_object.whitelist_branch)
    else:
        repo = git.Git(pgm_object.whitelist_path)
        repo.pull('origin', pgm_object.whitelist_branch)


def get_empty_wi_object(pgm_object):

    return yto.get_empty_wi_object(pgm_object.structure)


def get_single_whitelist(ob):

    return whitelist_parsing.get_single_whitelist(ob)


def get_factors(pgm_object, organism):

    return fac_cond.get_factors(organism, pgm_object.structure)


def get_conditions(pgm_object, factors, organism_name):

    return fac_cond.get_conditions(factors, organism_name,
                                   pgm_object.structure)


def validate_object(pgm_object, wi_object, finish=False):
    new_object = copy.deepcopy(wi_object)
    return validation.validate_object(new_object, pgm_object.structure, finish)


def get_summary(pgm_object, wi_object):

    return html_output.get_summary(wi_object, pgm_object.structure)


def save_object(dictionary, path, filename, edit_state):
    object, id = file_io.save_object(dictionary, path, filename, edit_state)
    return object, id


def save_filenames(file_str, path):

    return file_io.save_filenames(file_str, path)


def get_meta_info(pgm_object, path, project_ids):
    if not isinstance(project_ids, list):
        project_ids = [project_ids]
    html_str, metafile = searching.get_meta_info(pgm_object.structure, path,
                                                     project_ids)
    return html_str


def get_search_mask(pgm_object):
    return searching.get_search_mask(pgm_object.structure)


def find_metadata(pgm_object, path, search_string):
    return searching.find_metadata(pgm_object.structure, path, search_string)


def edit_wi_object(pgm_object, path):
    return editing.edit_wi_object(path, pgm_object.structure)


# TODO: not needed -> in summary
def parse_object(pgm_object, wi_object):

    # read in general structure
    return oty.parse_object(wi_object, pgm_object.structure)
