import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.yaml_to_wi_object as yto
import os
import copy
import pytz
from dateutil import parser


def get_factors(organism):
    """
    This function returns all experimental factor with a whitelist of their
    values.
    :param organism: the organism that was selected by the user
    :return: factor_value: a dictionary containing factors and whitelists
    """
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                     'keys.yaml'))
    factor_value = {'factor': utils.read_whitelist('factor')['whitelist']}
    values = {}
    for factor in factor_value['factor']:
        whitelist, whitelist_type, input_type, headers, w_keys = \
            whitelist_parsing.get_whitelist_with_type(factor, key_yaml, organism, None)
        values[factor] = {'whitelist': whitelist, 'input_type': input_type,
                          'whitelist_type': whitelist_type}
        if input_type == 'single_autofill' or input_type == 'multi_autofill':
            values[factor]['search_info'] = {'organism': organism, 'key_name': factor}
        if headers is not None:
            values[factor]['headers'] = headers
        if w_keys is not None:
            values[factor]['whitelist_keys'] = w_keys
    factor_value['values'] = values
    return factor_value


def get_samples(condition, sample, real_val):
    """
    This function created a pre-filled object with the structure of the samples
    to be displayed in the web interface.
    :param condition: the condition the sample is created for
    :param sample: the empty structure of the sample
    :return: sample: the pre-filled sample
    """
    conds = generate.split_cond(condition)
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                     'keys.yaml'))
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
                info = list(utils.find_keys(key_yaml, c[0]))
                if len(info)>0 and 'special_case' in info[0] and 'value_unit' in info[0]['special_case']:
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
                                        sub_info = list(utils.find_keys(key_yaml, x))
                                        if len(sub_info)>0 and 'special_case' in sub_info[0] and 'value_unit' in sub_info[0]['special_case']:
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
                                            sub_info = utils.find_keys(
                                                key_yaml, x)
                                            if len(sub_info) > 0 and 'special_case' in sub_info[0] and 'value_unit' in sub_info[0]['special_case']:
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
                        sample[i]['list_value'].append(c[1])
                        sample[i]['input_disabled'] = True
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
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
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
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                     'keys.yaml'))
    sample = yto.parse_empty(key_yaml['experimental_setting']['value']
                         ['conditions']['value']['biological_replicates']
                         ['value']['samples'],
                         'experimental_setting:conditions:biological_'
                         'replicates:samples', key_yaml, False)[
        'input_fields']
    whitelists = {}
    for item in sample:
        item, whitelists = whitelist_parsing.get_whitelist_object(item, organism,
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
