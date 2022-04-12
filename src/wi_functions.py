from src import utils

# This script contains all functions for generation of objects for the web
# interface


def get_empty_wi_object(node):
    result = []
    for key in node:
        result.append(parse_empty(node[key], key))
    return result


def parse_empty(node, pre):
    if isinstance(node[4], dict):
        input_fields = []
        for key in node[4]:
            input_fields.append(parse_empty(node[4][key], pre + ':' + key))
        res = {'position': pre, 'mandatory' : True if node[0]=='mandatory' else False,
               'list': node [1], 'title': node[2], 'desc': node[3], 'input_fields': input_fields}
    else:
        if node[5] == True:
            whitelist = utils.read_whitelist(pre.split(':')[-1])
        else:
            whitelist = None
        res = {'position': pre, 'mandatory': True if node[0]=='mandatory' else False , 'list': node[1],
               'displayName':node[2], 'desc':node[3], 'value': node[4],
               'whitelist':whitelist, 'input_type':node[6], 'data_type': node[7]}
    return res