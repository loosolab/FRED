import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.generate as generate


# This script contains all functions for generation of objects for the web
# interface


def get_empty_wi_object():
    key_yaml = utils.read_in_yaml('keys.yaml')
    result = []
    for key in key_yaml:
        result.append(parse_empty(key_yaml[key], key))
    return result


def parse_empty(node, pre):
    editable = True if pre.split(':')[-1] not in ['id', 'project_name',
                                                  'condition_name',
                                                  'sample_name'] else False
    if isinstance(node[4], dict):
        input_fields = []
        for key in node[4]:
            input_fields.append(parse_empty(node[4][key], pre + ':' + key))
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
                   'value':None, 'value_unit': None,
                   'whitelist': unit_whitelist, 'input_type': 'value_unit',
                   'editable': editable}
        else:
            res = {'position': pre,
                   'mandatory': True if node[0] == 'mandatory' else False,
                   'list': node[1], 'title': node[2], 'desc': node[3],
                   'input_fields': input_fields, 'editable': editable}
        if node[1]:
            res['list_value'] = []
    else:
        if node[5]:
            whitelist, depend = utils.read_whitelist(pre.split(':')[-1])
            if depend:
                new_white = {}
                possible_input, depend = utils.read_whitelist(
                    whitelist['ident_key'])
                for key in possible_input:
                    if key in whitelist:
                        new_white[key] = whitelist[key]
                    else:
                        w, d = utils.read_whitelist(key)
                        new_white[key] = w
                whitelist = new_white
        else:
            whitelist = None
        res = {'position': pre,
               'mandatory': True if node[0] == 'mandatory' else False,
               'list': node[1], 'displayName': node[2], 'desc': node[3],
               'value': node[4], 'whitelist': whitelist, 'input_type': node[6],
               'data_type': node[7], 'editable': editable}
        if node[1]:
            res['list_value'] = []
    return res


def get_samples(condition):
    conds = condition.split('-')
    key_yaml = utils.read_in_yaml('keys.yaml')
    samples = parse_empty(key_yaml['experimental_setting'][4]['conditions'][4]
                          ['biological_replicates'][4]['samples'],
                          'experimental_setting:conditions:biological_'
                          'replicates:samples')['input_fields']
    for i in range(len(samples)):
        if samples[i][
            'position'] == 'experimental_setting:conditions:biological_replicates:samples:sample_name':
            samples[i]['value'] = condition
        for c in conds:
            if samples[i][
                'position'] == f'experimental_setting:conditions:biological_replicates:samples:{c.split(":")[0]}':
                samples[i]['value'] = c.split(":")[1]
                samples[i]['editable'] = False
    return samples


def get_conditions(factors):
    """
    This functions returns all possible combinations for experimental factors
    and their values.
    :param factors: multiple dictionaries containing the keys 'factor' and
    'value' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'value': ['male', 'female']},
          {'factor: 'life_stage', 'value': ['child', 'adult']}]
    :return: a list containing all combinations of conditions
    """
    conditions = generate.get_condition_combinations(factors)
    condition_object = []
    for cond in conditions:
        sample = get_samples(cond)
        d = {'title': cond, 'position': 'experimental_setting:condition',
             'list': True, 'mandatory': True, 'list_value': [],
             'editable': True, 'input_fields': sample}
        condition_object.append(d)
    return condition_object
