import time

from tabulate import tabulate
import textwrap
import yaml
import os
import copy
import json

# The following functions were copied from Mampok
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/utils.py


def save_as_yaml(dictionary, file_path):
    """
    save dictionary as YAML file
    :param dictionary: a dictionary that should be saved
    :param file_path: the path of the yaml file to be created
    """
    with open(file_path, 'w') as file:
        documents = yaml.dump(dictionary, file, sort_keys=False)


def read_in_yaml(yaml_file):
    """
    read yaml, auto lower all keys
    :param yaml_file: the path to the yaml file to be read in
    :return: low_output: a dictionary containing the information of the yaml
    """
    with open(yaml_file) as file:
        output = yaml.load(file, Loader=yaml.FullLoader)
    low_output = {k.lower(): v for k, v in output.items()}
    return low_output


def read_in_json(json_file):
    with open(json_file) as file:
        output = json.load(file)
    low_output = {k.lower(): v for k, v in output.items()}
    return low_output


def save_as_json(dictionary, json_file):

    with open(json_file, 'w') as f:
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
                if ((type(kv) is int or type(
                        kv) is float) and (
                            type(val) is int or type(val) is float)) or (
                        type(kv) is bool and type(val) is bool):
                    if kv == val:
                        yield kv
                else:
                    if all(elem in str(val).lower() for elem in str(kv).lower().split(' ')):
                        yield val


def read_whitelist(key, whitelist_path=None):
    """
    This function reads in a whitelist and returns it.
    :param key: the key that contains a whitelist
    :return: whitelist: the read in whitelist
    """
    if whitelist_path is None:
        whitelist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists')
    try:
        whitelist = read_in_json(os.path.join(whitelist_path, 'misc', 'json', key))
    except (AttributeError, FileNotFoundError):
        try:
            whitelist = read_in_yaml(
                os.path.join(whitelist_path, 'whitelists', key))
        except (AttributeError, FileNotFoundError):
            whitelist = None
    return whitelist


def read_grouped_whitelist(whitelist, filled_object, all_plain=False, whitelist_path=None):
    """
    This function parses a whitelist of type 'group'. If there are more than 30
    values it is formed into a plain whitelist.
    :param whitelist: the read in whitelist
    :param filled_object: a dictionary containing filled information
    :return: whitelist: the read in whitelist
    """
    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            'metadata_whitelists')
    headers = {}
    for key in whitelist['whitelist']:
        if not isinstance(whitelist['whitelist'][key], list) and \
                os.path.isfile(
                os.path.join(whitelist_path, 'whitelists',
                             whitelist['whitelist'][key])):
            whitelist['whitelist'][key] = \
                get_whitelist(whitelist['whitelist'][key], filled_object, all_plain=all_plain, whitelist_path=whitelist_path)
            if isinstance(whitelist['whitelist'][key], dict):
                if whitelist['whitelist'][key]['whitelist_type'] == 'depend':
                    if whitelist['whitelist'] and 'whitelist' in \
                            whitelist['whitelist']:
                        whitelist['whitelist'][key] = whitelist['whitelist']
                    else:
                        whitelist['whitelist'][key] = None
                elif whitelist['whitelist'][key]['whitelist_type'] == 'group':
                    whitelist['whitelist'][key] = \
                        [x for xs in list(whitelist['whitelist'][key].values())
                         for x in xs]
                elif whitelist['whitelist'][key]['whitelist_type'] == 'plain':
                    if 'headers' in whitelist['whitelist'][key]:
                        headers[key] = whitelist['whitelist'][key]['headers']
                    whitelist['whitelist'][key] = \
                        whitelist['whitelist'][key]['whitelist']
    if all_plain:
        w = [f'{x}' for xs in list(whitelist['whitelist'].keys()) if
             whitelist['whitelist'][xs] is not None for x in
             whitelist['whitelist'][xs] if x is not None]
    else:
        w = [f'{x} ({xs})' for xs in list(whitelist['whitelist'].keys()) if
             whitelist['whitelist'][xs] is not None for x in
             whitelist['whitelist'][xs] if x is not None]

    if len(w) > 30:
        new_whitelist = copy.deepcopy(whitelist)
        new_whitelist['whitelist'] = w
        new_whitelist['whitelist_keys'] = list(whitelist['whitelist'].keys())
        whitelist = new_whitelist
        whitelist['whitelist_type'] = 'plain_group'
    if len(list(headers.keys())) > 0:
        whitelist['headers'] = headers
    return whitelist


def read_depend_whitelist(whitelist, depend, whitelist_path=None):
    """
    This function parses a whitelist of type 'depend' in order to get the
    values fitting the dependency.
    :param whitelist: the read in whitelist
    :param depend: the key whose values the whitelist depends on
    :return: whitelist: the read in whitelist
    """
    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            'metadata_whitelists')
    if depend in whitelist:
        whitelist = whitelist[depend]
    elif os.path.isfile(os.path.join(whitelist_path,
            'whitelists', depend)):
        whitelist = read_whitelist(depend, whitelist_path=whitelist_path)
    if not isinstance(whitelist, list) and not isinstance(whitelist, dict) \
            and os.path.isfile(os.path.join(
            whitelist_path, 'whitelists',
            whitelist)):
        whitelist = read_whitelist(whitelist, whitelist_path=whitelist_path)
    return whitelist


def get_whitelist(key, filled_object, all_plain=False, whitelist_path=None):
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
    whitelist = read_whitelist(key, whitelist_path=whitelist_path)
    if whitelist_path is None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            'metadata_whitelists')

    while isinstance(whitelist,
                     dict) and not group and not stay_depend and not \
            plain and not abbrev:
        if whitelist['whitelist_type'] == 'group':
            whitelist = read_grouped_whitelist(whitelist, filled_object, all_plain=all_plain, whitelist_path=whitelist_path)
            group = True
        elif whitelist['whitelist_type'] == 'plain':
            plain = True
        elif whitelist['whitelist_type'] == 'abbrev':
            abbrev = True
        elif whitelist['whitelist_type'] == 'depend':
            depend = list(find_keys(filled_object, whitelist['ident_key']))
            if len(depend) == 0:
                if whitelist['ident_key'] == 'organism_name':
                    depend = list(find_keys(filled_object, 'organism'))
            if len(depend) > 0:
                whitelist = read_depend_whitelist(whitelist['whitelist'],
                                                  depend[0].split(' ')[0], whitelist_path=whitelist_path)
            else:
                if all_plain:
                    new_whitelist = []
                    paths = []
                    for key in whitelist['whitelist']:
                        if not isinstance(whitelist['whitelist'][key], list) and os.path.isfile(os.path.join(whitelist_path, 'whitelists', whitelist['whitelist'][key])):
                            paths.append(whitelist['whitelist'][key])
                        else:
                            new_whitelist += whitelist['whitelist'][key]
                    for elem in paths:
                        w_list = get_whitelist(elem, {}, True)
                        new_whitelist += w_list['whitelist']
                    whitelist['whitelist'] = new_whitelist

                    whitelist['whitelist_type'] = 'plain'
                    plain = True
                else:
                    stay_depend = True

    if group and whitelist['whitelist_type'] != 'plain_group' and all_plain:
        new_whitelist = []
        for key in whitelist['whitelist']:
            if whitelist['whitelist'][key] is not None:
                new_whitelist += whitelist['whitelist'][key]
        whitelist['whitelist'] = new_whitelist
        whitelist['whitelist_type'] = 'plain'

    if whitelist:
        if all_plain:
            whitelist['whitelist'] = whitelist['whitelist']
        elif group and whitelist['whitelist_type'] != 'plain_group':
            for key in whitelist['whitelist']:
                if whitelist['whitelist'][key] is not None and key != 'headers' \
                        and key != 'whitelist_type' and key != 'whitelist_keys':
                    whitelist['whitelist'][key] = sorted(
                        whitelist['whitelist'][key])
        elif not stay_depend and not abbrev:
            whitelist['whitelist'] = sorted(whitelist['whitelist'])

    return whitelist


def find_list_key(item, l):
    """
    This function finds an item in a list of dictionaries.
    :param item: the key that should be found
    :param l: a list of dictionaries
    :return: item: a list containing the values of all found keys
    """
    for k in l.split(':'):
        item = list(find_keys(item, k))
    return item


def create_filenames(metafile, double):
    file_indices = list(find_keys(metafile, 'filenames'))
    if len(file_indices) > 0:
        indices = []
        for i in file_indices:
            indices += [int(x.split('__')[1]) for x in i]
        file_index = max(indices) + 1
    else:
        file_index = 1

    organisms = get_whitelist(os.path.join('abbrev', 'organism_name'),
                                   metafile)['whitelist']
    project_id = list(find_keys(metafile, 'id'))
    techniques = list(find_keys(metafile, 'techniques'))
    if len(project_id) > 0 and len(techniques) > 0:
        project_id = project_id[0]
        if 'experimental_setting' in metafile:
            for setting_elem in metafile['experimental_setting']:
                if 'setting_id' in setting_elem:
                    setting_id = setting_elem['setting_id']
                    organism = list(find_keys(setting_elem, 'organism_name'))
                    if len(organism) > 0:
                        organism = organisms[organism[0]]
                        if 'conditions' in setting_elem:
                            used_techs = None
                            for techs in techniques[0]:
                                if techs['setting'] == setting_id:
                                    used_techs = techs['technique']
                                    break
                            abbrev_techniques = {}
                            if used_techs is not None:
                                abbrev_techniques = get_whitelist(
                                    os.path.join('abbrev', 'technique'),
                                    metafile)['whitelist']
                            old_filenames = {}
                            old_sample_names = {}
                            for u_t in used_techs:
                                abbrev_tech = abbrev_techniques[u_t] if u_t in abbrev_techniques else u_t
                                for cond_elem in setting_elem['conditions']:
                                    if 'biological_replicates' in cond_elem and 'samples' in \
                                            cond_elem['biological_replicates']:
                                        local_count = 1
                                        for sample_elem in cond_elem['biological_replicates']['samples']:
                                            if 'technical_replicates' in sample_elem and 'count' in sample_elem['technical_replicates']:
                                                if 'sample_name' in sample_elem and 'number_of_measurements' in sample_elem:
                                                    filename_length = len(used_techs) * sample_elem['technical_replicates']['count'] * sample_elem['number_of_measurements']
                                                    sample_techniques = []
                                                    file_techniques = []
                                                    sample_names = []
                                                    filenames = []
                                                    do_samples = False
                                                    do_files = False
                                                    if sample_elem['sample_name'] not in old_sample_names.keys():
                                                        old_sample_names[sample_elem['sample_name']] = len(sample_elem['technical_replicates']['sample_name']) if 'sample_name' in sample_elem['technical_replicates'] else 0
                                                    if old_sample_names[sample_elem['sample_name']] < filename_length:
                                                        do_samples = True
                                                        if old_sample_names[sample_elem['sample_name']] > 0:
                                                            sample_techniques = set(list([x.split('_')[2] for x in sample_elem['technical_replicates']['sample_name']]))

                                                    if sample_elem['sample_name'] not in old_filenames.keys():
                                                        old_filenames[sample_elem['sample_name']] = len(sample_elem['technical_replicates']['filenames']) if 'filenames' in sample_elem['technical_replicates'] else 0
                                                    if old_filenames[sample_elem['sample_name']] < filename_length:
                                                        do_files = True
                                                        if old_filenames[sample_elem['sample_name']] > 0:
                                                            file_techniques = set(list([x.split('__')[2] for x in sample_elem['technical_replicates']['filenames']]))
                                                    if do_samples or do_files:
                                                        b_name = sample_elem[
                                                            'sample_name']
                                                        filename = get_file_name(
                                                            b_name.removesuffix(
                                                                f'_{b_name.split("_")[-1]}'),
                                                            double)
                                                        for t_count in range(1,
                                                                             sample_elem[
                                                                                 'technical_replicates'][
                                                                                 'count'] + 1):
                                                            for m_count in range(
                                                                    1,
                                                                    sample_elem[
                                                                        'number_of_measurements'] + 1):
                                                                if abbrev_tech not in sample_techniques:
                                                                    sample_name = f'{project_id}_{setting_id}_{abbrev_tech}_{organism}_{b_name}_t{"{:02d}".format(t_count)}_m{"{:02d}".format(m_count)}'
                                                                    sample_names.append(
                                                                        sample_name)
                                                                if abbrev_tech not in file_techniques:
                                                                    filenames.append(
                                                                        f'{project_id}__{file_index}__{abbrev_tech}__{filename}__{local_count}')
                                                                    file_index += 1
                                                                    local_count += 1
                                                        if do_samples:
                                                            if 'sample_name' in sample_elem['technical_replicates']:
                                                                sample_elem['technical_replicates']['sample_name'] += sample_names
                                                            else:
                                                                sample_elem['technical_replicates']['sample_name'] = sample_names
                                                        if do_files:
                                                            if 'filenames' in sample_elem['technical_replicates']:
                                                                sample_elem['technical_replicates']['filenames'] += filenames
                                                            else:
                                                                sample_elem[
                                                                    'technical_replicates']['filenames'] = filenames

    return metafile


def get_file_name(sample_name, double):
    splitted_name = sample_name.split('-')
    new_name = []
    for elem in splitted_name:
        new_elem, gene = split_name(elem, double)
        if new_elem != '':
            new_name.append(new_elem)
    sample_name = '_'.join(new_name)
    return sample_name


def split_name(elem, double, gene=True):
    new_name = []
    if '+' in elem:
        new_split = elem.split('+')
        for part in new_split:
            new_part, gene = split_name(part, double, gene=gene)
            if new_part != '':
                new_name.append(new_part)
        elem = '-'.join(new_name)

    if '#' in elem:
        remove = elem.split('#')[0]
        elem, gene = split_name(elem[len(f'{remove}#'):], double, gene=gene)

    if '.' in elem:
        if elem.lower() in [f'gn.{x.lower()}' for x in double]:
            gene = False
            elem = ''
        elif elem.lower().startswith('embl.') and gene is True:
            elem = ''
        else:
            elem = elem.split('.')[1]

    return elem, gene


def print_desc(desc, format='plain', size=70):
    new_desc = ''
    if isinstance(desc, list):
        for elem in desc:
            if isinstance(elem, str):
                new_desc += elem
            else:
                if format == 'plain':
                    for i in range(len(elem)):
                        for j in range(len(elem[i])):
                            elem[i][j] = '\n'.join(['\n'.join(textwrap.wrap(line, size * 1/len(elem[i]) - 1, break_long_words=False, replace_whitespace=False)) for line in elem[i][j].splitlines() if line.strip() != ''])
                new_desc += tabulate(elem, tablefmt=format).replace('>\n<', '><')
    else:
        new_desc = desc
    return new_desc


