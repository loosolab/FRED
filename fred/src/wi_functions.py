import copy
import sys

sys.path.append("metadata-organizer")
import os
import random
import string
import subprocess
import time
import json

import fred.src.utils as utils
import fred.src.web_interface.editing as editing
import fred.src.web_interface.factors_and_conditions as fac_cond
import fred.src.web_interface.file_io as file_io
import fred.src.git_whitelists as gwi
import fred.src.web_interface.html_output as html_output
import fred.src.web_interface.searching as searching
import fred.src.web_interface.validation as validation
import fred.src.web_interface.whitelist_parsing as whitelist_parsing
import fred.src.web_interface.wi_object_to_yaml as oty
import fred.src.web_interface.yaml_to_wi_object as yto
import fred.src.heatmap.create_heatmap as create_heatmap
from jinja2 import Template

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
        new_object,
        pgm_object["structure"],
        read_in_whitelists,
        finish,
        pgm_object["email"],
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


def get_plot_from_object(pgm_object, object):
    yaml_file = object
    try:
        template = Template(
        '''             
        {% if input.html %}
            {{ input.html }}
        {% else %}            
            <div style="overflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:20">
                {% if input.plot %}
                    {{ input.plot }}
                {% endif %}
                        
                {% if input.missing_samples %}
                    <i>Conditions without samples:</i>
                    {{ input.missing_samples }}
                {% endif %}
                </div>
        {% endif %}
        '''
        )
        plots = create_heatmap.get_heatmap(
            yaml_file, pgm_object["structure"], show_setting_id=False
        )
        plot_list = []
        for elem in plots:
            add_plot = {}
            if elem[1] is not None:
                add_plot["plot"] = (
                            elem[1].to_html(full_html=False, include_plotlyjs="cdn")
                            if elem[1] is not None
                            else elem[1]
                        )
            if elem[2] is not None:
                add_plot["missing_samples"] = html_output.object_to_html(
                    elem[2], 0, False
                )
            plot_list.append(
                {"title": elem[0], "plot": template.render(input=add_plot)}
            )
    except:
        plot_list = []
    return plot_list


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

    try:
        yaml_file = utils.read_in_yaml(res['data'][0]['path'])
        template = Template(
        '''              
        {% if input.html %}
            {{ input.html }}
        {% else %}            
            <div style="overflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:20">
                    {% if input.plot %}
                        {{ input.plot }}
                    {% endif %}
                    
                    {% if input.missing_samples %}
                        <i>Conditions without samples:</i>
                        {{ input.missing_samples }}
                    {% endif %}
            </div>
        {% endif %}
        '''
        )
        plots = create_heatmap.get_heatmap(yaml_file, pgm_object['structure'], show_setting_id=False)
        plot_list = []
        for elem in plots:
            add_plot = {}
            if elem[1] is not None:
                add_plot['plot'] = elem[1]
            if elem[2] is not None:
                add_plot['missing_samples'] = html_output.object_to_html(elem[2], 0, False)
            plot_list.append({'title': elem[0], 'plot': template.render(input=add_plot)})
    except:
        plot_list = []
    return plot_list


def download_plot(pgm_object, finished_yaml, save_path):
    plots = create_heatmap.get_heatmap(
                    finished_yaml, pgm_object["structure"], show_setting_id=True, labels="all", background=True
                )
    filenames = []
    try:
        project_id = finished_yaml['project']['id']
    except KeyError:
        project_id = 'missingID'
    for i in range(len(plots)):
        if plots[i][1] is not None:
            filename = f'{project_id}_{plots[i][0]}.png'
            plots[i][1].write_image(os.path.join(save_path, filename), format="png")
            filenames.append(filename)
    return filenames

def get_meta_info_from_object(object):
    try:
        project_id = object['project']['id']
    except KeyError:
        project_id = ''
    return searching.get_html_str('', object, project_id, None)


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
                "fred",
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
            "fred",
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
    print(f'Subprocess "FIND" took {"%.2f" % (subprocess_end - start)} seconds.')
    res = utils.read_in_json(os.path.join(working_path, f"{filename}.json"))
    os.remove(os.path.join(working_path, f"{filename}.json"))
    read_end = time.time()
    print(
        f'Reading and removing the json file took {"%.2f" % (read_end - subprocess_end)} seconds.'
    )
    return res["data"]


def edit_wi_object(path, pgm_object, read_in_whitelists):
    return editing.edit_wi_object(path, pgm_object["structure"], read_in_whitelists)


# TODO: not needed -> in summary
def parse_object(pgm_object, wi_object, read_in_whitelists, return_id=False):
    # read in general structure
    return oty.parse_object(wi_object, pgm_object["structure"], read_in_whitelists, return_id=return_id)


def parse_search_string_to_query(search_string, structure):
    if not search_string.startswith("("):
        search_string = f'({search_string})'

    query = ""
    sub_list = ""
    sub = ""

    # set brace_count to 0 meaning that there is currently no open
    # brace
    brace_count = 0

    # iterate over search string
    for letter in search_string:

        # if an opening bracket is reached, add 1 to brace_count, add
        # the string within sub to the sub_list and set sub to an empty
        # string
        if letter == "(":
            brace_count += 1
            sub_list += sub
            sub = ""

        # if a closing bracket is reached, subtract 1 from brace_count
        elif letter == ")":
            brace_count -= 1

            if sub != "":
                res = parse_string_to_query_dict(sub, structure)
                sub_list += res

            # set sub to an empty string again
            sub = ""

        else:

            # add the current character of the search string to sub
            sub += letter

    sub_list = parse_string_to_query_dict(sub_list, structure)
    # add a dictionary containing information about the metadata file
    # to result if it matches the search
    # key: project id
    # value: whole metafile or path to metafile depending on whether
    # result_dict is set to True or False
    d = json.loads(sub_list)
    return d


def get_text_keys(structure, pre=''):
    keys =  []
    for key in structure:
        if 'input_type' in structure[key]:
            if structure[key]['input_type'] in ['short_text', 'long_text', 'select', 'restricted_short_text']:
                keys.append(f'{pre}.{key}'.strip('.'))
        else:
            if 'value' in structure[key] and isinstance(structure[key]['value'], dict):
                keys += get_text_keys(structure[key]['value'], key)
    return keys

def get_all_query(keys, value):
    key_query =  []
    for key in keys:
        key_query.append(f'{"{"} "{key}": {"{"} "$regex": "{value}", "$options": "i" {"}"} {"}"}')
    
    return key_query
    


def parse_string_to_query_dict(string, structure, all_keys=None):
    regex_chars = ['(', ')', '[', ']', '*', '+', '?']
    if ' or ' in string:
        or_vals = string.split(' or ')
        for i in range(len(or_vals)):
            if not or_vals[i].startswith('{ '):
                if 'and' in or_vals[i]:
                    and_vals = or_vals[i].split(' and ')
                    for j in range(len(and_vals)):
                        if not and_vals[j].startswith('{ '):
                            is_not = False
                            if and_vals[j].strip().startswith('not '):
                                and_vals[j] = and_vals[j].split('not ')[1].strip()
                                is_not = True
                            if '"' in and_vals[j]:
                                key, value = and_vals[j].rstrip('"').split('"')
                                for rc in regex_chars:
                                    value = value.replace(rc, f'\\\\{rc}')
                                if key != '':
                                    end_key = key.rstrip(':').split(':')[-1]
                                    start_key = '.'.join(key.rstrip(':').split(':')[:-1])
                                    key_params = list(utils.find_keys(structure, end_key))
                                    if len(key_params) > 0 and 'special_case' in key_params[0] and 'merge' in key_params[0]['special_case']:
                                        key_params = key_params[0]
                                        if 'value' in key_params:
                                            sub_keys = [k for k in key_params['value']]
                                            sub_values = value.split(' ')
                                            sub_and_vals = []
                                            for sv in sub_values:
                                               sub_or_vals = []
                                               for sk in sub_keys:
                                                   full_key = f'{start_key}.{end_key}.{sk}'
                                                   sub_or_vals.append(f'{"{"} "{full_key}": {"{"} "$regex": "{sv}", "$options": "i" {"}"} {"}"}') 
                                               sub_and_value = f'[ {", ".join(sub_or_vals)} ]'
                                               sub_and_vals.append(f'{"{"} "$or": {sub_and_value} {"}"}')
                                        sub_and_value = f'[ {", ".join(sub_and_vals)} ]'
                                        search_val = f'"$and": {sub_and_value}'
                                    else:
                                        key = key.replace(':', '.').rstrip('.')
                                        value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                                        search_val = f'"{key}": {value}'
                                else:
                                    if all_keys is None:
                                        all_keys = get_text_keys(structure)
                                    value = f'[ {", ".join(get_all_query(all_keys, and_vals[j]))} ]'
                                    search_val = f'"$or": {value}'
                            else:
                                if all_keys is None:
                                    all_keys = get_text_keys(structure)
                                key = "$or"
                                value = f'[ {", ".join(get_all_query(all_keys, and_vals[j]))} ]'
                                search_val = f'"{key}": {value}'
                            if is_not:
                                and_vals[j] = f'{"{"} "$not": {"{"} {search_val} {"}"} {"}"}'
                            else:
                                and_vals[j] = f'{"{"} {search_val} {"}"}'
                    or_vals[i] = f'{"{"} "$and": [ {", ".join(and_vals)} ] {"}"}'
                else:
                    is_not = False
                    if or_vals[i].strip().startswith('not '):
                        or_vals[i] = or_vals[i].split('not ')[1].strip()
                        is_not = True
                    if '"' in or_vals[i]:
                        key, value = or_vals[i].rstrip('"').split('"')
                        for rc in regex_chars:
                                    value = value.replace(rc, f'\\\\{rc}')
                        if key != '':
                            end_key = key.rstrip(':').split(':')[-1]
                            start_key = '.'.join(key.rstrip(':').split(':')[:-1])
                            key_params = list(utils.find_keys(structure, end_key))
                            if len(key_params) > 0 and 'special_case' in key_params[0] and 'merge' in key_params[0]['special_case']:
                                key_params = key_params[0]
                                if 'value' in key_params:
                                    sub_keys = [k for k in key_params['value']]
                                    sub_values = value.split(' ')
                                    sub_and_vals = []
                                    for sv in sub_values:
                                        sub_or_vals = []
                                        for sk in sub_keys:
                                            full_key = f'{start_key}.{end_key}.{sk}'
                                            sub_or_vals.append(f'{"{"} "{full_key}": {"{"} "$regex": "{sv}", "$options": "i" {"}"} {"}"}') 
                                        sub_and_value = f'[ {", ".join(sub_or_vals)} ]'
                                        sub_and_vals.append(f'{"{"} "$or": {sub_and_value} {"}"}')
                                    sub_and_value = f'[ {", ".join(sub_and_vals)} ]'
                                    search_val = f'"$and": {sub_and_value}'
                                else:
                                    key = key.replace(':', '.').rstrip('.')
                                    value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                                    search_val = f'"{key}": {value}'
                            else:
                                key = key.replace(':', '.').rstrip('.')
                                value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                                search_val = f'"{key}": {value}'
                        else:
                            if all_keys is None:
                                all_keys = get_text_keys(structure)
                            key = "$or"
                            value = f'[ {", ".join(get_all_query(all_keys, or_vals[i]))} ]'
                            search_val = f'"{key}": {value}'
                    else:
                        if all_keys is None:
                            all_keys = get_text_keys(structure)
                        key = "$or"
                        value = f'[ {", ".join(get_all_query(all_keys, or_vals[i]))} ]'
                        search_val = f'"{key}": {value}'
                    if is_not:
                        or_vals[i] = f'{"{"} "$not": {"{"} {search_val} {"}"} {"}"}'
                    else:
                        or_vals[i] = f'{"{"} {search_val} {"}"}'
        res = f'{"{"} "$or": [ {", ".join(or_vals)} ] {"}"}'
    elif ' and ' in string:
        and_vals = string.split(' and ')
        for i in range(len(and_vals)):
            if not and_vals[i].startswith('{ '):
                is_not = False
                if and_vals[i].strip().startswith('not '):
                    and_vals[i] = and_vals[i].split('not ')[1].strip()
                    is_not = True
                if '"' in and_vals[i]:
                    key, value = and_vals[i].rstrip('"').split('"')
                    for rc in regex_chars:
                        value = value.replace(rc, f'\\\\{rc}')
                    if key != '':
                        end_key = key.rstrip(':').split(':')[-1]
                        start_key = '.'.join(key.rstrip(':').split(':')[:-1])
                        key_params = list(utils.find_keys(structure, end_key))
                        if len(key_params) > 0 and 'special_case' in key_params[0] and 'merge' in key_params[0]['special_case']:
                            key_params = key_params[0]
                            if 'value' in key_params:
                                sub_keys = [k for k in key_params['value']]
                                sub_values = value.split(' ')
                                sub_and_vals = []
                                for sv in sub_values:
                                    sub_or_vals = []
                                    for sk in sub_keys:
                                        full_key = f'{start_key}.{end_key}.{sk}'
                                        sub_or_vals.append(f'{"{"} "{full_key}": {"{"} "$regex": "{sv}", "$options": "i" {"}"} {"}"}') 
                                    sub_and_value = f'[ {", ".join(sub_or_vals)} ]'
                                    sub_and_vals.append(f'{"{"} "$or": {sub_and_value} {"}"}')
                                sub_and_value = f'[ {", ".join(sub_and_vals)} ]'
                                search_val = f'"$and": {sub_and_value}'
                            else:
                                key = key.replace(':', '.').rstrip('.')
                                value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                                search_val = f'"{key}": {value}'
                        else:
                            key = key.replace(':', '.').rstrip('.') 
                            value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                            search_val = f'"{key}": {value}'
                    else:
                        if all_keys is None:
                            all_keys = get_text_keys(structure)
                        key = "$or"
                        value = f'[ {", ".join(get_all_query(all_keys, and_vals[i]))} ]'
                        search_val = f'"{key}": {value}'
                else:
                    if all_keys is None:
                        all_keys = get_text_keys(structure)
                    key = "$or"
                    value = f'[ {", ".join(get_all_query(all_keys, and_vals[i]))} ]'
                    search_val = f'"{key}": {value}'
                if is_not:
                    and_vals[i] = f'{"{"} "$not": {"{"} {search_val} {"}"} {"}"}'
                else:
                    and_vals[i] = f'{"{"} {search_val} {"}"}'
        res = f'{"{"} "$and": [ {", ".join(and_vals)} ] {"}"}'
    else:
        is_not = False
        if not string.startswith('{ '):
            if string.strip().startswith('not '):
                string = string.split('not ')[1].strip()
                is_not = True
            if '"' in string:
                key, value = string.rstrip('"').split('"')
                for rc in regex_chars:
                    value = value.replace(rc, f'\\\\{rc}')
                if key != '':
                    end_key = key.rstrip(':').split(':')[-1]
                    start_key = '.'.join(key.rstrip(':').split(':')[:-1])
                    key_params = list(utils.find_keys(structure, end_key))
                    if len(key_params) > 0 and 'special_case' in key_params[0] and 'merge' in key_params[0]['special_case']:
                        key_params = key_params[0]
                        if 'value' in key_params:
                            sub_keys = [k for k in key_params['value']]
                            sub_values = value.split(' ')
                            sub_and_vals = []
                            for sv in sub_values:
                                sub_or_vals = []
                                for sk in sub_keys:
                                    full_key = f'{start_key}.{end_key}.{sk}'
                                    sub_or_vals.append(f'{"{"} "{full_key}": {"{"} "$regex": "{sv}", "$options": "i" {"}"} {"}"}') 
                                sub_and_value = f'[ {", ".join(sub_or_vals)} ]'
                                sub_and_vals.append(f'{"{"} "$or": {sub_and_value} {"}"}')
                            sub_and_value = f'[ {", ".join(sub_and_vals)} ]'
                            search_val = f'"$and": {sub_and_value}'
                        else:
                            key = key.replace(':', '.').rstrip('.')
                            value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                            search_val = f'"{key}": {value}'
                    else:
                        key = key.replace(':', '.').rstrip('.') 
                        value = f'{"{"} "$regex": "{value}", "$options": "i" {"}"}'
                        search_val = f'"{key}": {value}'
                else:
                    if all_keys is None:
                        all_keys = get_text_keys(structure)
                    key = "$or"
                    value = f'[ {", ".join(get_all_query(all_keys, value))} ]'
                    search_val = f'"{key}": {value}'
            else:
                if all_keys is None:
                    all_keys = get_text_keys(structure)
                key = "$or"
                value = f'[ {", ".join(get_all_query(all_keys, string))} ]'
                search_val = f'"{key}": {value}'
            if is_not:
                res = f'{"{"} "$not": {"{"} {search_val} {"}"} {"}"}'
            else:
                res = f'{"{"} {search_val} {"}"}'
        else:
            res=string
    return res
            

def get_metadata_search_view(metadata_path):

    metadata = utils.read_in_yaml(metadata_path)
    res = {}

    try:
        res["id"] = metadata["project"]["id"]
    except KeyError:
        res["id"] = None
    
    try:
        res["project_name"] = metadata["project"]["project_name"]
    except KeyError:
        res["project_name"] = None

    try:
        res["owner"] = metadata["project"]["owner"]["name"]
    except KeyError:
        res["owner"] = None

    try:
        res["email"] = metadata["project"]["owner"]["email"]
    except KeyError:
        res["email"] = None

    res["organisms"] = list(set(utils.find_keys(metadata, "organism_name")))

    technique = []

    techniques = list(utils.find_keys(metadata, "technique"))
    for elem in techniques:
        technique += elem
    technique = list(set(technique))
    res['technique'] = technique

    try:
        res["description"] = metadata["project"]["description"]
    except KeyError:
        res["description"] = None

    try:
        res["date"] = metadata["project"]["date"]
    except KeyError:
        res["date"] = None

    if "nerd" in metadata["project"]:
        nerds = []
        for nerd in metadata["project"]["nerd"]:
            nerds.append(nerd["name"])
        res["nerd"] = nerds
    else:
        res["nerd"] = None

    cell_type = list(set(utils.find_keys(metadata, "cell_type")))
    res["cell_type"] = cell_type

    tissue = []

    tissues = list(utils.find_keys(metadata, "tissue"))
    for elem in tissues:
        tissue += elem
    tissue = list(set(tissue))
    res["tissue"] = tissue

    # treatment
    treatment = []

    medical = list(
        utils.find_list_key(metadata, "medical_treatment:treatment_type")
    )
    treatment += list(set(medical))

    physical = list(utils.find_keys(metadata, "physical_treatment"))
    treatment += list(set(physical))

    injury = list(utils.find_list_key(metadata, "injury:injury_type"))
    treatment += list(set(injury))

    res["treatment"] = treatment

    # disease

    disease = list(utils.find_list_key(metadata, "disease:disease_type"))
    res["disease"] = list(set(disease))

    return res

def read_metadata(path):
    return utils.read_in_yaml(path)

def get_metadata(path):
    full_metadata = utils.read_in_yaml(path)
    search_view = get_metadata_search_view(path)
    return full_metadata, search_view