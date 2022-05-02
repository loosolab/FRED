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
    if isinstance(node[4], dict):
        input_fields = []
        for key in node[4]:
            input_fields.append(parse_empty(node[4][key], pre + ':' + key))
        res = {'position': pre, 'mandatory' : True if node[0]=='mandatory' else False,
               'list': node [1], 'title': node[2], 'desc': node[3], 'input_fields': input_fields}
    else:
        if node[5]:
            whitelist = utils.read_whitelist(pre.split(':')[-1])
        else:
            whitelist = None
        res = {'position': pre, 'mandatory': True if node[0]=='mandatory' else False , 'list': node[1],
               'displayName':node[2], 'desc':node[3], 'value': node[4],
               'whitelist':whitelist, 'input_type':node[6], 'data_type': node[7]}
    return res


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
    return generate.get_condition_combinations(factors)