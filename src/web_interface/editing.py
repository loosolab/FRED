import src.find_metafiles as find_metafiles
import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.whitelist_parsing as whitelist_parsing
import os
import copy
import pytz
from dateutil import parser


def edit_wi_object(path, project_id, key_yaml):
    """
    This function fills an empty wi object with the information of a metadata
    file.
    :param path: the path containing the metadata file
    :param project_id: the id of the  project
    :return: wi_object: the filled wi object
    """
    meta_yaml = find_metafiles.find_projects(path, project_id, True)

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
                wi_object[part] = get_all_factors(meta_yaml)
            else:
                wi_object[part] = fill_wi_object(empty_object[part],
                                                 meta_yaml[part])
    else:
        wi_object = yto.get_empty_wi_object(key_yaml)

    sample, whitelist_object = yto.parse_empty(
        key_yaml['experimental_setting']['value']['conditions']['value']
        ['biological_replicates']['value']['samples'],
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
            item, whitelists = whitelist_parsing.get_whitelist_object(item,
                                                    organism.split(' ')[0],
                                                    whitelists)
        whitelist_object[organism] = whitelists
    wi_object['whitelists'] = whitelist_object
    return wi_object


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


def fill_wi_object(wi_object, meta_yaml):
    """
    This function fills an empty wi object with the information of a metadata
    file.
    :param wi_object: the empty wi object
    :param meta_yaml: the metadata file
    :return: wi_object: the filled wi object
    """
    if 'list' in wi_object and wi_object['list']:
        if 'input_fields' in wi_object:
            if wi_object['position'].split(':')[-1] != 'experimental_factors':
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
                                                'input_type'] == \
                                                    'value_unit':
                                                part['whitelist'] = 'unit'
                                            else:
                                                part['whitelist'] = \
                                                    part['position'].split(
                                                        ':')[-1]
                                else:
                                    if 'whitelist' in field and field[
                                            'whitelist'] is not None:
                                        if field['input_type'] == 'value_unit':
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