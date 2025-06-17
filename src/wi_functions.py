import copy
import sys

sys.path.append("metadata-organizer")
import os
import random
import string
import subprocess
import time

import src.utils as utils
import src.web_interface.editing as editing
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.file_io as file_io
import src.git_whitelists as gwi
import src.web_interface.html_output as html_output
import src.web_interface.searching as searching
import src.web_interface.validation as validation
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.wi_object_to_yaml as oty
import src.web_interface.yaml_to_wi_object as yto
import create_heatmap

# This script contains all functions for generation of objects for the web
# interface


class Webinterface:

    def __init__(self, config):
        (
            self.whitelist_repo,
            self.whitelist_branch,
            self.whitelist_path,
            self.username,
            self.password,
            structure,
            self.update_whitelists,
            self.output_path,
            self.filename,
            self.email,
        ) = utils.parse_config(config)
        self.structure = utils.read_in_yaml(structure)
        self.whitelist_version = fetch_whitelists(self.__dict__)

    def to_dict(self):
        return self.__dict__


def fetch_whitelists(pgm_object):
    whitelist_version = gwi.get_whitelists(
        pgm_object["whitelist_path"],
        pgm_object["whitelist_repo"],
        pgm_object["whitelist_branch"],
        pgm_object["update_whitelists"],
    )
    return whitelist_version


def get_whitelist_object(pgm_object):
    whitelist_object = {
        "whitelists": whitelist_parsing.get_whitelist_object(pgm_object),
        "version": pgm_object["whitelist_version"],
    }
    return whitelist_object


def get_empty_wi_object(pgm_object, read_in_whitelists):
    return yto.get_empty_wi_object(pgm_object["structure"], read_in_whitelists)


def is_empty(pgm_object, wi_object, read_in_whitelsits):
    emtpy_object = yto.get_empty_wi_object(pgm_object["structure"], read_in_whitelsits)
    if wi_object == emtpy_object:
        empty = True
    else:
        empty = False
    return {"empty": empty, "object": emtpy_object}


def get_single_whitelist(ob, read_in_whitelists):
    return whitelist_parsing.get_single_whitelist(ob, read_in_whitelists)


def get_factors(pgm_object, organism, read_in_whitelists):
    return fac_cond.get_factors(organism, pgm_object["structure"], read_in_whitelists)


def get_conditions(pgm_object, factors, organism_name, read_in_whitelists):
    return fac_cond.get_conditions(
        factors, organism_name, pgm_object["structure"], read_in_whitelists
    )


def validate_object(pgm_object, wi_object, read_in_whitelists, finish=False):
    new_object = copy.deepcopy(wi_object)
    return validation.validate_object(
        new_object, pgm_object["structure"], read_in_whitelists, finish,
        pgm_object['email']
    )


def get_summary(pgm_object, wi_object, read_in_whitelists):
    return html_output.get_summary(
        wi_object, pgm_object["structure"], read_in_whitelists
    )


def save_object(dictionary, path, filename, edit_state):
    object, id = file_io.save_object(dictionary, path, filename, edit_state)
    return object, id


def save_filenames(file_str, path):
    return file_io.save_filenames(file_str, path)

def get_plot(pgm_object, config, path, project_id):
    uuid = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
        )
    filename = f"{uuid}_{time.time()}"
    working_path = os.path.join(os.path.dirname(__file__), "..", "..")
    proc = subprocess.Popen(
            [
                "python3",
                "metadata-organizer/metaTools.py",
                "find",
                "-p",
                path,
                "-s",
                f'project:id:"{project_id}',
                "-c",
                config,
                "-o",
                "json",
                "-f",
                filename,
                "-sv",
            ],
            cwd=working_path,
        )
    proc.wait()
    res = utils.read_in_json(os.path.join(working_path, f"{filename}.json"))
    os.remove(os.path.join(working_path, f"{filename}.json"))

    yaml_file = res['data']
    plots = create_heatmap.get_heatmap(yaml_file, pgm_object['structure'], show_setting_id=False)
    plot_list = []
    for elem in plots:
        plot_list.append({'title': elem[0], 'plot': elem[1]})
    return plot_list


# TODO: fix path
def get_meta_info(config, path, project_ids):

    if not isinstance(project_ids, list):
        project_ids = [project_ids]

    metafile = {}
    html_str = ""
    for project_id in project_ids:
        uuid = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
        )
        filename = f"{uuid}_{time.time()}"
        working_path = os.path.join(os.path.dirname(__file__), "..", "..")
        proc = subprocess.Popen(
            [
                "python3",
                "metadata-organizer/metaTools.py",
                "find",
                "-p",
                path,
                "-s",
                f'project:id:"{project_id}',
                "-c",
                config,
                "-o",
                "json",
                "-f",
                filename,
                "-sv",
            ],
            cwd=working_path,
        )
        proc.wait()
        res = utils.read_in_json(os.path.join(working_path, f"{filename}.json"))
        os.remove(os.path.join(working_path, f"{filename}.json"))

        html_str, metafile = searching.get_meta_info(
            html_str,
            res["data"],
            project_id,
            res["validation_reports"] if "validation_reports" in res else None,
        )

    if html_str == "":
        html_str = "No metadata found.<br>"
    return html_str, metafile


def get_search_mask(pgm_object):
    return searching.get_search_mask(pgm_object["structure"])


# TODO: fix path
def find_metadata(config, path, search_string):
    start = time.time()
    uuid = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
    )
    filename = f"{uuid}_{time.time()}"
    working_path = os.path.join(os.path.dirname(__file__), "..", "..")
    proc = subprocess.Popen(
        [
            "python3",
            "metadata-organizer/metaTools.py",
            "find",
            "-p",
            path,
            "-s",
            search_string,
            "-c",
            config,
            "-o",
            "json",
            "-f",
            filename,
            "-sv",
        ],
        cwd=working_path,
    )
    proc.wait()
    subprocess_end = time.time()
    print(
        f'Subprocess "FIND" took {"%.2f" % (subprocess_end - start)} seconds.')
    res = utils.read_in_json(os.path.join(working_path, f"{filename}.json"))
    os.remove(os.path.join(working_path, f"{filename}.json"))
    read_end = time.time()
    print(
        f'Reading and removing the json file took {"%.2f" % (read_end - subprocess_end)} seconds.')
    return res["data"]


def edit_wi_object(path, pgm_object, read_in_whitelists):
    return editing.edit_wi_object(path, pgm_object["structure"], read_in_whitelists)


# TODO: not needed -> in summary
def parse_object(pgm_object, wi_object, read_in_whitelists):
    # read in general structure
    return oty.parse_object(wi_object, pgm_object["structure"],
                            read_in_whitelists)
