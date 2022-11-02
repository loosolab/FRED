import src.utils as utils
import src.validate_yaml as validate_yaml
import src.wi_functions as wi_functions
from dateutil import parser
import pytz
import os


# This script contains all functions that are called in parallel for the web
# interface.

def read_gene_whitelist(path):
    """
    This function reads the whitelist for the genes of an organism and
    separates the values into gene name and ensembl id. It is called for all
    organisms at the same time.
    :param path: the path to the gene whitelist file of one organism
    :return: gene_name: a list containing all gene names
             ensembl_id: a list containing all ensembl_ids
    """
    gene_name = []
    ensembl_id = []
    sublist = utils.read_whitelist(path)['whitelist']
    for elem in sublist:
        gene_name.append(elem.split(' ')[0])
        ensembl_id.append(elem.split(' ')[1])
    return gene_name, ensembl_id


def validate_part(elem, wi_object, warnings, pooled, organisms, errors):
    """
    This function is used to validate a part of the WI object. If an error or a
    warning is found than it is added to the description of the key whose value
    contains the error/warning. This function is called simultaneously for the
    parts 'project', 'experimental_setting' and 'technical_details'.
    :param elem: the key of the part that is being validated
    :param wi_object: the object that is validated
    :param warnings: a list containing all warnings
    :param pooled: a boolean that states if the samples were pooled
    :param organisms: a list of all contained organisms
    :param errors: a list containing all errors
    :return: elem: the key of the part that is being validated
             wi_object: the validated object containing error and warn messages
             pooled: a boolean stating if the samples are pooled
             organisms: a list of all contained organisms
             warnings: a list containing all found warnings
             errors: a list containing all found errors
    """
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
                for sub_elem in wi_object['list_value']:
                    valid, message = validate_yaml.validate_value(
                        sub_elem, wi_object['input_type'],
                        wi_object['position'].split(':')[-1])
                    if not valid:
                        error = True
                        messages.append((sub_elem, message))
                        errors.append(
                            f'{wi_object["position"]}: Value {sub_elem} - '
                            f'{message}')

                wi_object['error'] = error
                if error:
                    message = ', '.join(
                        [f'{msg[0]}: {msg[1]}' for msg in messages])
                    error_desc = f'{error_desc}' \
                                 f'{"<br>" if error_desc != "" else ""}' \
                                 f'<font color="red">{message}</font>'
                wi_object['desc'] = \
                    f'{wi_object["backup_desc"]}' \
                    f'{"<br>" if wi_object["backup_desc"] != "" else ""}' \
                    f'{error_desc}{"<br>" if error_desc != "" else ""}' \
                    f'{warning_desc}'
            else:
                elem, wi_object[
                    'list_value'], pooled, organisms, warnings, errors = \
                    validate_part(
                        elem, wi_object['list_value'], warnings, pooled,
                        organisms, errors)
        else:
            if 'input_fields' in wi_object:
                elem, wi_object[
                    'input_fields'], pooled, organisms, warnings, errors = \
                    validate_part(
                        elem, wi_object['input_fields'], warnings, pooled,
                        organisms, errors)
            else:
                if wi_object['value'] is not None and wi_object['value'] != '':
                    if wi_object['input_type'] == 'date':
                        default_time = parser.parse(wi_object['value'])
                        timezone = pytz.timezone("Europe/Berlin")
                        local_time = default_time.astimezone(timezone)
                        value = local_time.strftime("%d.%m.%Y")
                    else:
                        value = wi_object['value']
                    valid, message = validate_yaml.validate_value(
                        value, wi_object['input_type'],
                        wi_object['position'].split(':')[-1])
                    wi_object['error'] = not valid
                    if not valid:
                        errors.append(f'{wi_object["position"]}: {message}')
                        error_desc = f'{error_desc}' \
                                     f'{"<br>" if error_desc != "" else ""}' \
                                     f'<font color="red">{message}</font>'
                    warning = False
                    warn_text = None
                    key = wi_object['position'].split(':')[-1]
                    if key == 'pooled':
                        pooled = wi_object['value']
                    elif key == 'donor_count':
                        warning, warn_text = \
                            validate_yaml.validate_donor_count(
                                pooled, wi_object['value'])
                    elif key == 'organism':
                        organisms.append(wi_object['value'].split(' ')[0])
                    elif key == 'reference_genome':
                        warning, warn_text = \
                            validate_yaml.validate_reference_genome(
                                organisms, wi_object['value'])
                    wi_object['warning'] = warning
                    if warning:
                        warnings.append(
                            f'{wi_object["position"]}: {warn_text}')
                        warning_desc = \
                            f'{warning_desc}' \
                            f'{"<br>" if warning_desc != "" else ""}' \
                            f'<font color="orange">{warn_text}</font>'
                    wi_object['desc'] = \
                        f'{wi_object["backup_desc"]}' \
                        f'{"<br>" if wi_object["backup_desc"] != "" else ""}' \
                        f'{error_desc}{"<br>" if error_desc != "" else ""}' \
                        f'{warning_desc}'
    elif isinstance(wi_object, list):
        for i in range(len(wi_object)):
            elem, wi_object[
                i], pooled, organisms, warnings, errors = validate_part(
                elem, wi_object[i], warnings, pooled, organisms, errors)
    return elem, wi_object, pooled, organisms, warnings, errors


def parse_part(wi_object, factors, organism, id, nom):
    gn = None
    embl = None
    key_yaml = utils.read_in_yaml(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        'keys.yaml'))
    if 'input_type' in wi_object and wi_object['input_type'] == 'gene':
        if wi_object['value'] is not None:
            gn, embl = wi_object['value'].split(' ')
        sub_keys = \
            list(utils.find_keys(
                key_yaml,
                wi_object['position'].split(':')[-1]))[0]['value'].keys()
        new_samp = {'position': wi_object['position'],
                    'mandatory': wi_object['mandatory'],
                    'list': wi_object['list'],
                    'title': wi_object['displayName'],
                    'desc': wi_object['desc']}
        input_fields = []
        for key in sub_keys:
            node = list(utils.find_keys(key_yaml, key))[0]
            input_field = wi_functions.parse_empty(
                node, f'{wi_object["position"]}:{key}', key_yaml, False)
            if gn is not None and embl is not None:
                input_field['value'] = gn if key == 'gene_name' else embl
            input_fields.append(input_field)
        for elem in factors:
            for i in range(len(elem)):
                if 'headers' in elem[i] and elem[i]['factor'] == \
                        wi_object['position'].split(':')[-1] and \
                        wi_object['value'] is not None:
                    for j in range(len(elem[i]['headers'].split(' '))):
                        for f in input_fields:
                            if f['position'].split(':')[-1] == \
                                    elem[i]['headers'].split(' ')[j]:
                                f['value'] = wi_object['value'].split(' ')[j]
        new_samp['input_fields'] = input_fields
        wi_object = new_samp

    if isinstance(wi_object, dict):
        if wi_object['position'].split(':')[-1] == 'experimental_setting':
            if len(wi_object['list_value']) > 0:
                organism = [o['value'] for o in wi_object['list_value'][0] if
                            o['position'].split(':')[-1] == 'organism']
                if len(organism) > 0:
                    organism = organism[0].split(' ')[0]
                else:
                    organism = None
            else:
                organism = None
        if wi_object['list']:
            val = []
            for elem in wi_object['list_value']:
                if isinstance(elem, dict):
                    if elem['position'].split(':')[-1] == 'condition':
                        samples = []
                        for sub_elem in elem['list_value']:
                            nom = [x['value'] for x in sub_elem if
                                   x['position'].split(':')[
                                       -1] == 'number_of_measurements'][0]
                            part_val = parse_part(sub_elem, factors, organism,
                                                  id, nom)
                            samples.append(part_val)

                        val.append({'condition_name': elem['correct_value'],
                                    'biological_replicates': {
                                        'count': len(samples),
                                        'samples': samples}})
                elif isinstance(elem, list):
                    val.append(
                        parse_list_part(elem, factors, organism, id, nom))
                else:
                    val.append(elem)
        else:
            if 'whitelist' in wi_object and wi_object[
                    'whitelist'] and 'headers' in wi_object['whitelist']:
                new_obj = {'position': wi_object['position'],
                           'mandatory': wi_object['mandatory'],
                           'list': wi_object['list'],
                           'title': wi_object['displayName'],
                           'desc': wi_object['desc']}
                input_fields = []
                for j in range(
                        len(wi_object['whitelist']['headers'].split(' '))):
                    node = list(utils.find_keys(key_yaml,
                                                wi_object['whitelist'][
                                                    'headers'].split(' ')[j]))[
                        0]
                    input_fields.append(wi_functions.parse_empty(
                        node,
                        f'{wi_object["position"]}:'
                        f'{wi_object["whitelist"]["headers"].split(" ")[j]}',
                        key_yaml, False))
                    input_fields[j]['value'] = wi_object['value'].split(' ')[j]
                new_obj['input_fields'] = input_fields
                wi_object = new_obj
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
                        if wi_object['position'].split(':')[
                                -1] == 'sample_name':
                            sample_count = int(
                                wi_object['value'].split('_')[-1])
                            val = f'{wi_object["correct_value"]}_b' \
                                  f'{"{:02d}".format(sample_count)}'
                        else:
                            val = wi_object['correct_value']
                    else:
                        val = wi_object['value']
    elif isinstance(wi_object, list):
        return parse_list_part(wi_object, factors, organism, id, nom)
    return val
