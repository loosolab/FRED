import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.generate as generate
import os
import copy

# This script contains all functions for generation of objects for the web
# interface


def get_empty_wi_object():
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    result = {}
    for key in key_yaml:
        result[key] = parse_empty(key_yaml[key], key, key_yaml, True)
    return result


def parse_empty(node, pre, key_yaml, get_whitelists):
    input_disabled = True if pre.split(':')[-1] in ['id', 'project_name',
                                                    'condition_name',
                                                    'sample_name'] else False
    if isinstance(node[4], dict):
        input_fields = []
        for key in node[4]:
            input_fields.append(parse_empty(node[4][key], pre + ':' + key,
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

            res = {'position': pre,
                   'mandatory': True if node[0] == 'mandatory' else False,
                   'list': node[1], 'displayName': node[2], 'desc': node[3],
                   'value': None, 'value_unit': None,
                   'whitelist': unit_whitelist, 'input_type': 'value_unit',
                   'input_disabled': input_disabled}
        else:
            res = {'position': pre,
                   'mandatory': True if node[0] == 'mandatory' else False,
                   'list': node[1], 'title': node[2], 'desc': node[3],
                   'input_fields': input_fields,
                   'input_disabled': input_disabled}
        if node[1]:
            res['list_value'] = []
    else:
        input_type = node[6]
        if get_whitelists:
            if node[5]:
                whitelist = utils.read_whitelist(pre.split(':')[-1])
                if 'whitelist_type' in whitelist and whitelist['whitelist_type'] == 'depend':
                    whitelist = None
                    input_type = 'dependable'
                elif 'whitelist_type' in whitelist and whitelist['whitelist_type'] == 'group':
                    new_w = []
                    for key in whitelist:
                        if key != 'whitelist_type':
                            new_w.append({'title': key, 'whitelist': whitelist[key]})
                    input_type = 'group_select'
                    whitelist = new_w
            elif node[7] == 'bool':
                whitelist = [True, False]
                input_type = 'select'
            else:
                whitelist = None
            if input_type != 'group_select':
                if isinstance(whitelist, dict):
                    input_type = 'dependable_select'
                #elif whitelist and len(whitelist) > 30:
                #    input_type = 'searchable_select'
        else:
            if node[5]:
                whitelist = pre.split(':')[-1]
            else:
                whitelist = None
            if node[7] == 'bool':
                input_type = 'bool'
                whitelist = pre.split(':')[-1]
        res = {'position': pre,
               'mandatory': True if node[0] == 'mandatory' else False,
               'list': node[1], 'displayName': node[2], 'desc': node[3],
               'value': node[4],
               'whitelist': whitelist,
               'input_type': input_type, 'data_type': node[7],
               'input_disabled': input_disabled}
        if node[1]:
            res['list_value'] = []
    return res


def get_factors(organism):
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    factor_value= {'factor': utils.read_whitelist('factor')}
    values = {}
    for factor in factor_value['factor']:
        whitelist, input_type = get_whitelist_with_type(factor, key_yaml, organism)
        values[factor] = {'whitelist': whitelist, 'input_type': input_type}
    factor_value['values'] = values
    return factor_value


def get_whitelist_with_type(key, key_yaml, organism):
    input_type = list(utils.find_keys(key_yaml, key))
    if len(input_type) > 0:
        if isinstance(input_type[0][4], dict) and len(
                input_type[0][4].keys()) == 2 and 'value' in \
                input_type[0][4] and 'unit' in input_type[0][4]:
            input_type = 'value_unit'
        elif input_type[0][7] == 'bool':
            input_type = 'bool'
        else:
            input_type = input_type[0][6]
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
        if whitelist['whitelist_type'] == 'group':
            whitelist = utils.read_grouped_whitelist(whitelist)
            new_w = []
            for value in whitelist:
                new_w.append({'title': value, 'whitelist': whitelist[value]})
            whitelist = new_w
            input_type = 'group_select'
        elif whitelist['whitelist_type'] == 'depend':
            whitelist = utils.read_depend_whitelist(whitelist, organism)
    # if whitelist and len(whitelist) > 30:
    #    input_type = 'searchable_select'
    if key == 'gene':
        input_type = 'unique'
    return whitelist, input_type


def get_samples(condition, sample):
    conds = generate.split_cond(condition)
    for i in range(len(sample)):
        if sample[i][
            'position'] == 'experimental_setting:conditions:biological_' \
                           'replicates:samples:sample_name':
            sample[i]['value'] = condition
        for c in conds:
            if sample[i][
                'position'] == f'experimental_setting:conditions:biological_' \
                               f'replicates:samples:{c[0]}':
                sample[i]['value'] = c[1]
                sample[i]['input_disabled'] = True
    return sample


def get_conditions(factors, organism_name):
    """
    This functions returns all possible combinations for experimental factors
    and their values.
    :param factors: multiple dictionaries containing the keys 'factor' and
    'value' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a list containing all combinations of conditions
    """
    conditions = generate.get_condition_combinations(factors)
    condition_object = []

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    sample = parse_empty(key_yaml['experimental_setting'][4]['conditions'][4]
                          ['biological_replicates'][4]['samples'],
                          'experimental_setting:conditions:biological_'
                          'replicates:samples', key_yaml, False)[
    'input_fields']
    whitelists = {}
    for item in sample:
        item, whitelists = get_whitelist_object(item, organism_name, whitelists)

    for cond in conditions:
        cond_sample = copy.deepcopy(sample)
        cond_sample = get_samples(cond, cond_sample)
        d = {'title': cond, 'position': 'experimental_setting:condition',
             'list': True, 'mandatory': True, 'list_value': [],
             'input_disabled': False, 'input_fields': copy.deepcopy(cond_sample)}
        condition_object.append(d)

    return {'conditions': condition_object, 'whitelist_object': whitelists}


def get_whitelist_object(item, organism_name, whitelists):
    if 'input_type' in item:
        input_type = item['input_type']
        if input_type == 'select':
            whitelist = utils.get_whitelist(item['position'].split(':')[-1],
                                            {'organism': organism_name})
            if isinstance(whitelist, dict):
                input_type = 'group_select'
        elif input_type == 'bool':
            whitelist = [True, False]
            input_type = 'select'
        elif input_type == 'value_unit':
            whitelist = utils.read_whitelist('unit')
        else:
            whitelist = None
        if item['position'].split(':')[-1] == 'gene':
            input_type = 'unique'
        item['input_type'] = input_type
        if input_type == 'group_select':
            w = []
            for key in whitelist:
                w.append({'title': key, 'whitelist': whitelist[key]})
            whitelist = w
        if whitelist:
            whitelists[item['position'].split(':')[-1]] = whitelist

    elif 'input_fields' in item:
        for i in item['input_fields']:
            i, whitelists = get_whitelist_object(i, organism_name, whitelists)
    return item, whitelists