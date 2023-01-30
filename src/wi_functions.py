import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.wi_utils as wi_utils
import src.generate_metafile as generate
import src.find_metafiles as find_metafiles
import os
import copy
import pytz
from dateutil import parser
import multiprocessing
import git
import time

# This script contains all functions for generation of objects for the web
# interface
disabled_fields = []


def get_empty_wi_object():
    """
    This function parses the keys.yaml and returns an empty object for the web
    interface.
    :return: wi_object: object containing all information from the keys.yaml
    in a format readable by the web interface
    """
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists')):
        repo = git.Repo.clone_from('https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.git/', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists'))
    else:
        repo = git.Repo(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists'))
        o = repo.remotes.origin
        o.pull()

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    wi_object = {}
    for key in key_yaml:
        wi_object[key] = parse_empty(key_yaml[key], key, key_yaml, True)
    wi_object['all_factors'] = []
    return wi_object


def get_single_whitelist(ob):
    whitelist = utils.get_whitelist(ob['key_name'], {'organism': ob['organism']})
    if 'whitelist' in whitelist:
        return whitelist['whitelist']
    else:
        return None


def parse_empty(node, pos, key_yaml, get_whitelists):
    """
    This function parses a part of the key.yaml into an object readable by the
    web-interface
    :param node: a part of the key.yaml that should be parsed
    :param pos: the position of the node (chained keys)
    :param key_yaml: the whole key.yaml
    :param get_whitelists: bool, True if whitelists should be included,
    False if not
    :return: part_object: an object for the web interface parsed from node
    """
    input_disabled = True if pos.split(':')[-1] in ['condition_name',
                                                    'sample_name'] else False
    whitelist_type = None
    if isinstance(node['value'], dict) and not \
            set(['mandatory', 'list', 'desc', 'display_name', 'value']) <= \
            set(node['value'].keys()):
        input_fields = []

        if 'special_case' in node and 'merge' in node['special_case']:
            input_type = 'select'
            if get_whitelists:
                whitelist = utils.read_whitelist(pos.split(':')[-1])
                if 'whitelist_type' in whitelist \
                        and whitelist['whitelist_type'] == 'plain' \
                        and 'headers' not in whitelist:
                    whitelist = whitelist['whitelist']
                    whitelist_type = whitelist['whitelist_type']
                elif 'whitelist_type' in whitelist \
                        and whitelist['whitelist_type'] == 'depend':
                    whitelist = None
                    input_type = 'dependable'
                elif 'whitelist_type' in whitelist and whitelist[
                        'whitelist_type'] == 'group':
                    if isinstance(whitelist['whitelist'], dict):
                        new_w = []
                        for key in whitelist['whitelist']:
                            if key != 'whitelist_type':
                                new_w.append(
                                    {'title': key,
                                     'whitelist': whitelist['whitelist'][key]})
                        input_type = 'group_select'
                        whitelist = new_w
                        whitelist_type = whitelist['whitelist_type']
                    else:
                        whitelist = whitelist['whitelist']
                        input_type = 'select'
                        whitelist_type = 'plain_group'
            else:
                whitelist = None
            if whitelist and len(whitelist) > 30:
                if node['list']:
                    input_type = 'multi_autofill'
                else:
                    input_type = 'single_autofill'
                whitelist = None
            #if input_type != 'group_select':
            #    if isinstance(whitelist, dict):
            #        input_type = 'dependable'
            if pos.split(':')[-1] == 'organism':
                input_type = 'organism_name'
            part_object = {'position': pos, 'mandatory': node['mandatory'],
                           'list': node['list'],
                           'displayName': node['display_name'],
                           'desc': node['desc'], 'value': None,
                           'whitelist': whitelist,
                           'whitelist_type': whitelist_type,
                           'input_type': input_type,
                           'input_disabled': input_disabled}
        else:
            for key in node['value']:
                input_fields.append(parse_empty(node['value'][key],
                                                pos + ':' + key,
                                                key_yaml, get_whitelists))
            unit = False
            value = False
            unit_whitelist = []
            if len(input_fields) == 2:
                for i in range(len(input_fields)):
                    if input_fields[i]['position'].split(':')[-1] == 'unit':
                        unit = True
                        unit_whitelist = input_fields[i]['whitelist']
                    elif input_fields[i]['position'].split(':')[-1] == 'value':
                        value = True
            if unit and value:

                part_object = {'position': pos, 'mandatory': node['mandatory'],
                               'list': node['list'],
                               'displayName': node['display_name'],
                               'desc': node['desc'], 'value': None,
                               'value_unit': None, 'whitelist': unit_whitelist,
                               'input_type': 'value_unit',
                               'input_disabled': input_disabled}
            else:
                part_object = {'position': pos, 'mandatory': node['mandatory'],
                               'list': node['list'],
                               'title': node['display_name'],
                               'desc': node['desc'],
                               'input_fields': input_fields,
                               'input_disabled': input_disabled}
        if node['list']:
            part_object['list_value'] = []
    else:
        if pos.split(':')[-1] == 'organism':
            input_type = 'organism_name'
        else:
            input_type = node['input_type']
        if get_whitelists:
            if node['whitelist']:
                whitelist = utils.get_whitelist(pos.split(':')[-1], {})
                if 'whitelist_type' in whitelist \
                        and whitelist['whitelist_type'] == 'plain' \
                        and 'headers' not in whitelist:
                    whitelist = whitelist['whitelist']
                    whitelist_type = 'plain'
                elif 'whitelist_type' in whitelist and whitelist[
                        'whitelist_type'] == 'depend':
                    whitelist = None
                    input_type = 'dependable'
                elif 'whitelist_type' in whitelist and whitelist[
                        'whitelist_type'] == 'group':
                    if isinstance(whitelist['whitelist'], dict):
                        new_w = []
                        for key in whitelist['whitelist']:
                            if key != 'whitelist_type':
                                new_w.append(
                                    {'title': key,
                                     'whitelist': whitelist['whitelist'][key]})
                        input_type = 'group_select'
                        whitelist_type = 'group'
                        whitelist = new_w
                    else:
                        whitelist_type = 'plain_group'
                        whitelist = whitelist['whitelist']
            elif node['input_type'] == 'bool':
                whitelist = [True, False]
                input_type = 'select'
            else:
                whitelist = None
            if input_type != 'group_select':
                if isinstance(whitelist, dict):
                    input_type = 'dependable_select'
                elif whitelist and len(whitelist) > 30:
                    if node['list']:
                        input_type = 'multi_autofill'
                        whitelist = None
                    else:
                        input_type = 'single_autofill'
                        whitelist = None
        else:
            if node['whitelist']:
                whitelist = pos.split(':')[-1]
            else:
                whitelist = None
            if node['input_type'] == 'bool':
                input_type = 'bool'
                whitelist = pos.split(':')[-1]
        part_object = {'position': pos, 'mandatory': node['mandatory'],
                       'list': node['list'],
                       'displayName': node['display_name'],
                       'desc': node['desc'], 'value': node['value'],
                       'whitelist': whitelist,
                       'whitelist_type': whitelist_type,
                       'input_type': input_type,
                       'input_disabled': input_disabled}
        if node['list'] or node['input_type'] == 'single_autofill':
            part_object['list_value'] = []
        if node['input_type'] == 'single_autofill' or node['input_type'] == 'multi_autofill':
            part_object['search_info'] = {'organism': None, 'key_name': part_object['position'].split(':')[-1]}

    return part_object


def get_factors(organism):
    """
    This function returns all experimental factor with a whitelist of their
    values.
    :param organism: the organism that was selected by the user
    :return: factor_value: a dictionary containing factors and whitelists
    """
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    factor_value = {'factor': utils.read_whitelist('factor')['whitelist']}
    values = {}
    for factor in factor_value['factor']:
        whitelist, whitelist_type, input_type, headers, w_keys = \
            get_whitelist_with_type(factor, key_yaml, organism, None)
        values[factor] = {'whitelist': whitelist, 'input_type': input_type,
                          'whitelist_type': whitelist_type}
        if input_type == 'single_autofill' or input_type == 'multi_autofill':
            values[factor]['search_info']: {'organism': organism, 'key_name': factor}
        if headers is not None:
            values[factor]['headers'] = headers
        if w_keys is not None:
            values[factor]['whitelist_keys'] = w_keys
    factor_value['values'] = values
    return factor_value


def get_whitelist_with_type(key, key_yaml, organism, headers):
    """
    This function reads in a whitelist and returns it together with its type.
    :param key: the key containing a whitelist
    :param key_yaml: the read in keys.yaml
    :param organism: the selected organism
    :param headers: the headers that a whitelist may contain
    :return:
    whitelist: the read in whitelist
    whitelist_type: the whitelist type
    input_type: the type of the expected value
    headers: the headers that might occur in the whitelist
    """
    whitelist_type = None
    is_list = False
    whitelist_keys = None
    filled_object = {'organism': copy.deepcopy(organism)}
    organism = organism.split(' ')[0]
    input_type = list(utils.find_keys(key_yaml, key))
    if len(input_type) > 0:
        if input_type[0]['list']:
            is_list = True
        if isinstance(input_type[0]['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) \
                <= set(input_type[0]['value'].keys()):
            if len(input_type[0]['value'].keys()) == 2 and 'value' in \
                    input_type[0]['value'] and 'unit' in \
                    input_type[0]['value']:
                input_type = 'value_unit'
            elif 'special_case' in input_type[0] and 'merge' in \
                    input_type[0]['special_case']:
                input_type = 'select'
            else:
                val = []
                for k in input_type[0]['value']:
                    k_val = {}
                    k_val['whitelist'], k_val['whitelist_type'], \
                        k_val['input_type'], \
                        header, whitelist_keys = get_whitelist_with_type(
                        k, key_yaml, organism, headers)
                    if header is not None:
                        k_val['headers'] = header
                    if whitelist_keys is not None:
                        k_val['whitelist_keys'] = whitelist_keys
                    node = list(utils.find_keys(key_yaml, k))[0]
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None
                    k_val['displayName'] = node['display_name']
                    k_val['required'] = node['mandatory']
                    k_val['position'] = k
                    k_val['value'] = []
                    val.append(k_val)
                val.append({'displayName': 'Multi', 'position': 'multi',
                            'whitelist': [True, False], 'input_type': 'bool',
                            'value': False})
                input_type = 'nested'
                return val, whitelist_type, input_type, headers, whitelist_keys
        else:
            if input_type[0]['input_type'] == 'bool':
                input_type = 'bool'
            else:
                input_type = input_type[0]['input_type']
    else:
        input_type = 'short_text'

    if input_type == 'value_unit':
        whitelist = utils.read_whitelist('unit')
    elif input_type == 'select':
        whitelist = utils.read_whitelist(key)
    elif input_type == 'bool':
        whitelist = [True, False]
        input_type = 'select'
    else:
        whitelist = None

    if isinstance(whitelist, dict):
        if 'headers' in whitelist:
            headers = whitelist['headers']
        if whitelist['whitelist_type'] == 'group':
            whitelist = utils.read_grouped_whitelist(whitelist, filled_object)
            input_type = 'group_select'
            if 'headers' in whitelist:
                headers = whitelist['headers']
            if 'whitelist_keys' in whitelist:
                whitelist_keys = whitelist['whitelist_keys']
            if isinstance(whitelist['whitelist'], dict):
                new_w = []
                for value in whitelist['whitelist']:
                    if value not in ['headers', 'whitelist_keys']:
                        new_w.append({'title': value,
                                      'whitelist':
                                          whitelist['whitelist'][value]})
                whitelist = new_w
                whitelist_type = 'group'
            else:
                whitelist_type = 'plain_group'
                input_type = 'select'
        elif whitelist['whitelist_type'] == 'depend':
            whitelist = utils.read_depend_whitelist(whitelist['whitelist'],
                                                    organism)
            whitelist_type = 'depend'
            if 'headers' in whitelist:
                headers = whitelist['headers']
    if isinstance(whitelist, dict) and 'whitelist' in whitelist:
        whitelist = whitelist['whitelist']

    if whitelist and len(whitelist) > 30:
        input_type = 'multi_autofill'
        whitelist = None
    if is_list:
        node = list(utils.find_keys(key_yaml, key))[0]
        new_w = [
            {'whitelist': whitelist, 'position': key,
             'displayName': node['display_name'], 'required': True,
             'input_type': input_type, 'whitelist_type': whitelist_type},
            {'displayName': 'Multi', 'position': 'multi',
             'whitelist': [True, False], 'input_type': 'bool',
             'value': False}]
        whitelist = new_w
        whitelist_type = 'list_select'
        input_type = 'nested'
    return whitelist, whitelist_type, input_type, headers, whitelist_keys


def get_samples(condition, sample, real_val):
    """
    This function created a pre-filled object with the structure of the samples
    to be displayed in the web interface.
    :param condition: the condition the sample is created for
    :param sample: the empty structure of the sample
    :return: sample: the pre-filled sample
    """
    conds = generate.split_cond(condition)
    for i in range(len(sample)):
        if sample[i][
            'position'] == 'experimental_setting:conditions:biological_' \
                           'replicates:samples:sample_name':
            sample_name = generate.get_short_name(condition, {})
            sample[i]['value'] = sample_name \
                .replace(':', ': ') \
                .replace('|', '| ') \
                .replace('#', '# ') \
                .replace('-', ' - ') \
                .replace('+', ' + ')
            sample[i]['correct_value'] = sample_name
        for c in conds:
            if sample[i][
                'position'] == f'experimental_setting:conditions:biological_' \
                               f'replicates:samples:{c[0]}':
                if c[0] in ['age', 'time_point', 'treatment_duration']:
                    unit = c[1].lstrip('0123456789')
                    value = c[1][:len(c[1]) - len(unit)]
                    sample[i]['value'] = int(value)
                    sample[i]['value_unit'] = unit
                elif isinstance(c[1], dict):
                    val = f'{c[0]}:{"{"}'
                    for l in range(len(list(c[1].keys()))):
                        val = f'{val}{"|" if l > 0 else ""}{list(c[1].keys())[l]}:"{c[1][list(c[1].keys())[l]]}"'
                    val = f'{val}{"}"}'
                    if val in real_val:
                        sample[i]['value'] = real_val[val]
                    else:
                        if sample[i]['list']:
                            filled_sample = copy.deepcopy(sample[i]
                                                          ['input_fields'])
                            for j in range(len(filled_sample)):
                                for x in c[1]:
                                    if filled_sample[
                                        j]['position'].split(':')[-1] == x:
                                        if x in ['age', 'time_point',
                                                 'treatment_duration']:
                                            unit = c[1][x].lstrip('0123456789')
                                            value = c[1][x][:len(c[1][x]) -
                                                             len(unit)]
                                            filled_sample[j]['value'] = \
                                                int(value)
                                            filled_sample[j]['value_unit'] = \
                                                unit
                                        else:
                                            filled_sample[j]['value'] = c[1][x]
                                        filled_sample[j]['input_disabled'] = \
                                            True
                            sample[i]['list_value'].append(filled_sample)
                        else:
                            if 'input_fields' in sample[i]:
                                for j in range(len(sample[i]['input_fields'])):
                                    for x in c[1]:
                                        if sample[i]['input_fields'][j][
                                            'position'].split(':')[-1] == x:
                                            if x in ['age', 'time_point',
                                                     'treatment_duration']:
                                                unit = c[1][x].lstrip(
                                                    '0123456789')
                                                value = c[1][x][
                                                        :len(c[1][x]) - len(
                                                            unit)]
                                                sample[i]['input_fields'][j][
                                                    'value'] = int(value)
                                                sample[i]['input_fields'][j][
                                                    'value_unit'] = unit
                                            else:
                                                sample[i]['input_fields'][j][
                                                    'value'] = c[1][x]
                            else:
                                val = ""
                                for key in c[1]:
                                    val = f'{val}{" " if val != "" else ""}{c[1][key]}'
                                sample[i]['value'] = val
                else:
                    if sample[i]['list']:
                        if len(sample[i]['list_value']) > 0:
                            new_val = copy.deepcopy(sample[i]['input_fields']
                                                    [0])
                            new_val['value'] = c[1]
                            new_val['input_disabled'] = True
                            sample[i]['list_value'].append([new_val])
                        else:
                            new_samp = copy.deepcopy(sample[i])
                            new_samp.pop('list_value')
                            new_samp['list'] = False
                            new_samp[
                                'position'] = \
                                f'{new_samp["position"]}:' \
                                f'{new_samp["position"].split(":")[-1]}'
                            sample[i]['input_fields'] = [new_samp]
                            new_val = copy.deepcopy(new_samp)
                            new_val['value'] = c[1]
                            new_val['input_disabled'] = True
                            sample[i]['list_value'].append([new_val])
                            sample[i]['title'] = copy.deepcopy(
                                sample[i]['displayName'])
                            sample[i].pop('displayName')
                            sample[i].pop('value')
                            sample[i].pop('whitelist')
                            sample[i].pop('whitelist_type')
                            sample[i].pop('input_type')
                    else:
                        if c[1] in real_val:
                            sample[i]['value'] = real_val[c[1]]
                        else:
                            sample[i]['value'] = c[1]
                if 'input_type' in sample[i] and sample[i]['input_type'] == 'single_autofill':
                    sample[i]['list_value'] = [] if sample[i][
                                                        'value'] is None else [
                        sample[i]['value']]
                sample[i]['input_disabled'] = True
            elif not any(sample[i]['position'] ==
                         f'experimental_setting:conditions:'
                         f'biological_replicates:samples:{x[0]}'
                         for x in conds):
                if sample[i]['list'] and 'title' not in sample[i]:
                    new_samp = copy.deepcopy(sample[i])
                    new_samp.pop('list_value')
                    new_samp['list'] = False
                    new_samp['position'] = \
                        f'{new_samp["position"]}:' \
                        f'{new_samp["position"].split(":")[-1]}'
                    if new_samp['input_type'] == 'single_autofill':
                        new_samp['list_value'] = [] if new_samp['value'] is None else [new_samp['value']]
                    sample[i]['input_fields'] = [new_samp]
                    sample[i]['title'] = copy.deepcopy(
                        sample[i]['displayName'])
                    sample[i].pop('displayName')
                    sample[i].pop('value')
                    sample[i].pop('whitelist')
                    sample[i].pop('whitelist_type')
                    sample[i].pop('input_type')
    return sample


def get_conditions(factors, organism_name):
    """
    This function creates all combinations of selected experimental factors and
    their values.
    :param organism_name: the selected organism
    :param factors: multiple dictionaries containing the keys 'factor' and
    'values' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a list containing all combinations of conditions
    """
    organism = organism_name.split(' ')[0]
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    real_val = {}
    for i in range(len(factors)):
        if len(factors[i]['values']) == 1 and isinstance(
                factors[i]['values'][0], dict) and not (
                'value' in factors[i]['values'][0] and 'unit' in
                factors[i]['values'][0]):
            empty_key = []
            for k in factors[i]['values'][0]:
                if (isinstance(factors[i]['values'][0][k], list) and len(
                        factors[i]['values'][0][k]) == 0) or \
                        factors[i]['values'][0][k] is None:
                    empty_key.append(k)
            for key in empty_key:
                factors[i]['values'][0].pop(key)
            node = list(utils.find_keys(key_yaml, factors[i]['factor']))
            if len(node) > 0 and 'special_case' in node[0] and 'group' in \
                    node[0]['special_case']:
                ident_key = node[0]['special_case']['group']
            else:
                ident_key = None
            factors[i]['values'][0]['ident_key'] = ident_key
            if 'multi' in factors[i]['values'][0]:
                factor_info = list(utils.find_keys(
                    key_yaml, factors[i]['factor']))[0]
                if factor_info['list'] and isinstance(
                        factor_info['value'], dict) and not \
                        set(['mandatory', 'list', 'desc', 'display_name',
                             'value']) <= set(factor_info['value'].keys()):
                    if factors[i]['values'][0]['multi'] and ident_key is None:
                        factors[i]['values'][0]['multi'] = False
                    factors[i]['values'] = generate.get_combis(
                        factors[i]['values'][0], factors[i]['factor'],
                        factors[i]['values'][0]['multi'])
                else:
                    factors[i]['values'] = generate.get_combis(
                        factors[i]['values'][0][factors[i]['factor']],
                        factors[i]['factor'], factors[i]['values'][0]['multi'])

        if 'whitelist_keys' in factors[i]:
            for j in range(len(factors[i]['values'])):
                for k in factors[i]['whitelist_keys']:
                    if factors[i]['values'][j].endswith(f' ({k})'):
                        factors[i]['values'][j] = factors[i]['values'][j].replace(f' ({k})', '')
                        w_key = k
                        if 'headers' in factors[i] and w_key in factors[i]['headers']:
                            headers = factors[i]['headers'][w_key].split(' ')
                            vals = factors[i]['values'][j].split(' ')

                            # iterate through the headers and save the header and value of the
                            # same index into a dictionary with header as key
                            v = f'{factors[i]["factor"]}:{"{"}'
                            for l in range(len(headers)):
                                v = f'{v}{"|" if l > 0 else ""}{headers[l]}:"{vals[l]}"'
                            v = f'{v}{"}"}'

                            # overwrite the input value with the dictionary
                            real_val[v] = f'{factors[i]["values"][j]} ({w_key})'
                            factors[i]['values'][j] = v
                        else:
                            real_val[factors[i]['values'][j]] = f'{factors[i]["values"][j]} ({w_key})'
        else:
            if 'headers' in factors[i]:
                headers = factors[i]['headers'].split(' ')
                for j in range(len(factors[i]['values'])):
                    val = factors[i]['values'][j].split(' ')
                    v = f'{factors[i]["factor"]}:{"{"}'
                    for k in range(len(headers)):
                        v = f'{v}{"|" if k > 0 else ""}{headers[k]}:"{val[k]}"'
                    v = f'{v}{"}"}'
                    factors[i]['values'][j] = v
    conditions = generate.get_condition_combinations(factors)
    condition_object = []

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    sample = parse_empty(key_yaml['experimental_setting']['value']
                         ['conditions']['value']['biological_replicates']
                         ['value']['samples'],
                         'experimental_setting:conditions:biological_'
                         'replicates:samples', key_yaml, False)[
        'input_fields']
    whitelists = {}
    for item in sample:
        item, whitelists = get_whitelist_object(item, organism,
                                                whitelists)

    for cond in conditions:
        cond_sample = copy.deepcopy(sample)
        cond_sample = get_samples(cond, cond_sample, real_val)
        d = {'correct_value': cond,
             'title': cond.replace(':', ': ').replace('|',
                                                      '| ').replace(
                 '#', '# ').replace('-', ' - '),
             'position': 'experimental_setting:condition',
             'list': True, 'mandatory': True, 'list_value': [],
             'input_disabled': False, 'desc': '',
             'input_fields': copy.deepcopy(cond_sample)}
        condition_object.append(d)

    return {'conditions': condition_object, 'whitelist_object': whitelists,
            'organism': organism_name}


def get_whitelist_object(item, organism_name, whitelists):
    """
    This function creates a whitelist object containing the whitelists of all
    keys of  sample.
    :param item: a key containing a whitelist
    :param organism_name: the selected organism
    :param whitelists: a dictionary to save the whitelists to
    :return:
    item: the key containing the whitelist
    whitelists: the whitelist object
    """
    if 'input_type' in item:
        input_type = item['input_type']
        if input_type == 'select' or input_type == 'single_autofill' or input_type == 'multi_autofill' or input_type == 'dependable':
            whitelist = utils.get_whitelist(item['position'].split(':')[-1],
                                            {'organism': organism_name})
            if 'headers' in whitelist:
                item['headers'] = whitelist['headers']
            if 'whitelist_keys' in whitelist:
                item['whitelist_keys'] = whitelist['whitelist_keys']

            if whitelist['whitelist_type'] == 'group':
                input_type = 'group_select'
            if whitelist['whitelist_type'] == 'plain' or \
                    whitelist['whitelist_type'] == 'plain_group':
                whitelist = whitelist['whitelist']
        elif input_type == 'bool':
            whitelist = [True, False]
            input_type = 'select'
        elif input_type == 'value_unit':
            item['value_unit'] = None
            whitelist = utils.read_whitelist('unit')
            if 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'plain':
                whitelist = whitelist['whitelist']
        else:
            whitelist = None

        item['whitelist'] = item['position'].split(':')[-1] if whitelist is not None else None
        if whitelist and isinstance(whitelist, list) and len(whitelist) > 30:
            if item['list']:
                input_type = 'multi_autofill'
            else:
                input_type = 'single_autofill'
            item['search_info'] = {'organism': organism_name,
                                   'key_name': item['position'].split(':')[-1]}
            if not 'list_value' in item:
                item['list_value'] = []
        item['input_type'] = input_type
        if input_type == 'group_select':
            w = []
            for key in whitelist['whitelist']:
                w.append({'title': key,
                          'whitelist': whitelist['whitelist'][key]})
            whitelist = w
        if whitelist:
            whitelists[item['position'].split(':')[-1]] = whitelist
        if input_type == 'value_unit':
            whitelists['unit'] = whitelist
    elif 'input_fields' in item:
        for i in item['input_fields']:
            i, whitelists = get_whitelist_object(i, organism_name, whitelists)
    return item, whitelists


def parse_object(wi_object):
    """
    This function parses a wi object back into a yaml.
    :param wi_object: the filled wi object
    :return: result: a dictionary matching the metadata yaml structure
    """
    factors = copy.deepcopy(wi_object['all_factors'])
    wi_object.pop('all_factors')
    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    wi_object = new_object
    result = {}
    project_id = ''
    for elem in wi_object['project']['input_fields']:
        if elem['position'].split(':')[-1] == 'id':
            project_id = elem['value']
    for key in wi_object:
        result[key] = parse_part(wi_object[key], factors, '', project_id, 1)
    return result


def parse_part(wi_object, factors, organism, id, nom):
    """
    This function parses a part of the wi object to create the yaml structure.
    :param wi_object: a part of the filled wi object
    :param factors: the selested experimental factors
    :param organism: the slected organism
    :param id: the project id
    :param nom: the number of measurements
    :return: val: the parsed part in yaml structure
    """
    gn = None
    embl = None
    key_yaml = utils.read_in_yaml(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        'keys.yaml'))

    if isinstance(wi_object, dict):
        if wi_object['list']:
            val = []
            for i in range(len(wi_object['list_value'])):
                if isinstance(wi_object['list_value'][i], dict):
                    if wi_object['list_value'][i]['position'].split(':')[-1] == 'condition':

                        samples = []
                        for sub_elem in wi_object['list_value'][i]['list_value']:

                            samples.append(get_sample(sub_elem, id, organism))

                        val.append({'condition_name': wi_object['list_value'][i]['correct_value'],
                                    'biological_replicates':
                                        {'count': len(samples),
                                         'samples': samples}})

                    #else:
                    #    print(elem['position'])
                elif isinstance(wi_object['list_value'][i], list):
                    if wi_object['position'].split(':')[-1] == 'experimental_setting':
                        val.append(parse_list_part(wi_object['list_value'][i], factors[i], organism, id,
                                               nom))
                    else:
                        val.append(parse_list_part(wi_object['list_value'][i], factors, organism, id,
                                               nom))
                else:
                    val.append(wi_object['list_value'][i])
        else:
            if 'whitelist_keys' in wi_object:
                for k in wi_object['whitelist_keys']:
                    if wi_object['value'].endswith(f' ({k})'):
                        wi_object['value'] = wi_object['value'].replace(f' ({k})', '')
                    if 'headers' in wi_object and k in wi_object['headers']:
                        new_val = {}
                        for l in range(len(wi_object['headers'][k].split(' '))):
                            new_val[wi_object['headers'][k].split(' ')[l]] = wi_object['value'].split(' ')[l]
                        wi_object['value'] = new_val
                        break
            elif 'headers' in wi_object:
                new_val = {}
                for l in range(len(wi_object['headers'].split(' '))):
                    new_val[wi_object['headers'].split(' ')[l]] = wi_object['value'].split(' ')[l]
                wi_object['value'] = new_val

            if 'input_fields' in wi_object:
                val = parse_part(wi_object['input_fields'], factors, organism,
                                 id, nom)
            else:
                if wi_object['value'] and wi_object[
                        'input_type'] == 'value_unit':
                    unit = wi_object['value_unit']
                    value = wi_object['value']
                    val = {'unit': unit, 'value': value}
                elif wi_object['value'] and wi_object['input_type'] == 'date':
                    default_time = parser.parse(wi_object['value'])
                    timezone = pytz.timezone("Europe/Berlin")
                    local_time = default_time.astimezone(timezone)
                    val = local_time.strftime("%d.%m.%Y")
                else:
                    if 'correct_value' in wi_object:
                        if wi_object['position'].split(':')[-1] == \
                                'sample_name':
                            sample_count = \
                                int(wi_object['value'].split('_')[-1])
                            val = \
                                f'{wi_object["correct_value"]}_b' \
                                f'{"{:02d}".format(sample_count)}'
                        else:
                            val = wi_object['correct_value']
                    else:
                        val = wi_object['value']
    elif isinstance(wi_object, list):
        return parse_list_part(wi_object, factors, organism, id, nom)

    return val


def get_sample(sub_elem, id, organism):
    short_organism = utils.get_whitelist(os.path.join('abbrev', 'organism_name'),
                                         {'organism_name': organism})['whitelist']
    short_organism = short_organism[organism]

    sample = {}
    for elem in sub_elem:
        if elem['list']:
            res = []
            for el in elem['list_value']:
                r = get_sample(el, id, organism)
                if isinstance(r, dict) and len(r.keys()) == 1 and list(r.keys())[0] == elem['position'].split(':')[-1]:
                    r = r[elem['position'].split(':')[-1]]
                res.append(r)
            if len(res) > 0:
                sample[elem['position'].split(':')[-1]] = res
        else:
            if 'correct_value' in elem:
                sample_count = int(elem['value'].split('_')[-1])
                sample[elem['position'].split(':')[-1]] = f'{elem["correct_value"]}_b{"{:02d}".format(sample_count)}'
            elif 'value' in elem:
                if elem['value'] is not None:
                    if elem['input_type'] == 'value_unit':
                        unit = elem['value_unit']
                        value = elem['value']
                        val = {'unit': unit, 'value': value}
                    elif elem['input_type'] == 'date':
                        default_time = parser.parse(elem['value'])
                        timezone = pytz.timezone("Europe/Berlin")
                        local_time = default_time.astimezone(timezone)
                        val = local_time.strftime("%d.%m.%Y")
                    else:
                        if 'whitelist_keys' in elem:
                            for k in elem['whitelist_keys']:
                                if elem['value'].endswith(f' ({k})'):
                                    elem['value'] = elem[
                                        'value'].replace(f' ({k})', '')
                                    if 'headers' in elem and k in elem[
                                        'headers']:
                                        new_val = {}
                                        for l in range(len(
                                                elem['headers'][k].split(
                                                        ' '))):
                                            new_val[
                                                elem['headers'][k].split(' ')[
                                                    l]] = \
                                            elem['value'].split(' ')[l]
                                        elem['value'] = new_val
                                        break
                        elif 'headers' in elem:
                            new_val = {}
                            for l in range(
                                    len(elem['headers'].split(' '))):
                                new_val[elem['headers'].split(' ')[l]] = \
                                elem['value'].split(' ')[l]
                            elem['value'] = new_val
                        val = elem['value']
                    sample[elem['position'].split(':')[-1]] = val
            else:
                if elem['position'].split(':')[-1] == 'technical_replicates':
                    sample_name = []
                    count = [x['value'] for x in elem['input_fields'] if x['position'].split(':')[-1] == 'count'][0]
                    for c in range(count):
                        for m in range(sample['number_of_measurements']):
                            sample_name.append(f'{id}_{short_organism}_'
                                           f'{sample["sample_name"]}'
                                           f'_t{"{:02d}".format(c + 1)}_'
                                           f'm{"{:02d}".format(m + 1)}')
                    sample['technical_replicates'] = {'count': count,
                                                  'sample_name': sample_name}
                else:
                    res = get_sample(elem['input_fields'], id, organism)
                    if len(res) > 0:
                        sample[elem['position'].split(':')[-1]] = res
    return sample


def parse_list_part(wi_object, factors, organism, id, nom):
    """
    This function parses a part of the wi object of type list into the yaml
    structure.
    :param wi_object: the part of the wi object
    :param factors: the selected experimental factors
    :param organism: the selected organism
    :param id: the project id
    :param nom: the number of measurements
    :return: res: the parsed part in yaml structure
    """
    res = {}
    for i in range(len(wi_object)):
        if wi_object[i]['position'].split(':')[
                -1] == 'organism':
            organism = wi_object[i]['value'].split(' ')[0]
        val = parse_part(wi_object[i], factors, organism, id, nom)
        if wi_object[i]['position'].split(':')[-1] == 'technical_replicates':
            sample_name = []
            for c in range(val['count']):
                for m in range(nom):
                    sample_name.append(f'{id}_{organism}_'
                                       f'{res["sample_name"]}'
                                       f'_t{"{:02d}".format(c+1)}_'
                                       f'm{"{:02d}".format(m+1)}')
            val['sample_name'] = sample_name
        elif wi_object[i]['position'].split(':')[-1] == 'experimental_factors':
            for r in range(len(factors)):
                if 'whitelist_keys' in factors[r]:
                    w_keys = factors[r]['whitelist_keys']
                    factors[r].pop('whitelist_keys')
                    if 'headers' in factors[r]:
                        headers = factors[r]['headers']
                        factors[r].pop('headers')
                    else:
                        headers = None
                    for j in range(len(factors[r]['values'])):
                        for k in w_keys:
                            if factors[r]['values'][j].endswith(f' ({k})'):
                                factors[r]['values'][j] = factors[r]['values'][j].replace(f' ({k})', '')
                                if headers is not None and k in headers:
                                    new_val = {}
                                    for l in range(len(headers[k].split(' '))):
                                        new_val[headers[k].split(' ')[l]] = factors[r]['values'][j].split(' ')[l]
                                    factors[r]['values'][j] = new_val
                                break
                elif 'headers' in factors[r]:
                    headers = factors[r]['headers']
                    factors[r].pop('headers')
                    for j in range(len(factors[r]['values'])):
                        new_val = {}
                        for l in range(len(headers.split(' '))):
                            new_val[headers.split(' ')[l]] = factors[r]['values'][j].split(' ')[l]
                        factors[r]['values'][j] = new_val

            res[wi_object[i]['position'].split(':')[-1]] = factors

        if type(val) == bool or type(val) == int or (
                val is not None and len(val) > 0):
            res[wi_object[i]['position'].split(':')[-1]] = val
    return res


def validate_object(wi_object):
    """
    This function performs a validation over the wi object.
    :param wi_object: the filled wi object
    :return: validation_object: the validated wi object with errors and
                                warnings
    """
    pooled = None
    organisms = []
    for setting in wi_object['experimental_setting']['list_value']:
        for elem in setting:
            if elem['position'].split(':')[-1] == 'organism':
                organisms.append(elem['value'].split(' ')[0])
    warnings = {}
    errors = {}
    factors = copy.deepcopy(wi_object['all_factors'])
    wi_object.pop('all_factors')
    arguments = [(elem, wi_object[elem], [], pooled, organisms, []) for elem in
                 wi_object]
    pool_obj = multiprocessing.Pool()
    answer = pool_obj.starmap(wi_utils.validate_part, arguments)

    for elem in answer:
        wi_object[elem[0]] = elem[1]
        warnings[elem[0]] = elem[4]
        errors[elem[0]] = elem[5]

    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    wi_object = new_object
    wi_object['all_factors'] = copy.deepcopy(factors)
    validation_object = {'object': wi_object, 'errors': errors,
                         'warnings': warnings}
    return validation_object


def get_summary(wi_object):
    """
    This function parses the wi object into a yaml structure and then parses
    the yaml to HTML to be output in the web interface. It also returns a list
    of filenames.
    :param wi_object: the filled wi object
    :return: a dictionary containing the yaml structure as a dictionary and as
             HTML as well as the filenames as a string and in HTML
    """
    factors = copy.deepcopy(wi_object['all_factors'])
    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    new_object['all_factors'] = factors
    yaml_object = parse_object(new_object)
    if 'project' in yaml_object and 'id' in yaml_object['project']:
        project_id = yaml_object['project']['id']
    else:
        project_id = None
    filename_nested = list(
        utils.find_list_key(yaml_object, 'technical_replicates:sample_name'))
    html_filenames, filenames = get_html_filenames(filename_nested)
    html_str = ''
    for elem in yaml_object:
        end = f'{"<hr><br>" if elem != list(yaml_object.keys())[-1] else ""}'
        html_str = f'{html_str}<h3>{elem}</h3>' \
                   f'{object_to_html(yaml_object[elem], 0, 0, False)}' \
                   f'<br>{end}'
    return {'yaml': yaml_object, 'summary': html_str,
            'file_names': html_filenames, 'file_string': (
                project_id,
                '\n'.join(filenames)) if project_id is not None else None}


def get_html_filenames(filename_nest):
    """
    This function parses the filenames into HTML.
    :param filename_nest: a nested list of filenames
    :return:
    html_filenames: the file names in HTML format
    filenames: the filenames as a string
    """
    filenames = []
    html_filenames = ''
    for file_list in filename_nest:
        part_html = ''
        for filename in file_list:
            part_html = f'{part_html}- {filename}<br>'
            filenames.append(filename)
        end = f'{"<br><hr><br>" if file_list != filename_nest[-1] else "<br>"}'
        html_filenames = f'{html_filenames}{part_html}{end}'
    return html_filenames, filenames


def object_to_html(yaml_object, depth, margin, is_list):
    """
    This function parses the yaml structure into HTML.
    :param yaml_object: a dictionary containing the yaml format
    :param depth: the depth of the indentation
    :param margin: the margin for the indentation
    :param is_list: a boolean to state if a key contains a list
    :return: html_str: the yaml structure in HTML
    """
    html_str = ''
    if isinstance(yaml_object, dict):
        for key in yaml_object:
            if key == list(yaml_object.keys())[0] and is_list:
                input_text = object_to_html(yaml_object[key],
                                            depth + 1, margin + 1.5, is_list)
                html_str = f'{html_str}<ul style="list-style-type: circle;">' \
                           f'<li><p><font color={get_color(depth)}>{key}' \
                           f'</font>: {input_text}</p></li></ul>'
            else:
                input_text = object_to_html(yaml_object[key],
                                            depth + 1, margin + 1.5, is_list)
                html_str = f'{html_str}<ul style="list-style: none;"><li><p>' \
                           f'<font color={get_color(depth)}>{key}</font>: ' \
                           f'{input_text}</p></li></ul>'
    elif isinstance(yaml_object, list):
        for elem in yaml_object:
            if not isinstance(elem, list) and not isinstance(elem, dict):
                html_str = f'{html_str}<ul style="list-style-type: circle;">' \
                           f'<li><p>{elem}</p></li></ul>'
            else:
                html_str = f'{html_str}' \
                           f'{object_to_html(elem, depth, margin, True)}'
    else:
        html_str = f'{html_str}{yaml_object}'
    return html_str


def get_color(depth):
    """
    This function returns a color for the key in the HTML format depending on
    its indentation.
    :param depth: the depth of indentation
    :return: color: the color in which the key should be colored
    """
    if depth < 1:
        color = '26a69a'
    elif depth < 2:
        color = '#d95965'
    elif depth < 3:
        color = '2fccbd'
    else:
        color = 'fc6875'
    return color


def save_object(dictionary, path, filename):
    """
    This function saves the yaml structure into a file
    :param dictionary: the parsed wi object in yaml format
    :param path: the path to save the file to
    :param filename: the name of the file
    :return: new_filename: the name under which the file was saved
    """
    metafiles = find_metafiles.find_projects(path,
                                         f'id:"{dictionary["project"]["id"]}"',
                                         False)
    if len(metafiles) > 0:
        for elem in metafiles:
            for key in elem:
                if key == dictionary['project']['id']:
                    path = elem[key]
        new_filename = path
        utils.save_as_yaml(dictionary, path)
    else:
        new_filename = f'{filename}_{dictionary["project"]["id"]}' \
                       f'_metadata.yaml'
        utils.save_as_yaml(dictionary, os.path.join(path, new_filename))
        new_filename = os.path.join(path, new_filename)
    return new_filename


def save_filenames(file_str, path):
    """
    This function saves the generated filenames into a file.
    :param file_str: the filenames to be saved
    :param path: the path to save the file to
    :return: filename: the name under which the generated filenames are saved
    """
    if file_str is not None:
        filename = f'{file_str[0]}_samples.txt'
        text_file = open(os.path.join(path, filename), "w")
        text_file.write(file_str[1])
        text_file.close()
    else:
        filename = None
    return filename


def get_meta_info(path, project_id):
    """
    This file creates an HTML summary for a project containing metadata.
    :param path: the path of a folder to be searched for a project
    :param project_id: the id of the project
    :return: html_str: the summary in HTML
    """
    # If file must be searched

    yaml = find_metafiles.find_projects(path, f'id:{project_id}', True)
    if len(yaml) == 0:
        return f'No metadata found.'
    else:
        count = 0
        for elem in yaml:
            for key in elem:
                if key == project_id:
                    yaml = elem[key]
                    count += 1
        if count > 1:
            return f'Error: Multiple metadata files found.'
        else:
            if 'path' in yaml:
                yaml.pop('path')
            html_str = ''
            for elem in yaml:
                end = f'{"<hr><br>" if elem != list(yaml.keys())[-1] else ""}'
                html_str = f'{html_str}<h3>{elem}</h3>' \
                           f'{object_to_html(yaml[elem], 0, 0, False)}<br>' \
                           f'{end}'
            return html_str


def get_search_mask():
    """
    This functions returns all necessary information for the search mask.
    :return: a dictionary containing all keys of the metadata structure and a
             whitelist object
    """
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists')):
        git.Repo.clone_from('https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.git/', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists'))
    else:
        repo = git.Repo(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'metadata_whitelists'))
        o = repo.remotes.origin
        o.pull()

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    keys = [
        {'key_name': 'All keys', 'display_name': 'All Fields', 'nested': [],
         'whitelist': False, 'chained_keys': ''}]
    keys += get_search_keys(key_yaml, '')
    whitelist_object = get_gene_whitelist()
    return {'keys': keys, 'whitelist_object': whitelist_object}


def find_metadata(path, search_string):
    """
    This function searches for metadata files that match a search string in a
    given directory.
    :param path: the path that should be searched
    :param search_string: the search string
    :return: new_files: a list containing all matching files
    """
    files = find_metafiles.find_projects(path, search_string, True)
    new_files = []
    for i in range(len(files)):
        for key in files[i]:
            res = {'id': key,
                   'path': files[i][key]['path'],
                   'project_name': files[i][key]['project']['project_name'],
                   'owner': files[i][key]['project']['owner']['name'],
                   'email': files[i][key]['project']['owner']['email'],
                   'organisms': list(
                       utils.find_keys(files[i][key], 'organism_name')),
                   'description': files[i][key]['project']['description'],
                   'date': files[i][key]['project']['date']}
            if 'nerd' in files[i][key]['project']:
                nerds = []
                for nerd in files[i][key]['project']['nerd']:
                    nerds.append(nerd['name'])
                res['nerd'] = nerds
            else:
                res['nerd'] = None
            new_files.append(res)
    return new_files


def get_gene_whitelist():
    """
    This function reads in the gene whitelist for all organisms.
    :return: a dictionary containing the gene names and ensembl ids
    """
    whitelist = utils.read_whitelist('gene')['whitelist']
    paths = [whitelist[k] for k in whitelist]

    pool_obj = multiprocessing.Pool()
    answer = pool_obj.map(wi_utils.read_gene_whitelist, paths)
    gene_name = []
    ensembl_id = []
    for elem in answer:
        gene_name += list(set(elem[0]))
        ensembl_id += list(set(elem[1]))
    gene_name = list(set(gene_name))
    ensembl_id = list(set(ensembl_id))
    return {'gene_name': gene_name, 'ensembl_id': ensembl_id}


def get_search_keys(key_yaml, chained):
    """
    This function returns all keys of the metadata structure in a nested way.
    :param key_yaml: the read in keys.yaml
    :param chained: the position of the key
    :return: res: a dictionary containing all metadata keys
    """
    res = []
    for key in key_yaml:
        d = {'key_name': key,
             'display_name': list(utils.find_keys(
                 key_yaml, key))[0]['display_name']}
        if isinstance(key_yaml[key]['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) \
                <= set(key_yaml[key]['value'].keys()):
            d['nested'] = get_search_keys(key_yaml[key]['value'],
                                          f'{chained}{key}:'
                                          if chained != '' else f'{key}:')
        else:
            d['chained_keys'] = f'{chained}{key}:' \
                if chained != '' else f'{key}:'
            d['nested'] = []
        if key == 'gene_name' or key == 'ensembl_id':
            d['whitelist'] = True
        else:
            d['whitelist'] = False
        res.append(d)
    return res


def edit_wi_object(path, project_id):
    """
    This function fills an empty wi object with the information of a metadata
    file.
    :param path: the path containing the metadata file
    :param project_id: the id of the project
    :return: wi_object: the filled wi object
    """
    meta_yaml = find_metafiles.find_projects(path, project_id, True)
    if len(meta_yaml) > 0:
        for elem in meta_yaml:
            for key in elem:
                if key == project_id:
                    meta_yaml = elem[key]
        if 'path' in meta_yaml:
            meta_yaml.pop('path')
        empty_object = get_empty_wi_object()
        wi_object = {}
        for part in empty_object:
            if part == 'all_factors':
                wi_object[part] = get_all_factors(meta_yaml)
            else:
                wi_object[part] = fill_wi_object(empty_object[part],
                                                 meta_yaml[part])
    else:
        wi_object = get_empty_wi_object()

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    sample = parse_empty(
        key_yaml['experimental_setting']['value']['conditions']['value']
        ['biological_replicates']['value']['samples'],
        'experimental_setting:conditions:biological_'
        'replicates:samples', key_yaml, False)[
        'input_fields']
    whitelist_object = {}
    for experimental_setting in wi_object['experimental_setting'][
            'list_value']:
        organism = ''
        for elem in experimental_setting:
            if elem['position'].split(':')[-1] == 'organism':
                organism = elem['value']
                break
        whitelists = {}
        for item in sample:
            item, whitelists = get_whitelist_object(item,
                                                    organism.split(' ')[0],
                                                    whitelists)
        whitelist_object[organism] = whitelists
    wi_object['whitelists'] = whitelist_object
    return wi_object


def get_all_factors(meta_yaml):
    """
    This function creates an object containing all experimental factors from a
    metadata yaml to be stored in a wi object.
    :param meta_yaml: the read in metadata file
    :return: all_factors: an object containing all experimental factors
    """
    all_factors = []
    for setting in meta_yaml['experimental_setting']:
        setting_factors = []
        for factors in setting['experimental_factors']:
            setting_fac = {'factor': factors['factor']}
            if factors['factor'] == 'gene':
                header = ''
                value = []
                for elem in factors['values']:
                    val = ''
                    for key in elem:
                        header = f'{header}{" " if header != "" else ""}{key}'
                        val = f'{val}{" " if val != "" else ""}{elem[key]}'
                    value.append(val)
                setting_fac['headers'] = header
            else:
                value = factors['values']
            setting_fac['values'] = value
            setting_factors.append(setting_fac)
        all_factors.append(setting_factors)
    return all_factors


def fill_wi_object(wi_object, meta_yaml):
    """
    This function fills an empty wi object with the information of a metadata
    file.
    :param wi_object: the empty wi object
    :param meta_yaml: the metadata file
    :return: wi_object: the filled wi object
    """
    if 'list' in wi_object and wi_object['list']:
        if 'input_fields' in wi_object:
            if wi_object['position'].split(':')[-1] == 'experimental_factors':
                pass
            else:
                for elem in meta_yaml:
                    list_value = []
                    for field in wi_object['input_fields']:
                        if field['position'].split(':')[-1] in elem:
                            list_value.append(
                                fill_wi_object(copy.deepcopy(field), elem[
                                    field['position'].split(':')[-1]]))

                        else:
                            if field['position'].split(':')[
                                    -2] == 'samples':
                                if 'input_fields' in field:
                                    for part in field['input_fields']:
                                        if 'whitelist' in part and part[
                                                'whitelist'] is not None:
                                            if part[
                                                'input_type'] == \
                                                    'value_unit':
                                                part['whitelist'] = 'unit'
                                            else:
                                                part['whitelist'] = \
                                                    part['position'].split(
                                                        ':')[-1]
                                else:
                                    if 'whitelist' in field and field[
                                            'whitelist'] is not None:
                                        if field['input_type'] == 'value_unit':
                                            field['whitelist'] = 'unit'
                                        else:
                                            field['whitelist'] = \
                                                field['position'].split(':')[
                                                    -1]
                            list_value.append(copy.deepcopy(field))
                    wi_object['list_value'].append(list_value)
                if wi_object['position'].split(':')[
                        -1] == 'experimental_setting':
                    for part in wi_object['list_value']:
                        conditions = []
                        for elem in part[2]['list_value']:
                            input_fields = copy.deepcopy(
                                elem[1]['input_fields'][1]['list_value'][0])
                            for i in range(len(input_fields)):
                                if input_fields[i]['position'].split(':')[
                                        -1] == 'sample_name':
                                    input_fields[i]['value'] = \
                                        input_fields[i]['value'].split('_')[0]
                            conditions.append(
                                {'position': 'experimental_setting:condition',
                                 'correct_value': f'{elem[0]["value"]}',
                                 'title': elem[0][
                                     'value'].replace(
                                     ':', ': ').replace(
                                     '|', '| ').replace(
                                     '#', '# ').replace(
                                     '-', ' - '),
                                 'desc': "", 'mandatory': True,
                                 'input_disabled': False, 'list': True,
                                 'input_fields': input_fields,
                                 'list_value': elem[1]['input_fields'][1][
                                     'list_value']})
                        part[2]['list_value'] = conditions

        else:
            if wi_object['position'].endswith(
                    'technical_replicates:sample_name'):
                wi_object['list_value'] = []
            else:
                for elem in meta_yaml:
                    wi_object['list_value'].append(elem)
    else:
        if 'input_fields' in wi_object:
            filled_fields = []
            for elem in wi_object['input_fields']:
                if elem['position'].split(':')[-1] in meta_yaml:
                    filled_fields.append(fill_wi_object(elem, meta_yaml[
                        elem['position'].split(':')[-1]]))
                else:
                    filled_fields.append(elem)
        else:
            if isinstance(meta_yaml, dict):
                val = ''
                for key in meta_yaml:
                    val = f'{val}{" " if val != "" else ""}{meta_yaml[key]}'
            else:
                if wi_object['position'].split(':')[-1] == 'date':
                    local_time = parser.parse(meta_yaml, dayfirst=True)
                    default_time = local_time.astimezone(pytz.utc)
                    val = default_time.strftime("%Y-%m-%dT%X.%fZ")
                else:
                    val = meta_yaml
            wi_object['value'] = val
            if wi_object['position'].split(':')[-1] == 'condition_name':
                global disabled_fields
                disabled_fields = [x[0] for x in
                                   generate.split_cond(wi_object['value'])]
            if wi_object['position'].split(':')[-1] == 'sample_name':
                sample_count = wi_object['value'].split('_')[-1]
                int_count = int(sample_count.replace('b', ''))
                value = f'{wi_object["value"].replace("_" + sample_count, "")}'
                wi_object['correct_value'] = copy.deepcopy(value)
                wi_value = value.replace(":", ": ")\
                    .replace("|", "| ").replace("#", "# ").replace("-", " - ")\
                    .replace("+", " + ")
                wi_object[
                    'value'] = f'{wi_value}_{int_count}'
            if wi_object['position'].split(':')[-2] == 'samples':
                if 'whitelist' in wi_object and wi_object[
                        'whitelist'] is not None:
                    wi_object['whitelist'] = wi_object['position'].split(':')[
                        -1]
            if wi_object['position'].split(':')[-1] in disabled_fields or \
                    wi_object['position'].split(':')[-1] in ['sample_name',
                                                             'condition_name',
                                                             'id',
                                                             'project_name']:
                wi_object['input_disabled'] = True
            else:
                wi_object['input_disabled'] = False
    return wi_object
