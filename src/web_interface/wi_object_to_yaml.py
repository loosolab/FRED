import src.utils as utils
import src.web_interface.factors_and_conditions as fact_cond
import copy
import os
import pytz
from dateutil import parser


def parse_object(wi_object):
    """
    This function parses a wi object back into a yaml.
    :param wi_object: the filled wi object
    :return: result: a dictionary matching the metadata yaml structure
    """
    factors = copy.deepcopy(wi_object['all_factors'])
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
    for key in wi_object:
        result[key] = parse_part(wi_object[key], factors, '', project_id, 1)
    return result


def parse_part(wi_object, factors, organism, id, nom):
    """
    This function parses a part of the wi object to create the yaml structure.
    :param wi_object: a part of the filled wi object
    :param factors: the selested experimental factors
    :param organism: the slected organism
    :param id: the project id
    :param nom: the number of measurements
    :return: val: the parsed part in yaml structure
    """
    gn = None
    embl = None
    key_yaml = utils.read_in_yaml(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        'keys.yaml'))

    if isinstance(wi_object, dict):
        if wi_object['list'] or ('input_type' in wi_object and (wi_object['input_type'] == 'single_autofill' or wi_object['input_type'] == 'multi_autofill')):
            val = []
            if 'list_value' in wi_object:
                for i in range(len(wi_object['list_value'])):
                    if isinstance(wi_object['list_value'][i], dict):
                        if wi_object['list_value'][i]['position'].split(':')[-1] == 'condition':

                            samples = []
                            for sub_elem in wi_object['list_value'][i]['list_value']:
                                samples.append(fact_cond.get_sample(sub_elem, id, organism, factors, nom))

                            val.append({'condition_name': wi_object['list_value'][i]['correct_value'],
                                        'biological_replicates':
                                            {'count': len(samples),
                                             'samples': samples}})

                        #else:
                        #    print(elem['position'])
                    elif isinstance(wi_object['list_value'][i], list):
                        if wi_object['position'].split(':')[-1] == 'experimental_setting':
                            val.append(parse_list_part(wi_object['list_value'][i], factors[i], organism, id,
                                                   nom))
                        else:
                            val.append(parse_list_part(wi_object['list_value'][i], factors, organism, id,
                                                   nom))
                    else:
                        val.append(wi_object['list_value'][i])
        else:
            if 'whitelist_keys' in wi_object:
                for k in wi_object['whitelist_keys']:
                    if wi_object['value'].endswith(f' ({k})'):
                        wi_object['value'] = wi_object['value'].replace(f' ({k})', '')
                    if 'headers' in wi_object and k in wi_object['headers']:
                        new_val = {}
                        for l in range(len(wi_object['headers'][k].split(' '))):
                            new_val[wi_object['headers'][k].split(' ')[l]] = wi_object['value'].split(' ')[l]
                        wi_object['value'] = new_val
                        break
            elif 'headers' in wi_object:
                new_val = {}
                for l in range(len(wi_object['headers'].split(' '))):
                    new_val[wi_object['headers'].split(' ')[l]] = wi_object['value'].split(' ')[l]
                wi_object['value'] = new_val

            if 'input_fields' in wi_object:
                val = parse_part(wi_object['input_fields'], factors, organism,
                                 id, nom)
            else:
                if wi_object['value'] and wi_object[
                        'input_type'] == 'value_unit':
                    unit = wi_object['value_unit']
                    value = wi_object['value']
                    val = {'unit': unit, 'value': value}
                elif wi_object['value'] and wi_object['input_type'] == 'date':
                    default_time = parser.parse(wi_object['value'])
                    timezone = pytz.timezone("Europe/Berlin")
                    local_time = default_time.astimezone(timezone)
                    val = local_time.strftime("%d.%m.%Y")
                else:
                    if 'correct_value' in wi_object:
                        if wi_object['position'].split(':')[-1] == \
                                'sample_name':
                            sample_count = \
                                int(wi_object['value'].split('_')[-1])
                            val = \
                                f'{wi_object["correct_value"]}_b' \
                                f'{"{:02d}".format(sample_count)}'
                        else:
                            val = wi_object['correct_value']
                    else:
                        val = wi_object['value']
    elif isinstance(wi_object, list):
        return parse_list_part(wi_object, factors, organism, id, nom)

    return val

def parse_list_part(wi_object, factors, organism, id, nom):
    """
    This function parses a part of the wi object of type list into the yaml
    structure.
    :param wi_object: the part of the wi object
    :param factors: the selected experimental factors
    :param organism: the selected organism
    :param id: the project id
    :param nom: the number of measurements
    :return: res: the parsed part in yaml structure
    """
    res = {}
    for i in range(len(wi_object)):
        if wi_object[i]['position'].split(':')[
                -1] == 'organism':
            organism = wi_object[i]['value'].split(' ')[0]
            val = {'organism_name': wi_object[i]['value'].split(' ')[0],
                               'taxonomy_id': wi_object[i]['value'].split(' ')[1]}
        else:
            val = parse_part(wi_object[i], factors, organism, id, nom)
        if wi_object[i]['position'].split(':')[-1] == 'technical_replicates':
            sample_name = []
            for c in range(val['count']):
                for m in range(nom):
                    sample_name.append(f'{id}_{organism}_'
                                       f'{res["sample_name"]}'
                                       f'_t{"{:02d}".format(c+1)}_'
                                       f'm{"{:02d}".format(m+1)}')
            val['sample_name'] = sample_name
        elif wi_object[i]['position'].split(':')[-1] == 'experimental_factors':
            key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
            for r in range(len(factors)):
                infos = list(utils.find_keys(key_yaml, factors[r]['factor']))

                if 'whitelist_keys' in factors[r]:
                    w_keys = factors[r]['whitelist_keys']
                    factors[r].pop('whitelist_keys')
                    if 'headers' in factors[r]:
                        headers = factors[r]['headers']
                        factors[r].pop('headers')
                    else:
                        headers = None
                    for j in range(len(factors[r]['values'])):
                        for k in w_keys:
                            if factors[r]['values'][j].endswith(f' ({k})'):
                                factors[r]['values'][j] = factors[r]['values'][j].replace(f' ({k})', '')
                                if headers is not None and k in headers:
                                    new_val = {}
                                    for l in range(len(headers[k].split(' '))):
                                        new_val[headers[k].split(' ')[l]] = factors[r]['values'][j].split(' ')[l]
                                    factors[r]['values'][j] = new_val
                                break
                elif 'headers' in factors[r]:
                    headers = factors[r]['headers']
                    factors[r].pop('headers')
                    for j in range(len(factors[r]['values'])):
                        new_val = {}
                        for l in range(len(headers.split(' '))):
                            new_val[headers.split(' ')[l]] = factors[r]['values'][j].split(' ')[l]
                        factors[r]['values'][j] = new_val
                elif len(infos) > 0 and isinstance(infos[0]['value'], dict) and len(infos[0]['value']) == 2 and 'unit' in infos[0]['value'] and 'value' in infos[0]['value']:
                    for j in range(len(factors[r]['values'])):
                        unit = factors[r]['values'][j].lstrip('0123456789')
                        value = int(factors[r]['values'][j][:len(factors[r]['values'][j]) - len(unit)])
                        factors[r]['values'][j] = {'unit': unit, 'value': value}
                elif len(factors[r]['values']) == 1 and isinstance(factors[r]['values'][0], dict):
                    if all(x in [factors[r]['factor'], 'multi'] for x in list(factors[r]['values'][0].keys())):
                        factors[r]['values'] = factors[r]['values'][0][factors[r]['factor']]
                    else:
                        factors[r]['values'] = factors[r]['values'][0]
                        remove = []
                        for elem in factors[r]['values']:
                            if factors[r]['values'][elem] == None or elem == 'multi' or ((isinstance(factors[r]['values'][elem], list) or isinstance(factors[r]['values'][elem], dict)) and len(factors[r]['values'][elem]) == 0):
                                remove.append(elem)
                        for elem in remove:
                            factors[r]['values'].pop(elem)

            res[wi_object[i]['position'].split(':')[-1]] = factors

        if type(val) == bool or type(val) == int or (
                val is not None and len(val) > 0):
            res[wi_object[i]['position'].split(':')[-1]] = val
    return res
