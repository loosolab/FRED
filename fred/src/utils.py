import copy
import json
import math
import os
import textwrap
from Bio import Entrez
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
from tabulate import tabulate

# The following functions were copied from Mampok
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/utils.py


def parse_config(config_file):
    config = read_in_yaml(config_file)
    print(config)
    missing_keys = []
    try:
        whitelist_repo = config["whitelist_repository"]
    except KeyError:
        missing_keys.append("whitelist_repository")
        whitelist_repo = "https://github.com/loosolab/FRED_whitelists.git"
    if (
        "private_access" in config
        and "username" in config["private_access"]
        and "password" in config["private_access"]
        and config["private_access"]["username"] is not None
        and config["private_access"]["password"] is not None
    ):
        username = config["private_access"]["username"]
        password = config["private_access"]["password"]
    else:
        username = None
        password = None
    try:
        structure = config["structure"]
        if structure == 'fred':
            structure = os.path.join(os.path.dirname(__file__), '..', 'structure', 'keys.yaml')
        elif structure == 'mampok':
            structure = os.path.join(os.path.dirname(__file__), '..', 'structure', 'mamplan_keys.yaml')
    except KeyError:
        structure = os.path.join(os.path.dirname(__file__), '..', 'structure', 'keys.yaml')
        missing_keys.append("structure")
    try:
        whitelist_branch = config["branch"]
    except KeyError:
        whitelist_branch = "main"
        missing_keys.append("branch")
    try:
        whitelist_path = config["whitelist_path"]
    except KeyError:
        whitelist_path = os.path.join(os.path.dirname(__file__), '..', '..', "FRED_whitelists")
        missing_keys.append("whitelist_path")

    try:
        update_whitelists = config["update_whitelists"]
    except KeyError:
        missing_keys.append("update_whitelist")
        update_whitelists = True
    try:
        output_path = config["output_path"]
    except KeyError:
        output_path = "."
        missing_keys.append("output_path")
    try:
        filename = config["filename"]
    except KeyError:
        filename = "_metadata"
        missing_keys.append("filename")
    try:
        email = config["email"]
    except KeyError:
        email = "Your.Name.Here@example.org"

    if len(missing_keys) > 0:
        print(
            f'The keys {", ".join(missing_keys)} could not be found in the '
            f"config file. FRED is running with default values for those "
            f"keys."
        )
    return (
        whitelist_repo,
        whitelist_branch,
        whitelist_path,
        username,
        password,
        structure,
        update_whitelists,
        output_path,
        filename,
        email
    )


def save_as_yaml(dictionary, file_path):
    """
    save dictionary as YAML file
    :param dictionary: a dictionary that should be saved
    :param file_path: the path of the yaml file to be created
    """
    with open(file_path, "w") as file:
        yaml.dump(dictionary, file, sort_keys=False, Dumper=Dumper)


def read_in_yaml(yaml_file):
    """
    read yaml, auto lower all keys
    :param yaml_file: the path to the yaml file to be read in
    :return: low_output: a dictionary containing the information of the yaml
    """
    with open(yaml_file) as file:
        output = yaml.load(file, Loader=Loader)
    low_output = {k.lower(): v for k, v in output.items()}
    return low_output


def read_in_json(json_file):
    with open(json_file) as file:
        output = json.load(file)
    low_output = {k.lower(): v for k, v in output.items()}
    return low_output


def save_as_json(dictionary, json_file):

    with open(json_file, "w") as f:
        json.dump(dictionary, f)


# The following function was found on Stackoverflow
# https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-
# nested-dictionaries-and-lists
# original function name: findkeys
# submitted by user 'arainchi' on Nov 9, 2013 at 3:14,
# edited on Sep 12, 2019 at 21:50


def find_keys(node, kv):
    """
    generator to return all values of given key in dictionary
    :param node: a dictionary to be searched
    :param kv: the key to search for
    """
    if isinstance(node, list):
        for i in node:
            for x in find_keys(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in find_keys(j, kv):
                yield x


# The following function is based on 'findkeys' and customized to solve
# related problems


def find_values(node, kv):
    """
    generator to return all keys in dictionary that fit a given key value
    :param node: a dictionary to be searched
    :param kv: the key value to search for
    """
    if isinstance(node, list):
        for i in node:
            for x in find_values(i, kv):
                yield x
    elif isinstance(node, dict):
        for val in node.values():
            if isinstance(val, dict) or isinstance(val, list):
                for x in find_values(val, kv):
                    yield x
            else:
                if (
                    (type(kv) is int or type(kv) is float)
                    and (type(val) is int or type(val) is float)
                ) or (type(kv) is bool and type(val) is bool):
                    if kv == val:
                        yield kv
                else:
                    if all(
                        elem in str(val).lower() for elem in str(kv).lower().split(" ")
                    ):
                        yield val


def read_whitelist(key, whitelist_path=None):
    """
    This function reads in a whitelist and returns it.
    :param key: the key that contains a whitelist
    :return: whitelist: the read in whitelist
    """
    print('UTILS PATH', os.path.dirname(__file__))
    if whitelist_path is None:
        print('NO WHITELIST PATH', whitelist_path)
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "FRED_whitelists"
        )
    print('!!!', whitelist_path)
    try:
        whitelist = read_in_json(os.path.join(whitelist_path, "misc", "json", key))
    except (AttributeError, FileNotFoundError):
        try:
            whitelist = read_in_yaml(os.path.join(whitelist_path, "whitelists", key))
        except (AttributeError, FileNotFoundError):
            whitelist = None
    print('WHITELIST IS', whitelist[0:3] if whitelist is not None else whitelist)
    return whitelist


def read_grouped_whitelist(
    whitelist,
    filled_object,
    whitelist_object=None,
    all_plain=False,
    whitelist_path=None,
):
    """
    This function parses a whitelist of type 'group'. If there are more than 30
    values it is formed into a plain whitelist.
    :param whitelist: the read in whitelist
    :param filled_object: a dictionary containing filled information
    :return: whitelist: the read in whitelist
    """
    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "metadata_whitelists"
        )
    headers = {}
    for key in whitelist["whitelist"]:
        if not isinstance(whitelist["whitelist"][key], list):
            new_whitelist = False
            if (
                whitelist_object is not None
                and whitelist["whitelist"][key] in whitelist_object
            ):
                whitelist["whitelist"][key] = get_whitelist(whitelist['whitelist'][key], filled_object, whitelist_object=whitelist_object, all_plain=all_plain, whitelist_path=whitelist_path)
                new_whitelist = True
            elif whitelist['whitelist'][key] is not None and os.path.isfile(
                os.path.join(whitelist_path, "whitelists", whitelist["whitelist"][key])
            ):
                whitelist["whitelist"][key] = get_whitelist(
                    whitelist["whitelist"][key],
                    filled_object,
                    whitelist_object=whitelist_object,
                    all_plain=all_plain,
                    whitelist_path=whitelist_path,
                )
                new_whitelist = True
            if new_whitelist:
                if isinstance(whitelist["whitelist"][key], dict):
                    if whitelist["whitelist"][key]["whitelist_type"] == "depend":
                        if (
                            whitelist["whitelist"]
                            and "whitelist" in whitelist["whitelist"]
                        ):
                            whitelist["whitelist"][key] = whitelist["whitelist"]
                        else:
                            whitelist["whitelist"][key] = None
                    elif whitelist["whitelist"][key]["whitelist_type"] == "group":
                        whitelist["whitelist"][key] = [
                            x
                            for xs in list(whitelist["whitelist"][key].values())
                            for x in xs
                        ]
                    elif whitelist["whitelist"][key]["whitelist_type"] == "plain":
                        if "headers" in whitelist["whitelist"][key]:
                            headers[key] = whitelist["whitelist"][key]["headers"]
                        whitelist["whitelist"][key] = whitelist["whitelist"][key][
                            "whitelist"
                        ]
    if all_plain:
        w = [
            f"{x}"
            for xs in list(whitelist["whitelist"].keys())
            if whitelist["whitelist"][xs] is not None
            for x in whitelist["whitelist"][xs]
            if x is not None
        ]
    else:
        w = [
            f"{x} ({xs})"
            for xs in list(whitelist["whitelist"].keys())
            if whitelist["whitelist"][xs] is not None
            for x in whitelist["whitelist"][xs]
            if x is not None
        ]

    if len(w) > 30:
        new_whitelist = copy.deepcopy(whitelist)
        new_whitelist["whitelist"] = w
        new_whitelist["whitelist_keys"] = list(whitelist["whitelist"].keys())
        whitelist = new_whitelist
        whitelist["whitelist_type"] = "plain_group"
    if len(list(headers.keys())) > 0:
        whitelist["headers"] = headers
    return whitelist


def read_depend_whitelist(
    whitelist, depend, whitelist_object=None, whitelist_path=None
):
    """
    This function parses a whitelist of type 'depend' in order to get the
    values fitting the dependency.
    :param whitelist: the read in whitelist
    :param depend: the key whose values the whitelist depends on
    :return: whitelist: the read in whitelist
    """
    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "metadata_whitelists"
        )
    if depend in whitelist:
        whitelist = whitelist[depend]
    else:
        if whitelist_object is not None and depend in whitelist_object:
            whitelist = whitelist_object[depend]
        elif os.path.isfile(os.path.join(whitelist_path, "whitelists", depend)):
            whitelist = read_whitelist(depend, whitelist_path=whitelist_path)
    if not isinstance(whitelist, list) and not isinstance(whitelist, dict):
        if whitelist_object is not None and whitelist in whitelist_object:
            whitelist = whitelist_object[whitelist]
        elif os.path.isfile(os.path.join(whitelist_path, "whitelists", whitelist)):
            whitelist = read_whitelist(whitelist, whitelist_path=whitelist_path)
    return whitelist


def get_whitelist(
    key, filled_object, whitelist_object=None, all_plain=False, whitelist_path=None
):
    """
    This function reads in a whitelist and parses it depending on its type.
    :param key: the key that contains a whitelist
    :param filled_object: a dictionary containing filled information
    :return: whitelist: the parsed whitelist
    """
    group = False
    stay_depend = False
    plain = False
    abbrev = False

    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "FRED_whitelists"
        )

    if whitelist_object is not None:
        if key in whitelist_object:
            whitelist = whitelist_object[key]
        else:
            whitelist = None
    else:
        whitelist = read_whitelist(key, whitelist_path=whitelist_path)

    while (
        isinstance(whitelist, dict)
        and not group
        and not stay_depend
        and not plain
        and not abbrev
    ):
        if whitelist["whitelist_type"] == "group":
            whitelist = read_grouped_whitelist(
                whitelist,
                filled_object,
                whitelist_object=whitelist_object,
                all_plain=all_plain,
                whitelist_path=whitelist_path,
            )
            group = True
        elif whitelist["whitelist_type"] == "plain":
            plain = True
        elif whitelist["whitelist_type"] == "abbrev":
            abbrev = True
        elif whitelist["whitelist_type"] == "depend":
            depend = list(find_keys(filled_object, whitelist["ident_key"]))
            if len(depend) == 0:
                if whitelist["ident_key"] == "organism_name":
                    depend = list(find_keys(filled_object, "organism"))
            if len(depend) > 0:
                whitelist = read_depend_whitelist(
                    whitelist["whitelist"],
                    depend[0].split(" ")[0],
                    whitelist_object=whitelist_object,
                    whitelist_path=whitelist_path,
                )
            else:
                if all_plain:
                    new_whitelist = []
                    paths = []
                    for key in whitelist["whitelist"]:
                        if not isinstance(
                            whitelist["whitelist"][key], list
                        ) and os.path.isfile(
                            os.path.join(
                                whitelist_path,
                                "whitelists",
                                whitelist["whitelist"][key],
                            )
                        ):
                            paths.append(whitelist["whitelist"][key])
                        else:
                            new_whitelist += whitelist["whitelist"][key]
                    for elem in paths:
                        w_list = get_whitelist(
                            elem, {}, whitelist_object=whitelist_object, all_plain=True
                        )
                        new_whitelist += w_list["whitelist"]
                    whitelist["whitelist"] = new_whitelist

                    whitelist["whitelist_type"] = "plain"
                    plain = True
                else:
                    stay_depend = True

    if group and whitelist["whitelist_type"] != "plain_group" and all_plain:
        new_whitelist = []
        for key in whitelist["whitelist"]:
            if whitelist["whitelist"][key] is not None:
                new_whitelist += whitelist["whitelist"][key]
        whitelist["whitelist"] = new_whitelist
        whitelist["whitelist_type"] = "plain"

    if whitelist:
        if all_plain:
            whitelist["whitelist"] = whitelist["whitelist"]
        elif group and whitelist["whitelist_type"] != "plain_group":
            for key in whitelist["whitelist"]:
                if (
                    whitelist["whitelist"][key] is not None
                    and key != "headers"
                    and key != "whitelist_type"
                    and key != "whitelist_keys"
                ):
                    whitelist["whitelist"][key] = sorted(whitelist["whitelist"][key])
        elif not stay_depend and not abbrev:
            whitelist["whitelist"] = sorted(whitelist["whitelist"])

    return whitelist


def get_key_positions(item, search_key, position=[], positions=[]):
    if isinstance(item, dict):
        for key in item:
            if key == search_key:
                positions.append(position + [key])
            else:
                positions = get_key_positions(
                    item[key], search_key, position + [key], positions
                )
    elif isinstance(item, list):
        for i in range(len(item)):
            positions = get_key_positions(
                item[i], search_key, position + [i], positions
            )
    return positions


def find_position(item, l):
    for elem in l:
        item = item[elem]
    return item


def find_list_key(item, l):
    """
    This function finds an item in a list of dictionaries.
    :param item: the key that should be found
    :param l: a list of dictionaries
    :return: item: a list containing the values of all found keys
    """
    for k in l.split(":"):
        item = list(find_keys(item, k))
    return item


def fill_key(position, value, fill_dict):
    if len(position) > 0:
        if len(position) == 1:
            fill_dict[position[0]] = value
        else:
            if type(position[1]) == str:
                if type(position[0]) == str and position[0] not in fill_dict:
                    fill_dict[position[0]] = {}
            else:
                if position[0] not in fill_dict:
                    fill_dict[position[0]] = []
                if len(fill_dict[position[0]]) < position[1] + 1:
                    for i in range(len(fill_dict[position[0]]), position[1] + 1):
                        fill_dict[position[0]].append({})
            fill_key(position[1:], value, fill_dict[position[0]])
    else:
        print("NO POSITION")


def create_sample_names(metafile, old_sample_names, position, read_in_whitelists=None):
    sample_names = []
    project_id = list(find_keys(metafile, "id"))
    techniques = list(find_keys(metafile, "techniques"))
    organisms = get_whitelist(
        os.path.join("abbrev", "organism_name"),
        metafile,
        whitelist_object=read_in_whitelists,
    )["whitelist"]
    if len(project_id) > 0 and len(techniques) > 0:
        project_id = project_id[0]
        setting_index = position.index("experimental_setting") + 1
        setting = find_position(metafile, position[: setting_index + 1])
        setting_id = list(find_keys(setting, "setting_id"))
        organism = list(find_keys(setting, "organism_name"))
        if len(setting_id) > 0 and len(organism) > 0:
            setting_id = setting_id[0]
            organism = organisms[organism[0]]
            used_techs = None
            for techs in techniques[0]:
                if techs["setting"] == setting_id:
                    used_techs = techs["technique"]
                    break
            if used_techs is not None:
                abbrev_techniques = get_whitelist(
                    os.path.join("abbrev", "technique"),
                    metafile,
                    whitelist_object=read_in_whitelists,
                )["whitelist"]
                abbrev_tech = None
                for u_t in used_techs:
                    abbrev_tech = (
                        abbrev_techniques[u_t] if u_t in abbrev_techniques else u_t
                    )
                    if abbrev_tech is not None:
                        sample_index = position.index("samples") + 1
                        sample = find_position(metafile, position[: sample_index + 1])
                        if (
                            "sample_name" in sample
                            and "number_of_measurements" in sample
                        ):
                            tech_count = find_position(
                                metafile, position[:-1] + ["count"]
                            )
                            filename_length = (
                                len(used_techs)
                                * tech_count
                                * sample["number_of_measurements"]
                            )
                            key_name = f'{setting_id}_{sample["sample_name"]}'
                            if key_name not in old_sample_names.keys():
                                old_sample_names[key_name] = []
                            sample_names = old_sample_names[key_name]
                            if len(old_sample_names[key_name]) < filename_length:
                                sample_techniques = []
                                if len(old_sample_names[key_name]) > 0:
                                    sample_techniques = set(
                                        list(
                                            [
                                                x.split("_")[2]
                                                for x in old_sample_names[key_name]
                                            ]
                                        )
                                    )

                                b_name = sample["sample_name"]

                                for t_count in range(1, tech_count + 1):
                                    for m_count in range(
                                        1, sample["number_of_measurements"] + 1
                                    ):
                                        if abbrev_tech not in sample_techniques:
                                            sample_name = f'{project_id}_{setting_id}_{abbrev_tech}_{organism}_{b_name}_t{"{:02d}".format(t_count)}_m{"{:02d}".format(m_count)}'
                                            sample_names.append(sample_name)

    return sorted(list(set(sample_names)))


def add_value_at_pos(key_yaml, metafile, keys, value, overwrite=False, position=""):
    if keys[0] in key_yaml:
        key_yaml = key_yaml[keys[0]]
        if len(keys) == 1:
            if isinstance(metafile, list):
                for i in range(len(metafile)):
                    if keys[0] in metafile[i]:
                        if key_yaml["list"]:
                            if value not in metafile[i][keys[0]]:
                                metafile[i][keys[0]].append(value)
                        else:
                            if metafile[i][keys[0]] != value and overwrite:
                                metafile[i][keys[0]] = value
            else:
                if keys[0] in metafile:
                    if key_yaml["list"]:
                        if value not in metafile[keys[0]]:
                            metafile[keys[0]].append(value)
                    else:
                        if metafile[keys[0]] != value and overwrite:
                            metafile[keys[0]] = value
                else:
                    if key_yaml["list"]:
                        metafile[keys[0]] = [value]
                    else:
                        metafile[keys[0]] = value
        else:
            if isinstance(metafile, list):
                for i in range(len(metafile)):
                    if keys[0] in metafile[i]:
                        metafile[i][keys[0]] = add_value_at_pos(
                            key_yaml["value"],
                            metafile[i][keys[0]],
                            keys[1:],
                            value,
                            overwrite=overwrite,
                            position=(
                                f"{position}:{keys[0]}" if position != "" else keys[0]
                            ),
                        )
            else:
                if keys[0] in metafile:
                    metafile[keys[0]] = add_value_at_pos(
                        key_yaml["value"],
                        metafile[keys[0]],
                        keys[1:],
                        value,
                        overwrite=overwrite,
                        position=f"{position}:{keys[0]}" if position != "" else keys[0],
                    )
                else:
                    if not key_yaml["list"]:
                        metafile[keys[0]] = add_value_at_pos(
                            key_yaml["value"],
                            {},
                            keys[1:],
                            value,
                            overwrite=overwrite,
                            position=(
                                f"{position}:{keys[0]}" if position != "" else keys[0]
                            ),
                        )
    else:
        print(f"Key {keys[0]} was not found at position {position}.")
    return metafile


def create_filenames(
    metafile, double, position, old_filenames={}, read_in_whitelists=None
):
    filenames = []
    global_index = []
    all_filenames = list(find_keys(metafile, "filenames"))
    if len(all_filenames) > 0:
        for elem in all_filenames:
            for x in elem:
                try:
                    global_index.append(int(x.split("__")[1]))
                except ValueError:
                    pass

    for k in old_filenames:
        for x in old_filenames[k]:
            try:
                global_index.append(int(x.split("__")[1]))
            except ValueError:
                pass

    if len(global_index) > 0:
        global_index = max(global_index) + 1
    else:
        global_index = 1

    local_index = []
    sample_index = position.index("samples")
    samples = find_position(metafile, position[: sample_index + 1])
    cond_filenames = list(
        find_keys(find_position(metafile, position[: sample_index + 1]), "filenames")
    )
    if len(cond_filenames) > 0:
        for elem in cond_filenames:
            for x in elem:
                try:
                    local_index.append(int(x.split("__")[-1]))
                except ValueError:
                    pass

    project_id = list(find_keys(metafile, "id"))
    techniques = list(find_keys(metafile, "techniques"))
    if len(project_id) > 0 and len(techniques) > 0:
        project_id = project_id[0]
        setting_index = position.index("experimental_setting") + 1
        setting = find_position(metafile, position[: setting_index + 1])
        setting_id = list(find_keys(setting, "setting_id"))
        if len(setting_id) > 0:
            setting_id = setting_id[0]

            for sample in samples:
                if (
                    "sample_name" in sample
                    and f'{project_id}_{sample["sample_name"]}' in old_filenames
                ):
                    project_id += [
                        int(x.split("__")[-1])
                        for x in old_filenames[
                            f"{project_id}_" f'{sample["sample_name"]}'
                        ]
                    ]
            if len(local_index) > 0:
                local_index = max(local_index) + 1
            else:
                local_index = 1
            used_techs = None
            for techs in techniques[0]:
                if techs["setting"] == setting_id:
                    used_techs = techs["technique"]
                    break
            if used_techs is not None:
                abbrev_techniques = get_whitelist(
                    os.path.join("abbrev", "technique"),
                    metafile,
                    whitelist_object=read_in_whitelists,
                )["whitelist"]
                abbrev_tech = None
                for u_t in used_techs:
                    tech_local_index = local_index
                    abbrev_tech = (
                        abbrev_techniques[u_t] if u_t in abbrev_techniques else u_t
                    )
                    if abbrev_tech is not None:
                        sample_index = position.index("samples") + 1
                        sample = find_position(metafile, position[: sample_index + 1])
                        if (
                            "sample_name" in sample
                            and "number_of_measurements" in sample
                        ):
                            tech_count = find_position(
                                metafile, position[:-1] + ["count"]
                            )
                            filename_length = (
                                len(used_techs)
                                * tech_count
                                * sample["number_of_measurements"]
                            )
                            key_name = f'{setting_id}_{sample["sample_name"]}'
                            file_techniques = []
                            if key_name not in old_filenames.keys():
                                old_filenames[key_name] = []
                            filenames = old_filenames[key_name]
                            if len(old_filenames[key_name]) < filename_length:
                                if len(old_filenames[key_name]) > 0:
                                    file_techniques = set(
                                        list(
                                            [
                                                x.split("__")[2]
                                                for x in old_filenames[key_name]
                                            ]
                                        )
                                    )

                                b_name = sample["sample_name"]
                                # TODO: change rstrip to removesuffix
                                if b_name.endswith(f'_{b_name.split("_")[-1]}'):
                                    b_name = b_name[: -len(f'_{b_name.split("_")[-1]}')]
                                filename = get_file_name(b_name, double)
                                for t_count in range(1, tech_count + 1):
                                    for m_count in range(
                                        1, sample["number_of_measurements"] + 1
                                    ):
                                        if abbrev_tech not in file_techniques:
                                            filenames.append(
                                                f"{project_id}__{global_index}__{abbrev_tech}__{filename}__{tech_local_index}"
                                            )
                                            global_index += 1
                                            tech_local_index += 1

    return sorted(list(set(filenames)))


def get_file_name(sample_name, double):
    splitted_name = sample_name.split("-")
    new_name = []
    for elem in splitted_name:
        new_elem, gene = split_name(elem, double)
        if new_elem != "":
            new_name.append(new_elem)
    sample_name = "_".join(new_name)
    return sample_name


def NestedDictValues(d):
    for v in d.values():
        if isinstance(v, dict):
            yield from NestedDictValues(v)
        else:
            yield v


def split_name(elem, double, gene=True):
    new_name = []
    if "+" in elem:
        new_split = elem.split("+")
        for part in new_split:
            new_part, gene = split_name(part, double, gene=gene)
            if new_part != "":
                new_name.append(new_part)
        elem = "-".join(new_name)

    if "#" in elem:
        remove = elem.split("#")[0]
        elem, gene = split_name(elem[len(f"{remove}#") :], double, gene=gene)

    if "." in elem:
        if elem.lower() in [f"gn.{x.lower()}" for x in double]:
            gene = False
            elem = ""
        elif elem.lower().startswith("embl.") and gene is True:
            elem = ""
        else:
            elem = elem.split(".")[1]

    return elem, gene


def print_desc(desc, format="plain", size=70):
    new_desc = ""
    if isinstance(desc, list):
        for elem in desc:
            if isinstance(elem, str):
                new_desc += elem
            else:
                if format == "plain":
                    for i in range(len(elem)):
                        for j in range(len(elem[i])):
                            # if format == 'plain':
                            #    elem[i][j] = elem[i][j].replace('\u001b[1m', '').replace('\u001b[22m', '')
                            elem[i][j] = "\n".join(
                                [
                                    "\n".join(
                                        textwrap.wrap(
                                            line,
                                            math.ceil(size * 1 / (len(elem[i]) + 1)),
                                            break_long_words=False,
                                            replace_whitespace=False,
                                        )
                                    )
                                    for line in elem[i][j].splitlines()
                                    if line.strip() != ""
                                ]
                            )
                new_desc += (
                    tabulate(elem, tablefmt=format)
                    .replace(">\n<", "><")
                    .replace(
                        "<td>",
                        f'<td style="width:{int(1/len(elem[0])*100)}%; vertical-align:top;">',
                    )
                )
    else:
        new_desc = desc
    if format == "html":
        new_desc = (
            new_desc.replace("\u001b[1m", "<b>")
            .replace("\u001b[22m", "</b>")
            .replace("\n", "<br>")
            .replace("<table>", '<table class="pgm_desc_table">')
        )
    else:
        new_desc.replace("33[1m", "").replace("33[0;0m", "")
    return new_desc


def get_combis(values, key, result_dict, key_yaml, read_in_whitelists=None):
    """
    This function creates all combinations for one experimental factor that can
    occur multiple tims in one conditions.
    :param values: the chosen values for the experimental factor
    :param key: the name of the experimental factor
    :return: disease_values: a list of all possible combinations of the
                             experimental factor
    """
    # TODO: remove special case
    if key == "gene_editing":
        whitelist_key = "editing_method"
        depend_key = "editing_type"
        whitelist = get_whitelist(
            whitelist_key, result_dict, whitelist_object=read_in_whitelists
        )
    else:
        whitelist_key = None
        depend_key = None
        whitelist = None

    control_values = []
    control = values["control"] if "control" in values else None
    if "control" in values:
        values.pop("control")
        
    key_info = list(find_keys(key_yaml, key))
    if len(key_info) > 0:
        key_info = key_info[0]
    else:
        key_info = None
    if isinstance(values, list):
        possible_values = []
        for i in range(len(values)):
            new_vals = []
            if isinstance(values[i], dict):
                v = "|".join(
                    [
                        f'{k}:"{values[i][k]}"'
                        for k in values[i]
                        if k not in ["ident_key", "control"]
                    ]
                )
                s = f'{key}:{"{"}{v}{"}"}'
            else:
                s = f'{key}:"{values[i]}"'
            for p_val in possible_values:
                new_vals.append(f"{p_val}-{s}")
            possible_values += new_vals
            possible_values.append(s)
        return possible_values

    else:
        values = {
            k: v
            for k, v in values.items()
            if not (type(v) in [list, dict] and len(v) == 0) and v is not None
        }

        if (
            "ident_key" in values
            and values["ident_key"] is not None
            and values["ident_key"] in values
        ):
            ident_key = values["ident_key"]
            start = ident_key
            values.pop("ident_key")
        else:
            ident_key = None
            if "ident_key" in values:
                values.pop("ident_key")
            start = list(values.keys())[0]

        possible_values = {}
        disease_values = []

        depend = []
        for elem in values[start]:
            if isinstance(elem, dict) and "value" in elem and "unit" in elem:
                elem = f'{elem["value"]}{elem["unit"]}'
            value = []
            possible_values[elem] = []
            if control and start in control and control[start] == elem:
                control_values = [f'{start}:"{elem}"']
            else:
                if elem.startswith(f'{start}:{"{"}'):
                    value = [elem]
                elif '"' in elem:
                    value = [f"{start}:{elem}"]
                else:
                    value = [f'{start}:"{elem}"']
            if start == ident_key:
                depend += value
            value = value + control_values

            for val_key in values:
                val_info = [
                    x for x in list(find_keys(key_yaml, val_key)) if isinstance(x, dict)
                ]
                new_controls = []
                value2 = []
                if val_key != start:
                    for x in value:
                        val = x
                        if val not in control_values:
                            for v in values[val_key]:
                                if isinstance(v, dict) and "value" in v and "unit" in v:
                                    v = f'{v["value"]}{v["unit"]}'
                                if (
                                    control
                                    and val_key in control
                                    and control[val_key] == v
                                ):
                                    control_values.append(f'{val_key}:"{v}"')
                                elif (
                                    len(val_info) > 0
                                    and "special_case" in val_info[0]
                                    and "merge" in val_info[0]["special_case"]
                                ):
                                    value2.append(f"{val}|{val_key}:{v}")
                                elif whitelist and val_key == whitelist_key:
                                    g_key = None
                                    for group_key in whitelist["whitelist"]:
                                        if v in whitelist["whitelist"][group_key]:
                                            g_key = group_key
                                            break
                                    if (
                                        g_key == "all"
                                        or f'{depend_key}:"{g_key}"' in val
                                    ):
                                        if v.startswith(f'{val_key}:{"{"}'):
                                            if v not in val:
                                                value2.append(f"{val}|{v}")
                                        else:
                                            if f'{val_key}:"{v}"' not in val:
                                                value2.append(f'{val}|{val_key}:"{v}"')
                                    else:
                                        value2.append(val)
                                elif v.startswith(f'{val_key}:{"{"}'):
                                    if v not in val:
                                        value2.append(f"{val}|{v}")
                                else:
                                    if f'{val_key}:"{v}"' not in val:
                                        value2.append(f'{val}|{val_key}:"{v}"')
                        else:
                            value2.append(val)
                            if (
                                len(val_info) > 0
                                and "special_case" in val_info[0]
                                and "insert_control" in val_info[0]["special_case"]
                            ):
                                for c_val in control_values:
                                    if val_key not in c_val:
                                        for v in values[val_key]:
                                            if (
                                                "special_case" in val_info[0]
                                                and "merge"
                                                in val_info[0]["special_case"]
                                            ):
                                                new_controls.append(
                                                    f"{c_val}|{val_key}:{v}"
                                                )
                                            else:
                                                new_controls.append(
                                                    f'{c_val}|{val_key}:"{v}"'
                                                )
                    value = value2
                control_values += new_controls
            possible_values[elem] = value

        if key_info and key_info["list"]:
            group = None
            if "special_case" in key_info and "group" in key_info["special_case"]:
                group = key_info["special_case"]["group"]

        for z in possible_values:
            for x in possible_values[z]:
                part_values = []
                if x not in control_values:
                    disease_values.append(f'{key}:{"{"}{x}{"}"}')
                    if key_info and key_info["list"] and (group is None or group != z):
                        for d in disease_values:
                            if (
                                f'{key}:{"{"}{x}{"}"}' not in d
                                and f'{d}-{key}:{"{"}{x}{"}"}' not in disease_values
                                and f'{key}:{"{"}{x}{"}"}-{d}' not in disease_values
                            ):
                                part_values.append(f'{d}-{key}:{"{"}{x}{"}"}')
                disease_values += part_values

        disease_values += [f'{key}:{"{"}{x}{"}"}' for x in list(set(control_values))]

        return list(set(disease_values))


def get_condition_combinations(factors):
    """
    This function returns all possible combinations for experimental factors
    :param factors: multiple dictionaries containing the factors and their
                    respective values
    :return: a list containing all combinations of conditions
    """

    # create a list to store all conditions
    combinations = []

    # iterate over the factor dictionaries
    for i in range(len(factors)):

        # iterate over the values in a dictionary
        for value in factors[i]["values"]:

            # if the value is of type value_unit, chain the value and its unit
            # in a string
            if isinstance(value, dict) and "value" in value and "unit" in value:
                value = f'{value["value"]}{value["unit"]}'

            # if the value starts with '<factor>:' then add it to the
            # combinations list, otherwise put the '<factor>:' in front of the
            # value and add it to the combinations list
            if type(value) == str and value.split(":")[0] == factors[i]["factor"]:
                combinations.append(f"{value}")
            else:
                combinations.append(f'{factors[i]["factor"]}:"{value}"')

            # iterate over the factor dictionarie starting at i+1
            for j in range(i + 1, len(factors)):

                # call this function on the sublist of factors from i+1
                comb = get_condition_combinations(factors[j:])

                # iterate over the combinations created from the sublist of
                # factors
                for c in comb:

                    # if the value starts with '<factor>:' than chain it to the
                    # created combination otherwise do the same but add
                    # '<factor>:' in front of the value
                    # add the chained combination to the combinations list
                    if (
                        type(value) == str
                        and value.split(":")[0] == factors[i]["factor"]
                    ):
                        combinations.append(f"{value}-{c}")
                    else:
                        combinations.append(f'{factors[i]["factor"]}:"{value}"-{c}')

    # return a list of all combinations
    return list(set(combinations))


def get_short_name(condition, result_dict, key_yaml, read_in_whitelists=None):
    """
    This function creates an abbreviated version of a condition.
    :param condition: the condition that should be abbreviated
    :param result_dict: a dictionary containing all filled information
    :return: short_condition: an abbreviated version of the condition
    """
    conds = split_cond(condition)
    whitelist = get_whitelist(
        os.path.join("abbrev", "factor"),
        result_dict,
        whitelist_object=read_in_whitelists,
    )["whitelist"]
    short_cond = []
    for c in conds:
        if c[0] in whitelist:
            k = whitelist[c[0]]
        else:
            k = c[0]

        short_cond.append(
            get_short_value(
                c[0],
                k,
                c[1],
                "",
                result_dict,
                key_yaml,
                read_in_whitelists=read_in_whitelists,
            )
        )

    short_condition = "-".join(short_cond).replace("/", "")
    return short_condition


def get_short_value(
    factor,
    short_factor,
    value,
    short_cond,
    result_dict,
    key_yaml,
    read_in_whitelists=None,
):
    if isinstance(value, dict):
        cond_whitelist = get_whitelist(
            os.path.join("abbrev", factor),
            result_dict,
            whitelist_object=read_in_whitelists,
        )
        new_vals = {}
        for v in value:
            new_v = (
                cond_whitelist["whitelist"][v]
                if cond_whitelist and v in cond_whitelist["whitelist"]
                else v
            )
            new_vals[new_v] = get_short_value(
                v,
                new_v,
                value[v],
                short_cond,
                result_dict,
                key_yaml,
                read_in_whitelists=read_in_whitelists,
            )

        val = "+".join(
            [f'{new_vals[x].replace(" ", "")}' for x in list(new_vals.keys())]
        )
        short_cond += f"{short_factor}#{val}"
    else:
        info = list(find_keys(key_yaml, factor))
        # TODO: if wird nicht durchlaufen
        if (
            len(info) > 0
            and "special_case" in info[0]
            and "value_unit" in info[0]["special_case"]
        ):
            short_units = get_whitelist(
                os.path.join("abbrev", "unit"),
                result_dict,
                whitelist_object=read_in_whitelists,
            )["whitelist"]
            value_unit = split_value_unit(value)
            short_cond += (
                f'{short_factor}.{str(value_unit["value"]).replace(".","p")}'
                f'{short_units[value_unit["unit"]] if value_unit["unit"] in short_units else value_unit["unit"]}'
            )
        else:
            val_whitelist = get_whitelist(
                os.path.join("abbrev", factor),
                result_dict,
                whitelist_object=read_in_whitelists,
            )
            if val_whitelist and value.lower() in val_whitelist["whitelist"]:
                short_cond += (
                    f"{short_factor}." f'{val_whitelist["whitelist"][value.lower()]}'
                )
            elif val_whitelist and value in val_whitelist["whitelist"]:
                short_cond += f'{short_factor}.{val_whitelist["whitelist"][value]}'
            else:
                short_cond += f"{short_factor}.{value}"
    return short_cond


def split_value_unit(value_unit):
    """
    This function splits a value_unit (e.g. 2weeks) into a value and unit and
    returns them in a dictionary
    :param value_unit: a string containing a number and a unit
    :return: a dictionary containing value and unit
    """

    # split value and unit
    unit = value_unit.lstrip("0123456789.")
    value = value_unit[: len(value_unit) - len(unit)]
    if "." in value:
        value = float(value)
    else:
        value = int(value)

    return {"value": value, "unit": unit}


def split_cond(condition):
    conditions = []
    count = 0
    cond = '"'
    for i in range(len(condition)):
        if condition[i] == '"':
            count += 1
            cond += condition[i]
        elif condition[i] == "-":
            if count % 2 == 0:
                conditions.append(cond)
                cond = '"'
            else:
                cond += condition[i]
        elif condition[i] == ":":
            if count % 2 == 0:
                cond += f'"{condition[i]}'
            else:
                cond += condition[i]
        elif condition[i] == "{":
            if count % 2 == 0:
                cond += f'{condition[i]}"'
            else:
                cond += condition[i]
        elif condition[i] == "|":
            if count % 2 == 0:
                cond += f',"'
            else:
                cond += condition[i]
        else:
            cond += condition[i]
    conditions.append(cond)
    for j in range(len(conditions)):
        d = json.loads(f'{"{"}{conditions[j]}{"}"}')

        key = list(d.keys())[0]
        conditions[j] = (key, d[key])

    return conditions


def get_publication_object(pubmed_id, email):
    Entrez.email = email
    try:
        handle = Entrez.esummary(db="pubmed", id=pubmed_id, retmode="xml")
        records = list(Entrez.parse(handle))
    except RuntimeError:
        records = None
    return records
