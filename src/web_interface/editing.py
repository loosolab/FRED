import src.find_metafiles as find_metafiles
import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.searching as searching
import os
import copy
import pytz
from dateutil import parser

disabled_fields = []


def edit_wi_object(path, project_id, key_yaml):
    """
    This function fills an empty wi object with the information of a metadata
    file.
    :param path: the path containing the metadata file
    :param project_id: the id of the  project
    :return: wi_object: the filled wi object
    """
    # TODO: als Übergabe bei get_info
    html_str, meta_yaml = searching.get_meta_info(path, project_id)
    whitelist_object = {}
    if meta_yaml is not None:
        file_path = meta_yaml['path']
        meta_yaml.pop('path')
        empty_object = yto.get_empty_wi_object(key_yaml)
        wi_object = {}
        wi_object['all_factors'], real_val = get_all_factors(meta_yaml,
                                                             key_yaml)
        for part in empty_object:
            if part != 'all_factors':
                wi_object[part], whitelist_object = new_fill(
                    meta_yaml[part], empty_object[part], key_yaml,
                    whitelist_object, real_val)

    else:
        wi_object = yto.get_empty_wi_object(key_yaml)

    wi_object['whitelists'] = whitelist_object
    wi_object['path'] = file_path
    return wi_object


def new_fill(meta_yaml, wi_object, key_yaml, whitelist_object, real_val):

    if isinstance(meta_yaml, dict):

        if 'headers' in wi_object:
            fill_key = 'value'
            filled_value = ''
            for header in wi_object['headers'].split(' '):
                filled_value = filled_value + ' ' + meta_yaml[header]
            filled_value = filled_value.lstrip(' ').rstrip(' ')
        else:
            if wi_object['position'].split(':')[-1] == 'experimental_setting':
                fill_key = 'input_fields'
                filled_value, whitelist_object = fill_experimental_setting(
                    wi_object, meta_yaml, key_yaml, whitelist_object, real_val)
                print(len(filled_value))
            else:
                fill_key = 'input_fields'
                filled_value = copy.deepcopy(wi_object['input_fields'])
                for i in range(len(filled_value)):
                    if filled_value[i]['position'].split(':')[-1] in meta_yaml:
                        filled_value[i], whitelist_object = new_fill(
                            meta_yaml[filled_value[i]['position'].split(
                                ':')[-1]],
                            filled_value[i], key_yaml, whitelist_object, real_val)

    elif isinstance(meta_yaml, list):
        fill_key = 'list_value'
        filled_value = []
        for i in range(len(meta_yaml)):
            f_val, whitelist_object = new_fill(meta_yaml[i], copy.deepcopy(wi_object),
                                               key_yaml, whitelist_object, real_val)
            # TODO: WTF?
            if 'input_fields' in f_val:
                f_val = f_val['input_fields']
            else:
                f_val = f_val['value']
            filled_value.append(f_val)

    else:
        fill_key = 'value'
        filled_value = meta_yaml

    if 'input_type' in wi_object and wi_object['input_type'] == \
            'single_autofill':
        fill_key = 'list_value'

    wi_object[fill_key] = filled_value
    return wi_object, whitelist_object


def fill_experimental_setting(wi_object, meta_yaml, key_yaml, whitelist_object, real_val):
    organism = ''
    filled_object = []
    for j in range(len(wi_object['input_fields'])):
        f = copy.deepcopy(wi_object['input_fields'][j])
        for key in meta_yaml:

            if wi_object['input_fields'][j]['position'].split(':')[-1] == key:
                if key == 'experimental_factors':
                    pass
                elif key == 'conditions':
                    sample = list(utils.find_keys(key_yaml, 'samples'))
                    if len(sample) > 0:

                        sample, whitelists = yto.parse_empty(
                            sample[0],
                            'experimental_setting:conditions:biological_'
                            'replicates:samples', key_yaml,
                            {'organism': organism},
                            get_whitelist_object=True)
                        sample = sample['input_fields']

                        conditions = []

                        for cond in meta_yaml[key]:
                            samples = []
                            split_cond = generate.split_cond(
                                cond['condition_name'])
                            sample_name = generate.get_short_name(
                                cond['condition_name'], {})
                            input_fields = fac_cond.get_samples(
                                split_cond, copy.deepcopy(sample), real_val,
                                key_yaml, sample_name, organism)

                            for s in cond['biological_replicates']['samples']:
                                filled_keys = []
                                for k in s:
                                    if s[k] is not None:
                                        # TODO: dict (disease usw.)
                                        # TODO: real_val
                                        if isinstance(s[k], list):
                                            for elem in s[k]:
                                                if (s, elem) not in filled_keys and (s, elem) not in split_cond:
                                                    filled_keys.append((s, elem))
                                        elif (s, s[k]) not in split_cond:
                                            filled_keys.append((s, s[k]))

                                cond_sample_name = f'{sample_name}_{int(s["sample_name"].split("_")[-1].replace("b",""))}'
                                filled_sample = copy.deepcopy(input_fields)
                                filled_sample = fac_cond.get_samples(
                                        filled_keys,
                                        filled_sample, real_val,
                                        key_yaml, cond_sample_name, organism,
                                        is_factor=False)
                                samples.append(copy.deepcopy(filled_sample))
                            d = {'correct_value': cond['condition_name'],
                                 'title': cond['condition_name'].replace(':',
                                                                         ': ').replace(
                                     '|',
                                     '| ').replace(
                                     '#', '# ').replace('-', ' - '),
                                 'position': 'experimental_setting:condition',
                                 'list': True, 'mandatory': True,
                                 'list_value': samples,
                                 'input_disabled': False, 'desc': '',
                                 'input_fields': input_fields}
                            conditions.append(d)
                        f['list_value'] = conditions
                        whitelist_object[organism] = whitelists

                else:

                    if 'headers' in f and isinstance(meta_yaml[key], dict):
                        new_val = parse_headers(meta_yaml[key], f['headers'])
                    else:
                        new_val = meta_yaml[key]

                    if key == 'organism':
                        if 'organism_name' in new_val:
                            organism = new_val['organism_name']
                        else:
                            organism = new_val

                    if 'whitelist_keys' in f:
                        new_val = parse_whitelist_keys(meta_yaml[key], f['whitelist_keys'], utils.get_whitelist(key, {'organism': organism}))

                    if 'list' in f and f['list']:
                        f['list_value'] = new_val
                    else:
                        f['value'] = new_val
                filled_object.append(f)
    return filled_object, whitelist_object


def parse_headers(value, headers):

    if isinstance(headers, dict):
        header = None
        for k in headers:
            if sorted(headers[k].split(' ')) == sorted(list(value.keys())):
                header = headers[k].split(' ')
                break
    else:
        header = headers.split(' ')

    if header is not None:
        val = ''
        for h in header:
            val = f'{val}{" " if val != "" else ""}{value[h]}'
        value = val

    return value


def parse_whitelist_keys(value, whitelist_keys, whitelist):

    for key in whitelist_keys:
        if f'{value} ({key})' in whitelist:
            value = f'{value} ({key})'
            break

    return value


# TODO: value unit?
def get_all_factors(meta_yaml, real_val):
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
            w = utils.get_whitelist(factors['factor'], setting)
            setting_fac['values'] = []
            for elem in factors['values']:
                value = elem
                if w and 'headers' in w:
                    if 'headers' not in setting_fac:
                        setting_fac['headers'] = w['headers']
                    if isinstance(elem, dict):
                        value = parse_headers(value, w['headers'])

                if w and 'whitelist_keys' in w:
                    if 'whitelist_keys' not in setting_fac:
                        setting_fac['whitelist_keys'] = w['whitelist_keys']
                    if 'whitelist_type' in w and w['whitelist_type'] == 'plain_group':
                        value = parse_whitelist_keys(value, w['whitelist_keys'], w['whitelist'])

                if isinstance(elem, dict) and len(list(elem.keys()))==2 and 'unit' in elem and 'value' in elem:
                    value = f'{elem["value"]}{elem["unit"]}'

                if value != elem:
                    if isinstance(elem, dict):
                        # rewrite the value into a string
                        val = "|".join(
                            [f'{key}:"{elem[key]}"' for key in elem])
                        val = f'{factors["factor"]}:{"{"}{val}{"}"}'
                        real_val[val] = value
                    else:
                        real_val[elem] = value
                setting_fac['values'].append(value)
            setting_factors.append(setting_fac)
        all_factors.append(setting_factors)
    return all_factors, real_val
