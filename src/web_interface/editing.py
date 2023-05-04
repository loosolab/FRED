import src.find_metafiles as find_metafiles
import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.whitelist_parsing as whitelist_parsing
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
    meta_yaml = find_metafiles.find_projects(path, project_id, True)
    whitelist_object = {}
    if len(meta_yaml) > 0:
        for elem in meta_yaml:
            for key in elem:
                if key == project_id:
                    meta_yaml = elem[key]
        if 'path' in meta_yaml:
            meta_yaml.pop('path')
        empty_object = yto.get_empty_wi_object(key_yaml)
        wi_object = {}
        for part in empty_object:
            if part == 'all_factors':
                wi_object['all_factors'] = get_all_factors(meta_yaml)
            else:
                wi_object[part], whitelist_object = new_fill(
                    meta_yaml[part], empty_object[part], key_yaml,
                    whitelist_object)

    else:
        wi_object = yto.get_empty_wi_object(key_yaml)

    wi_object['whitelists'] = whitelist_object
    return wi_object


def new_fill(meta_yaml, wi_object, key_yaml, whitelist_object):

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
                    wi_object, meta_yaml, key_yaml, whitelist_object)
                print(len(filled_value))
            else:
                fill_key = 'input_fields'
                filled_value = copy.deepcopy(wi_object['input_fields'])
                for i in range(len(filled_value)):
                    if filled_value[i]['position'].split(':')[-1] in meta_yaml:
                        filled_value[i], whitelist_object = new_fill(
                            meta_yaml[filled_value[i]['position'].split(
                                ':')[-1]],
                            filled_value[i], key_yaml, whitelist_object)

    elif isinstance(meta_yaml, list):
        fill_key = 'list_value'
        filled_value = []
        for i in range(len(meta_yaml)):
            f_val, whitelist_object = new_fill(meta_yaml[i], copy.deepcopy(wi_object),
                                               key_yaml, whitelist_object)
            filled_value.append(f_val)

    else:
        fill_key = 'value'
        filled_value = meta_yaml

    if 'input_type' in wi_object and wi_object['input_type'] == \
            'single_autofill':
        fill_key = 'list_value'

    wi_object[fill_key] = filled_value
    return wi_object, whitelist_object


def fill_experimental_setting(wi_object, meta_yaml, key_yaml, whitelist_object):
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
                                split_cond, copy.deepcopy(sample), {},
                                key_yaml, sample_name, organism)

                            for s in cond['biological_replicates']['samples']:
                                filled_keys = []
                                for k in s:
                                    if s[k] is not None:
                                        if isinstance(s[k], list):
                                            for elem in s[k]:
                                                if (s, elem) not in filled_keys:
                                                    filled_keys.append((s, elem))
                                        elif (s, s[k]) not in split_cond:
                                            filled_keys.append((s, s[k]))

                                sample_name = f'{sample_name}_{int(s["sample_name"].split("_")[-1].replace("b",""))}'
                                filled_sample = copy.deepcopy(input_fields)
                                filled_sample = fac_cond.get_samples(
                                        filled_keys,
                                        filled_sample, {},
                                        key_yaml, sample_name, organism,
                                        is_factor=False)
                                samples.append(filled_sample)
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

                    if 'headers' in f:
                        new_val = ''
                        for header in f['headers'].split(' '):
                            new_val = new_val + ' ' + meta_yaml[key][header]
                        new_val = new_val.lstrip(' ').rstrip(' ')
                    else:
                        new_val = meta_yaml[key]

                    if key == 'organism':
                        organism = new_val
                    if 'list' in f and f['list']:
                        f['list_value'] = new_val
                    else:
                        f['value'] = new_val
                filled_object.append(f)
    return filled_object, whitelist_object



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
