import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.generate as generate
import os


# This script contains all functions for generation of objects for the web
# interface


def get_empty_wi_object():
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    result = {}
    for key in key_yaml:
        result[key] = parse_empty(key_yaml[key], key, None, key_yaml)
    return result


def parse_empty(node, pre, organism_name, key_yaml):
    input_disabled = True if pre.split(':')[-1] in ['id', 'project_name',
                                                    'condition_name',
                                                    'sample_name'] else False
    if isinstance(node[4], dict):
        input_fields = []
        for key in node[4]:
            input_fields.append(parse_empty(node[4][key], pre + ':' + key,
                                            organism_name, key_yaml))
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
        if node[5]:
            whitelist, depend = utils.read_whitelist(pre.split(':')[-1])
            if depend:
                new_white = dependable(whitelist, key_yaml)
                if organism_name and organism_name in new_white:
                    print(new_white[organism_name])
                    new_white = new_white[organism_name]['whitelist']
                whitelist = new_white
        elif node[7] == 'bool':
            whitelist = [True, False]
        else:
            whitelist = None
        input_type = 'dependable_select' if isinstance(whitelist, dict) else \
            node[6]
        res = {'position': pre,
               'mandatory': True if node[0] == 'mandatory' else False,
               'list': node[1], 'displayName': node[2], 'desc': node[3],
               'value': node[4],
               'whitelist': sorted(whitelist) if isinstance(whitelist,
                                                            list) else
               whitelist,
               'input_type': input_type, 'data_type': node[7],
               'input_disabled': input_disabled}
        if node[1]:
            res['list_value'] = []
    return res


def dependable(whitelist, key_yaml):
    new_white = {'ident_key': whitelist['ident_key']}
    possible_input, depend = utils.read_whitelist(
        whitelist['ident_key'])
    for key in possible_input:
        input_type = 'select'
        if key in whitelist:
            new_white[key] = {
                'whitelist': sorted(whitelist[key]) if isinstance(
                    whitelist[key], list) else whitelist[key],
                'input_type': input_type}
        else:
            input_type = list(utils.find_keys(key_yaml, key))
            if len(input_type) > 0:
                if isinstance(input_type[0][4], dict) and len(
                        input_type[0][4].keys()) == 2 and 'value' in \
                        input_type[0][4] and 'unit' in input_type[0][4]:
                    input_type = 'value_unit'
                else:
                    input_type = input_type[0][6]
            else:
                input_type = 'short_text'
            if input_type == 'value_unit':
                w, d = utils.read_whitelist('unit')
            else:
                w, d = utils.read_whitelist(key)
            if d:
                w = dependable(w, key_yaml)
                input_type = 'dependable_select'
            new_white[key] = {'whitelist': w, 'input_type': input_type}
    return new_white


def get_samples(condition, organism_name):
    conds = generate.split_cond(condition)
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    samples = parse_empty(key_yaml['experimental_setting'][4]['conditions'][4]
                          ['biological_replicates'][4]['samples'],
                          'experimental_setting:conditions:biological_'
                          'replicates:samples', organism_name, key_yaml)[
        'input_fields']
    for i in range(len(samples)):
        if samples[i][
            'position'] == 'experimental_setting:conditions:biological_' \
                           'replicates:samples:sample_name':
            samples[i]['value'] = condition
        for c in conds:
            if samples[i][
                'position'] == f'experimental_setting:conditions:biological_' \
                               f'replicates:samples:{c[0]}':
                samples[i]['value'] = c[1]
                samples[i]['input_disabled'] = True
    return samples


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
    for cond in conditions:
        sample = get_samples(cond, organism_name)
        d = {'title': cond, 'position': 'experimental_setting:condition',
             'list': True, 'mandatory': True, 'list_value': [],
             'input_disabled': False, 'input_fields': sample}
        condition_object.append(d)
    return condition_object
