import src.utils as utils
import src.validate_yaml as validate_yaml
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
        if not 'list' in wi_object:
            print(wi_object)
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
