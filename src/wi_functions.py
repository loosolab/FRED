import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.wi_utils as wi_utils
import src.generate as generate
import src.metaTools_functions as metaTools_functions
import os
import copy
import pytz
from dateutil import parser
import multiprocessing

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
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    wi_object = {}
    for key in key_yaml:
        wi_object[key] = parse_empty(key_yaml[key], key, key_yaml, True)
    wi_object['all_factors'] = []
    return wi_object


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
    if isinstance(node[4], dict):
        input_fields = []

        if len(node) > 5 and isinstance(node[5], dict) and 'merge' in node[5]:
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
                        for key in whitelist:
                            if key != 'whitelist_type':
                                new_w.append(
                                    {'title': key, 'whitelist': whitelist[key]})
                        input_type = 'group_select'
                        whitelist = new_w
                        whitelist_type = whitelist['whitelist_type']
                    else:
                        whitelist = whitelist['whitelist']
                        input_type = 'select'
                        whitelist_type = 'plain_group'
            else:
                whitelist = None
            if input_type != 'group_select':
                if isinstance(whitelist, dict):
                    input_type = 'dependable'
            if pos.split(':')[-1] == 'gene':
                input_type = 'gene'
            if pos.split(':')[-1] == 'organism':
                input_type = 'organism_name'
            part_object = {'position': pos,
                   'mandatory': True if node[0] == 'mandatory' else False,
                   'list': node[1], 'displayName': node[2], 'desc': node[3],
                   'value': None,
                   'whitelist': whitelist,
                   'whitelist_type': whitelist_type,
                   'input_type': input_type, 'data_type': 'str',
                   'input_disabled': input_disabled}
        else:
            for key in node[4]:
                input_fields.append(parse_empty(node[4][key], pos + ':' + key,
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

                part_object = {'position': pos,
                       'mandatory': True if node[0] == 'mandatory' else False,
                       'list': node[1], 'displayName': node[2],
                       'desc': node[3], 'value': None, 'value_unit': None,
                       'whitelist': unit_whitelist, 'input_type': 'value_unit',
                       'data_type': 'value_unit',
                       'input_disabled': input_disabled}
            else:
                part_object = {'position': pos,
                       'mandatory': True if node[0] == 'mandatory' else False,
                       'list': node[1], 'title': node[2], 'desc': node[3],
                       'input_fields': input_fields,
                       'input_disabled': input_disabled}
        if node[1]:
            part_object['list_value'] = []
    else:
        if pos.split(':')[-1] == 'organism':
            input_type = 'organism_name'
        else:
            input_type = node[6]
        if get_whitelists:
            if node[5]:
                whitelist = utils.read_whitelist(pos.split(':')[-1])
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
                    if isinstance(whitelist, dict) and not 'whitelist' in whitelist:
                        new_w = []
                        for key in whitelist:
                            if key != 'whitelist_type':
                                new_w.append(
                                    {'title': key, 'whitelist': whitelist[key]})
                        input_type = 'group_select'
                        whitelist = new_w
                    else:
                        whitelist_type = 'plain_group'
                        whitelist = whitelist['whitelist']
            elif node[7] == 'bool':
                whitelist = [True, False]
                input_type = 'select'
            else:
                whitelist = None
            if input_type != 'group_select':
                if isinstance(whitelist, dict):
                    input_type = 'dependable_select'
                # elif whitelist and len(whitelist) > 30:
                #    input_type = 'searchable_select'
        else:
            if node[5]:
                whitelist = pos.split(':')[-1]
            else:
                whitelist = None
            if node[7] == 'bool':
                input_type = 'bool'
                whitelist = pos.split(':')[-1]
        part_object = {'position': pos,
               'mandatory': True if node[0] == 'mandatory' else False,
               'list': node[1], 'displayName': node[2], 'desc': node[3],
               'value': node[4],
               'whitelist': whitelist,
               'whitelist_type': whitelist_type,
               'input_type': input_type, 'data_type': node[7],
               'input_disabled': input_disabled}
        if node[1]:
            part_object['list_value'] = []
    return part_object


def get_factors(organism):
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    factor_value = {'factor': utils.read_whitelist('factor')['whitelist']}
    values = {}
    for factor in factor_value['factor']:
        whitelist, whitelist_type, input_type, headers = get_whitelist_with_type(factor,
                                                                 key_yaml,
                                                                 organism, None)
        values[factor] = {'whitelist': whitelist, 'input_type': input_type,
                          'whitelist_type': whitelist_type}
        if headers is not None:
            values[factor]['headers'] = headers
    factor_value['values'] = values
    return factor_value


def get_whitelist_with_type(key, key_yaml, organism, headers):
    whitelist_type = None
    is_list = False
    filled_object = {'organism': copy.deepcopy(organism)}
    organism = organism.split(' ')[0]
    input_type = list(utils.find_keys(key_yaml, key))
    if len(input_type) > 0:
        if input_type[0][1]:
            is_list = True
        if isinstance(input_type[0][4], dict):
            if len(input_type[0][4].keys()) == 2 and 'value' in \
                    input_type[0][4] and 'unit' in input_type[0][4]:
                input_type = 'value_unit'
            elif isinstance(input_type[0][5], dict) and 'merge' in \
                    input_type[0][5]:
                input_type = 'select'
            else:
                val = []
                for k in input_type[0][4]:
                    k_val = {}
                    k_val['whitelist'], k_val['whitelist_type'], \
                        k_val['input_type'], \
                        header = get_whitelist_with_type(k, key_yaml, organism, headers)
                    if header is not None:
                        k_val['headers'] = header
                    node = list(utils.find_keys(key_yaml, k))[0]
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None
                    k_val['displayName'] = node[2]
                    k_val['required'] = True \
                        if node[0] == 'mandatory' else False
                    k_val['position'] = k
                    k_val['value'] = []
                    val.append(k_val)
                val.append({'displayName': 'Multi', 'position': 'multi',
                            'whitelist': [True, False], 'input_type': 'bool',
                            'value': False})
                input_type = 'nested'
                return val, whitelist_type, input_type, headers
        else:
            if input_type[0][7] == 'bool':
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
        if 'headers' in whitelist:
            headers = whitelist['headers']
        if whitelist['whitelist_type'] == 'group':
            whitelist = utils.read_grouped_whitelist(whitelist, filled_object)
            if 'headers' in whitelist:
                headers = whitelist['headers']
            if 'whitelist' not in whitelist:
                new_w = []
                for value in whitelist:
                    if value not in ['headers', 'whitelist_keys']:
                        new_w.append({'title': value, 'whitelist': whitelist[value]})
                whitelist = new_w
                whitelist_type = 'group'
            else:
                whitelist_type = 'plain_group'
                input_type = 'select'
            input_type = 'group_select'
        elif whitelist['whitelist_type'] == 'depend':
            whitelist = utils.read_depend_whitelist(whitelist, organism)
            whitelist_type = 'depend'
    if isinstance(whitelist, dict) and 'whitelist' in whitelist:
        whitelist = whitelist['whitelist']


    # if whitelist and len(whitelist) > 30:
    #    input_type = 'searchable_select'
    if key == 'gene':
        input_type = 'gene'
    elif key == 'enrichment':
        whitelist = whitelist[:50]
        input_type = 'select'
    if is_list:
        node = list(utils.find_keys(key_yaml, key))[0]
        new_w = [
            {'whitelist': whitelist, 'position': key, 'displayName': node[2],
             'input_type': input_type, 'whitelist_type': whitelist_type},
            {'displayName': 'Multi', 'position': 'multi',
             'whitelist': [True, False], 'input_type': 'bool',
             'value': False}]
        whitelist = new_w
        whitelist_type = 'list_select'
        input_type = 'nested'
    return whitelist, whitelist_type, input_type, headers


def get_samples(condition, sample):
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
                    if 'input_type' in sample[i] and sample[i][
                            'input_type'] == 'gene':
                        val = ""
                        for key in c[1]:
                            val = f'{val}{" " if val != "" else ""}{c[1][key]}'
                        sample[i]['value'] = val
                    else:
                        if sample[i]['list']:
                            sample[i]['list_value'].append(
                                copy.deepcopy(sample[i]['input_fields']))
                            for j in range(len(sample[i]['list_value'])):
                                for k in range(
                                        len(sample[i]['list_value'][j])):
                                    for x in c[1]:
                                        if sample[i]['list_value'][
                                            j][k]['position'].split(
                                                ':')[-1] == x:
                                            if x in ['age', 'time_point',
                                                        'treatment_duration']:
                                                unit = c[1][x].lstrip(
                                                    '0123456789')
                                                value = c[1][x][
                                                        :len(c[1][x]) - len(
                                                            unit)]
                                                sample[i]['list_value'][j][k][
                                                    'value'] = int(value)
                                                sample[i]['list_value'][j][k][
                                                    'value_unit'] = unit
                                            else:
                                                sample[i]['list_value'][j][k][
                                                    'value'] = c[1][x]
                                            sample[i]['list_value'][j][k][
                                                'input_disabled'] = True
                        else:
                            for j in range(len(sample[i]['input_fields'])):
                                for x in c[1]:
                                    if sample[i]['input_fields'][j][
                                            'position'].split(':')[-1] == x:
                                        if x in ['age', 'time_point',
                                                 'treatment_duration']:
                                            unit = c[1][x].lstrip(
                                                '0123456789')
                                            value = c[1][x][
                                                    :len(c[1][x]) - len(unit)]
                                            sample[i]['input_fields'][j][
                                                'value'] = int(value)
                                            sample[i]['input_fields'][j][
                                                'value_unit'] = unit
                                        else:
                                            sample[i]['input_fields'][j][
                                                'value'] = c[1][x]
                else:
                    if sample[i]['list']:
                        if len(sample[i]['list_value']) > 0:
                            sample[i]['list_value'][0]['list_value'].append(c[1])
                        else:
                            sample[i]['list_value'].append(copy.deepcopy(sample[i]))
                            sample[i]['input_fields'].append(copy.deepcopy(sample[i]))
                            sample[i]['list_value'][0]['list_value'].append(c[1])
                            sample[i]['title'] = copy.deepcopy(sample[i]['displayName'])
                            sample[i].pop('displayName')
                            sample[i].pop('value')
                            sample[i].pop('whitelist')
                            sample[i].pop('whitelist_type')
                            sample[i].pop('input_type')
                            sample[i].pop('data_type')
                    else:
                        sample[i]['value'] = c[1]
                sample[i]['input_disabled'] = True
    return sample


def get_conditions(factors, organism_name):
    """
    :param organism_name:
    :param factors: multiple dictionaries containing the keys 'factor' and
    'values' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a list containing all combinations of conditions

    This functions returns all possible combinations for experimental factors
    and their values.
    """
    organism = organism_name.split(' ')[0]
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
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
            if len(node) > 0 and len(node[0]) > 5 and isinstance(node[0][4], dict):
                ident_key = node[0][5]
            else:
                ident_key = None
            factors[i]['values'][0]['ident_key'] = ident_key
            if 'multi' in factors[i]['values'][0]:
                factor_info = list(utils.find_keys(key_yaml, factors[i]['factor']))[0]
                if factor_info[1] and isinstance(factor_info[4], dict):
                    if factors[i]['values'][0]['multi'] and ident_key is None:
                        factors[i]['values'][0]['multi'] = False
                    factors[i]['values'] = generate.get_combis(
                        factors[i]['values'][0], factors[i]['factor'],
                        factors[i]['values'][0]['multi'])
                else:
                    factors[i]['values'] = generate.get_combis(factors[i]['values'][0][factors[i]['factor']], factors[i]['factor'], factors[i]['values'][0]['multi'])
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
    sample = parse_empty(key_yaml['experimental_setting'][4]['conditions'][4]
                         ['biological_replicates'][4]['samples'],
                         'experimental_setting:conditions:biological_'
                         'replicates:samples', key_yaml, False)[
        'input_fields']
    whitelists = {}
    for item in sample:
        item, whitelists = get_whitelist_object(item, organism,
                                                whitelists)

    for cond in conditions:
        cond_sample = copy.deepcopy(sample)
        cond_sample = get_samples(cond, cond_sample)
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
    if 'input_type' in item:
        input_type = item['input_type']
        if input_type == 'select' or input_type == 'gene':
            whitelist = utils.get_whitelist(item['position'].split(':')[-1],
                                            {'organism': organism_name})
            if isinstance(whitelist, dict):
                if 'whitelist_type' in whitelist and whitelist[
                        'whitelist_type'] == 'plain':
                    whitelist = whitelist['whitelist']
                else:
                    input_type = 'group_select'
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
        if item['position'].split(':')[-1] == 'gene':
            if 'whitelist' in whitelist:
                whitelist = whitelist['whitelist']
            input_type = 'gene'
        item['input_type'] = input_type
        if input_type == 'group_select':
            w = []
            for key in whitelist:
                w.append({'title': key, 'whitelist': whitelist[key]})
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
    factors = wi_object['all_factors']
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
    arguments = [(wi_object[key], factors, '', project_id, 1) for key
                 in wi_object]
    pool_obj = multiprocessing.Pool()
    answer = pool_obj.starmap(wi_utils.parse_part, arguments)
    for i in range(len(answer)):
        result[list(wi_object.keys())[i]] = answer[i]
    return result


def validate_object(wi_object):
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
    metafiles = metaTools_functions.find(path,
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
    if file_str is not None:
        filename = f'{file_str[0]}_samples.txt'
        text_file = open(os.path.join(path, filename), "w")
        text_file.write(file_str[1])
        text_file.close()
    else:
        filename = None
    return filename


def get_meta_info(path, project_id):
    # If file must be searched

    yaml = metaTools_functions.find(path, f'id:{project_id}', True)
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
    files = metaTools_functions.find(path, search_string, True)
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
    whitelist = utils.read_whitelist('gene')
    whitelist.pop('whitelist_type')
    whitelist.pop('ident_key')
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
    res = []
    for key in key_yaml:
        d = {'key_name': key,
             'display_name': list(utils.find_keys(key_yaml, key))[0][2]}
        if isinstance(key_yaml[key][4], dict):
            d['nested'] = get_search_keys(key_yaml[key][4],
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
    meta_yaml = metaTools_functions.find(path, project_id, True)
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
    sample = parse_empty(key_yaml['experimental_setting'][4]['conditions'][4]
                         ['biological_replicates'][4]['samples'],
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
                                                'data_type'] == \
                                                    'value_unit':
                                                part['whitelist'] = 'unit'
                                            else:
                                                part['whitelist'] = \
                                                    part['position'].split(
                                                        ':')[-1]
                                else:
                                    if 'whitelist' in field and field[
                                            'whitelist'] is not None:
                                        if field['data_type'] == 'value_unit':
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
