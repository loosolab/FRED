import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.generate as generate
import src.validate_yaml as validate_yaml
import src.metaTools_functions as metaTools_functions
import os
import copy
import datetime
import pytz
from dateutil import parser


# This script contains all functions for generation of objects for the web
# interface


def get_empty_wi_object():
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    result = {}
    for key in key_yaml:
        result[key] = parse_empty(key_yaml[key], key, key_yaml, True)
    result['all_factors'] = []
    return result


def parse_empty(node, pre, key_yaml, get_whitelists):
    input_disabled = True if pre.split(':')[-1] in ['condition_name',
                                                    'sample_name'] else False
    if isinstance(node[4], dict):
        input_fields = []

        if len(node) > 5 and isinstance(node[5], dict) and 'merge' in node[5]:
            input_type = 'select'
            if get_whitelists:
                whitelist = utils.read_whitelist(pre.split(':')[-1])
                if 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'depend':
                    whitelist = None
                    input_type = 'dependable'
                elif 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'group':
                    new_w = []
                    for key in whitelist:
                        if key != 'whitelist_type':
                            new_w.append(
                                {'title': key, 'whitelist': whitelist[key]})
                    input_type = 'group_select'
                    whitelist = new_w
            else:
                whitelist = None
            if input_type != 'group_select':
                if isinstance(whitelist, dict):
                    input_type = 'dependable'
            if pre.split(':')[-1] == 'gene':
                input_type = 'gene'
            if pre.split(':')[-1] == 'organism':
                input_type = 'organism_name'
            res = {'position': pre,
                   'mandatory': True if node[0] == 'mandatory' else False,
                   'list': node[1], 'displayName': node[2], 'desc': node[3],
                   'value': None,
                   'whitelist': whitelist,
                   'input_type': input_type, 'data_type': 'str',
                   'input_disabled': input_disabled}
        else:
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
                       'list': node[1], 'displayName': node[2],
                       'desc': node[3], 'value': None, 'value_unit': None,
                       'whitelist': unit_whitelist, 'input_type': 'value_unit',
                       'data_type': 'value_unit', 'input_disabled': input_disabled}
            else:
                res = {'position': pre,
                       'mandatory': True if node[0] == 'mandatory' else False,
                       'list': node[1], 'title': node[2], 'desc': node[3],
                       'input_fields': input_fields,
                       'input_disabled': input_disabled}
        if node[1]:
            res['list_value'] = []
    else:
        if pre.split(':')[-1] == 'organism':
            input_type = 'organism_name'
        else:
            input_type = node[6]
        if get_whitelists:
            if node[5]:
                whitelist = utils.read_whitelist(pre.split(':')[-1])
                if 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'depend':
                    whitelist = None
                    input_type = 'dependable'
                elif 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'group':
                    new_w = []
                    for key in whitelist:
                        if key != 'whitelist_type':
                            new_w.append(
                                {'title': key, 'whitelist': whitelist[key]})
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
                # elif whitelist and len(whitelist) > 30:
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
    factor_value = {'factor': utils.read_whitelist('factor')}
    values = {}
    for factor in factor_value['factor']:
        whitelist, input_type, headers = get_whitelist_with_type(factor, key_yaml,
                                                        organism)
        values[factor] = {'whitelist': whitelist, 'input_type': input_type}
        if headers is not None:
            values[factor]['headers'] = headers
    factor_value['values'] = values
    return factor_value


def get_whitelist_with_type(key, key_yaml, organism):
    headers = None
    input_type = list(utils.find_keys(key_yaml, key))
    if len(input_type) > 0:
        if isinstance(input_type[0][4], dict):
            if len(input_type[0][4].keys()) == 2 and 'value' in \
                    input_type[0][4] and 'unit' in input_type[0][4]:
                    input_type = 'value_unit'
            elif isinstance(input_type[0][5], dict) and 'merge' in input_type[0][5]:
                    input_type = 'select'
            else:
                val = []
                for k in input_type[0][4]:
                    k_val = {}
                    k_val['whitelist'], k_val['input_type'], header = get_whitelist_with_type(k, key_yaml, organism)
                    if header is not None:
                        key_val['headers'] = header
                    node = list(utils.find_keys(key_yaml, k))[0]
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None
                    k_val['displayName'] = node[2]
                    k_val['required'] = True if node[0] == 'mandatory' else False
                    k_val['position'] = k
                    k_val['value'] = []
                    val.append(k_val)
                val.append({'displayName': 'Multi', 'position': 'multi', 'whitelist': [True, False], 'input_type': 'bool', 'value': False})
                input_type = 'nested'
                return val, input_type, headers

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
        if whitelist['whitelist_type'] == 'group':
            whitelist = utils.read_grouped_whitelist(whitelist)
            new_w = []
            for value in whitelist:
                new_w.append({'title': value, 'whitelist': whitelist[value]})
            whitelist = new_w
            input_type = 'group_select'
        elif whitelist['whitelist_type'] == 'depend':
            whitelist = utils.read_depend_whitelist(whitelist, organism)

    if isinstance(whitelist, dict) and 'whitelist' in whitelist:
        if 'headers' in whitelist:
            headers = whitelist['headers']
        whitelist = whitelist['whitelist']

    # if whitelist and len(whitelist) > 30:
    #    input_type = 'searchable_select'
    if key == 'gene':
        input_type = 'gene'
    return whitelist, input_type, headers


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
                if c[0] in ['age', 'time_point', 'treatment_duration']:
                    unit = c[1].lstrip('0123456789')
                    value = c[1][:len(c[1]) - len(unit)]
                    sample[i]['value'] = int(value)
                    sample[i]['value_unit'] = unit
                elif isinstance(c[1], dict):
                   if 'input_type' in sample[i] and sample[i]['input_type'] == 'gene':
                       val = ""
                       for key in c[1]:
                           val = f'{val}{" " if val != "" else ""}{c[1][key]}'
                       sample[i]['value'] = val
                   else:
                        if sample[i]['list']:
                            sample[i]['list_value'].append(copy.deepcopy(sample[i]['input_fields']))
                            for j in range(len(sample[i]['list_value'])):
                                for k in range(len(sample[i]['list_value'][j])):
                                    for x in c[1]:
                                        if sample[i]['list_value'][j][k]['position'].split(':')[-1] == x:
                                            if x in ['age', 'time_point',
                                                     'treatment_duration']:
                                                unit = c[1][x].lstrip(
                                                    '0123456789')
                                                value = c[1][x][
                                                        :len(c[1][x]) - len(unit)]
                                                sample[i]['list_value'][j][k]['value'] = int(value)
                                                sample[i]['list_value'][j][k]['value_unit'] = unit
                                            else:
                                                sample[i]['list_value'][j][k]['value'] = c[1][x]
                                            sample[i]['list_value'][j][k]['input_disabled'] = True
                        else:
                            for j in range(len(sample[i]['input_fields'])):
                                for x in c[1]:
                                    if sample[i]['input_fields'][j]['position'].split(':')[-1] == x:
                                        if x in ['age', 'time_point',
                                                 'treatment_duration']:
                                            unit = c[1][x].lstrip(
                                                '0123456789')
                                            value = c[1][x][
                                                    :len(c[1][x]) - len(unit)]
                                            sample[i]['input_fields'][j]['value'] = int(value)
                                            sample[i]['input_fields'][j][
                                                'value_unit'] = unit
                                        else:
                                            sample[i]['input_fields'][j]['value'] = c[1][x]


                else:
                    sample[i]['value'] = c[1]

                sample[i]['input_disabled'] = True
    return sample


def get_conditions(factors, organism_name):
    """
    This functions returns all possible combinations for experimental factors
    and their values.
    :param factors: multiple dictionaries containing the keys 'factor' and
    'values' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a list containing all combinations of conditions
    """
    for i in range(len(factors)):
        if len(factors[i]['values']) == 1 and isinstance(factors[i]['values'][0], dict) and not ('value' in factors[i]['values'][0] and 'unit' in factors[i]['values'][0]):
            empty_key = []
            for k in factors[i]['values'][0]:
                if (isinstance(factors[i]['values'][0][k], list) and len(factors[i]['values'][0][k]) == 0) or factors[i]['values'][0][k] is None:
                    empty_key.append(k)
            for key in empty_key:
                factors[i]['values'][0].pop(key)
            key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'keys.yaml'))
            node = list(utils.find_keys(key_yaml, factors[i]['factor']))
            if len(node) > 0 and len(node[0]) > 5:
                ident_key = node[0][5]
            else:
                ident_key = None
            factors[i]['values'][0]['ident_key'] = ident_key
            if 'multi' in factors[i]['values'][0]:
                if factors[i]['values'][0]['multi'] and ident_key is None:
                    factors[i]['values'][0]['multi'] = False
                factors[i]['values'] = generate.get_combis(factors[i]['values'][0], factors[i]['factor'], factors[i]['values'][0]['multi'])
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
        item, whitelists = get_whitelist_object(item, organism_name,
                                                whitelists)

    for cond in conditions:
        cond_sample = copy.deepcopy(sample)
        cond_sample = get_samples(cond, cond_sample)
        d = {'title': cond, 'position': 'experimental_setting:condition',
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
                input_type = 'group_select'
        elif input_type == 'bool':
            whitelist = [True, False]
            input_type = 'select'
        elif input_type == 'value_unit':
            item['value_unit'] = None
            whitelist = utils.read_whitelist('unit')
        else:
            whitelist = None
        if item['position'].split(':')[-1] == 'gene':
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
    result = {}
    for key in wi_object:
        result[key] = parse_part(wi_object[key], factors)
    return result


def parse_part(wi_object, factors):
    if 'input_type' in wi_object and wi_object['input_type'] == 'gene':
        key_yaml = utils.read_in_yaml(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            'keys.yaml'))
        sub_keys = list(utils.find_keys(key_yaml, wi_object['position'].split(':')[-1]))[0][4].keys()
        new_samp = {'position': wi_object['position'],
                    'mandatory': wi_object['mandatory'],
                    'list': wi_object['list'],
                    'title': wi_object['displayName'],
                    'desc': wi_object['desc']}
        input_fields = []
        for key in sub_keys:
            node = list(utils.find_keys(key_yaml, key))[0]
            input_fields.append(parse_empty(node, f'{wi_object["position"]}:{key}', key_yaml, False))
        for elem in factors:
            for i in range(len(elem)):
                if 'headers' in elem[i] and elem[i]['factor'] == wi_object['position'].split(':')[-1]:
                    for j in range(len(elem[i]['headers'].split(' '))):
                        for f in input_fields:
                            if f['position'].split(':')[-1] == elem[i]['headers'].split(' ')[j]:
                                f['value'] = wi_object['value'].split(' ')[j]
        new_samp['input_fields'] = input_fields
        wi_object = new_samp

    return_dict = {}
    if isinstance(wi_object, dict):
        if wi_object['list']:
            test = []
            for elem in wi_object['list_value']:
                if not isinstance(elem, dict) and not isinstance(elem, list):
                    test.append(elem)
                else:
                    test.append(parse_part(elem, factors))
            return test
        else:
            if 'input_fields' in wi_object:
                return parse_part(wi_object['input_fields'], factors)
            else:
                if wi_object['value'] and wi_object[
                        'input_type'] == 'value_unit':
                    unit = wi_object['value_unit']
                    value = wi_object['value']
                    return {'unit': unit, 'value': value}
                else:
                    return wi_object['value']
    elif isinstance(wi_object, list):
        for i in range(len(wi_object)):
            if wi_object[i]['position'].split(':')[-1] == 'conditions':
                test = []
                for j in range(len(wi_object[i]['list_value'])):
                    value = parse_part(wi_object[i]['list_value'][j], factors)
                    if ((isinstance(value, list) or isinstance(value,
                                                               dict)) and len(
                        value) > 0) or (
                            not isinstance(value, list) and not isinstance(
                        value,
                        dict) and value is not None and value != ''):
                        test.append({'condition_name':
                                         wi_object[i]['list_value'][j][
                                             'title'],
                                     'biological_replicates': {
                                         'count': len(value),
                                         'samples': value}})
                    else:
                        test.append({'condition_name':
                                         wi_object[i]['list_value'][j][
                                             'title']})
                return_dict['conditions'] = test
            elif wi_object[i]['position'].split(':')[
                -1] == 'technical_replicates':
                technical_replicates = parse_part(wi_object[i], factors)
                sample_name = []
                for c in range(technical_replicates['count']):
                    sample_name.append(
                        f'{return_dict["sample_name"]}_t{c + 1}')
                technical_replicates['sample_name'] = sample_name
                return_dict['technical_replicates'] = technical_replicates
            elif wi_object[i]['position'].split(':')[
                -1] == 'experimental_factors':
                res = []
                all_factors = {}
                i = 0
                for elem in factors:
                    for d in elem:
                        if 'headers' in d:
                            header = d['headers'].split(' ')
                            d.pop('headers')
                            for l in range(len(d['values'])):
                                vals = d['values'][l].split(' ')
                                d['values'][l] = {}
                                for h in range(len(header)):
                                    d['values'][l][header[h]] = vals[h]
                        else:
                            for j in range(len(d['values'])):
                                if isinstance(d['values'][j], dict):
                                    empty_keys = []
                                    for key in d['values'][j]:
                                        if not isinstance(d['values'][j][key],list) or len(d['values'][j][key]) == 0:
                                            empty_keys.append(key)
                                    for key in empty_keys:
                                        d['values'][j].pop(key)
                        if not any(d['factor'] in y['factor'] for y in res):
                            res.append(d)
                            all_factors[d['factor']] = i
                            i += 1
                        else:
                            for x in d['values']:
                                if x not in res[all_factors[d['factor']]][
                                        'values']:
                                    res[all_factors[d['factor']]][
                                        'values'].append(x)
                return_dict['experimental_factors'] = res

            else:
                value = parse_part(wi_object[i], factors)
                if ((isinstance(value, list) or isinstance(value,
                                                           dict)) and len(
                    value) > 0) or (
                        not isinstance(value, list) and not isinstance(value,
                                                                       dict) and value is not None and value != ''):
                    if 'input_type' in wi_object[i] and wi_object[i][
                            'input_type'] == 'date':
                        default_time = parser.parse(wi_object[i]['value'])
                        timezone = pytz.timezone("Europe/Berlin")
                        local_time = default_time.astimezone(timezone)
                        value = local_time.strftime("%d.%m.%Y")
                    return_dict[
                        wi_object[i]['position'].split(':')[-1]] = value
    return return_dict


def validate_object(wi_object):
    pooled = None
    organisms = []
    warnings = {}
    errors = {}
    factors = wi_object['all_factors']
    wi_object.pop('all_factors')
    for elem in wi_object:
        wi_object[
            elem], pooled, organisms, part_warnings, part_errors = validate_part(
            wi_object[elem], [], pooled, organisms, [])
        warnings[elem] = part_warnings
        errors[elem] = part_errors
    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    wi_object = new_object
    wi_object['all_factors'] = factors
    html_str = ''
    yaml_object = parse_object(wi_object)
    for elem in yaml_object:
        html_str = f'{html_str}<h3>{elem}</h3>{object_to_html(yaml_object[elem], 0, 0, False)}<br>{"<hr><br>" if elem != list(yaml_object.keys())[-1] else ""}'
    wi_object['all_factors'] = factors
    validation_object = {'object': wi_object, 'errors': errors,
                         'warnings': warnings, 'summary': html_str,
                         'yaml': yaml_object}
    return validation_object


def validate_part(wi_object, warnings, pooled, organisms, errors):
    error_desc = ''
    warning_desc = ''
    if isinstance(wi_object, dict):
        if 'desc' in wi_object and 'backup_desc' not in wi_object:
            wi_object['backup_desc'] = wi_object['desc']
        if wi_object['list']:
            if not any([isinstance(x, dict) or isinstance(x, list) for x in
                        wi_object['list_value']]):
                error = False
                messages = []
                for elem in wi_object['list_value']:
                    valid, message = validate_yaml.validate_value(elem,
                                                                  wi_object[
                                                                      'data_type'],
                                                                  wi_object[
                                                                      'position'].split(
                                                                      ':')[-1])
                    if not valid:
                        error = True
                        messages.append((elem, message))
                        errors.append(
                            f'{wi_object["position"]}: Value {elem} - {message}')
                wi_object['error'] = error
                if error:
                    message = ', '.join(
                        [f'{msg[0]}: {msg[1]}' for msg in messages])
                    error_desc = f'{error_desc}{"<br>" if error_desc != "" else ""}<font color="red">{message}</font>'
                wi_object[
                    'desc'] = f'{wi_object["backup_desc"]}{"<br>" if wi_object["backup_desc"] != "" else ""}{error_desc}{"<br>" if error_desc != "" else ""}{warning_desc}'
            else:
                wi_object[
                    'list_value'], pooled, organisms, warnings, errors = validate_part(
                    wi_object['list_value'], warnings, pooled, organisms,
                    errors)
        else:
            if 'input_fields' in wi_object:
                wi_object[
                    'input_fields'], pooled, organisms, warnings, errors = validate_part(
                    wi_object['input_fields'], warnings, pooled, organisms,
                    errors)
            else:
                if wi_object['value'] is not None and wi_object['value'] != '':
                    if wi_object['input_type'] == 'date':
                        default_time = parser.parse(wi_object['value'])
                        timezone = pytz.timezone("Europe/Berlin")
                        local_time = default_time.astimezone(timezone)
                        value = local_time.strftime("%d.%m.%Y")
                    else:
                        value = wi_object['value']
                    valid, message = validate_yaml.validate_value(value,
                                                                  wi_object[
                                                                      'data_type'],
                                                                  wi_object[
                                                                      'position'].split(
                                                                      ':')[-1])
                    wi_object['error'] = not valid
                    if not valid:
                        errors.append(f'{wi_object["position"]}: {message}')
                        error_desc = f'{error_desc}{"<br>" if error_desc != "" else ""}<font color="red">{message}</font>'

                    warning = False
                    warn_text = None
                    key = wi_object['position'].split(':')[-1]
                    if key == 'pooled':
                        pooled = wi_object['value']
                    elif key == 'donor_count':
                        warning, warn_text = validate_yaml.validate_donor_count(
                            pooled, wi_object['value'])
                    elif key == 'organism':
                        organisms.append(wi_object['value'])
                    elif key == 'reference_genome':
                        warning, warn_text = validate_yaml.validate_reference_genome(
                            organisms, wi_object['value'])
                    wi_object['warning'] = warning
                    if warning:
                        warnings.append(
                            f'{wi_object["position"]}: {warn_text}')
                        warning_desc = f'{warning_desc}{"<br>" if warning_desc != "" else ""}<font color="orange">{warn_text}</font>'
                    wi_object[
                        'desc'] = f'{wi_object["backup_desc"]}{"<br>" if wi_object["backup_desc"] != "" else ""}{error_desc}{"<br>" if error_desc != "" else ""}{warning_desc}'
    elif isinstance(wi_object, list):
        for i in range(len(wi_object)):
            wi_object[i], pooled, organisms, warnings, errors = validate_part(
                wi_object[i], warnings, pooled, organisms, errors)
    return wi_object, pooled, organisms, warnings, errors


def object_to_html(yaml_object, depth, margin, is_list):
    html_str = ''
    if isinstance(yaml_object, dict):
        for key in yaml_object:
            if key == list(yaml_object.keys())[0] and is_list:
                html_str = f'{html_str}<ul style="list-style-type: circle;"><li><p><font color={get_color(depth)}>{key}</font>: {object_to_html(yaml_object[key], depth+1, margin+1.5, is_list)}</p></li></ul>'
            else:
                html_str = f'{html_str}<ul style="list-style: none;"><li><p><font color={get_color(depth)}>{key}</font>: {object_to_html(yaml_object[key], depth+1, margin+1.5, is_list)}</p></li></ul>'
    elif isinstance(yaml_object, list):
        for elem in yaml_object:
            if not isinstance(elem, list) and not isinstance(elem,dict):
                html_str = f'{html_str}<ul style="list-style-type: circle;"><li><p>{elem}</p></li></ul>'
            else:
                html_str = f'{html_str}{object_to_html(elem, depth, margin, True)}'
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


def save_object(dictionary, path):
    utils.save_as_yaml(dictionary, os.path.join(path,
                                                f'{dictionary["project"]["id"]}_metadata.yaml'))


def get_meta_info(path, id):
    # If file must be searched

    yaml = metaTools_functions.find(path, f'id:{id}', True)
    if len(yaml) == 0:
        return f'No metadata found.'
    elif len(yaml) > 1:
        return f'Error: Multiple metadata files found.'
    else:
        if 'path' in yaml[0][id]:
            yaml[0][id].pop('path')
        html_str = ''
        for elem in yaml[0][id]:
            html_str = f'{html_str}<h3>{elem}</h3>{object_to_html(yaml[0][id][elem], 0, 0, False)}<br>{"<hr><br>" if elem != list(yaml[0][id].keys())[-1] else ""}'
        return html_str

