import src.validate_yaml as validate_yaml
import src.web_interface.wi_utils as wi_utils
import src.web_interface.wi_object_to_yaml as oty
import src.utils as utils

# TODO: rewrite and documentation


def validate_object(wi_object, key_yaml, read_in_whitelists, finish):
    """
    This function performs a validation over the wi object
    :param wi_object: the filled wi object
    :return: validation_object: the validated wi object with errors and
                                warnings
    """
    pooled = None
    organisms = []
    settings = []
    for setting in wi_object['experimental_setting']['list_value']:
        for elem in setting:
            if elem['position'].split(':')[-1] == 'organism':
                if isinstance(elem['value'], dict):
                    organisms.append(elem['value']['organism_name'].split(
                        ' ')[0])
                else:
                    organisms.append(elem['value'].split(' ')[0])
            elif elem['position'].split(':')[-1] == 'setting_id':
                settings.append(elem['value'])
    warnings = {}
    errors = {}

    for part in ['project', 'experimental_setting', 'technical_details']:

        part, wi_object[part], pooled, organisms, warnings[part], \
                errors[part] = validate_part(part, wi_object[part], [], pooled,
                                             organisms, settings, [])

    if finish:
        parsed = oty.parse_object(wi_object, key_yaml, read_in_whitelists)
        for part in ['project', 'experimental_setting', 'technical_details']:
            if part not in parsed:
                parsed[part] = {}
            valid, missing_mandatory_keys, invalid_keys, invalid_entries, \
            invalid_value, logical_warn = validate_yaml.validate_file(parsed[part], key_yaml[part]['value'], 'metadata', logical_validation=False, generated=False, only_mandatory=True)
            for elem in missing_mandatory_keys:
                diaplay_name = list(utils.find_keys(key_yaml, elem.split(':')[-1]))[0]['display_name']
                errors[part].append({'position': f'{part}:{elem}',
                                     'title': f'Missing {diaplay_name}',
                                     'message': 'Missing mandatory input'})
    validation_object = {'object': wi_object, 'errors': errors,
                         'warnings': warnings}
    return validation_object


def validate_part(elem, wi_object, warnings, pooled, organisms, settings, errors):
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
            if wi_object['position'].split(':')[-1] == 'techniques':
                tech_settings = []
                for t_elem in wi_object['list_value']:
                    for t_sub_elem in t_elem:
                        if t_sub_elem['position'].split(':')[-1] == 'setting':
                            tech_settings.append(t_sub_elem['value'])
                warning, warn_text = validate_yaml.validate_techniques(settings, tech_settings)
                if warning:
                    warnings.append({'position': wi_object['position'],
                                     'title': 'Invalid Technique',
                                     'message': warn_text})

                    warn_text = warn_text.replace('\n', '<br>')
                    warning_desc = \
                        f'{warning_desc}' \
                        f'{"<br>" if warning_desc != "" else ""}' \
                        f'<font color="orange">{warn_text}</font>'
                    wi_object['desc'] =  \
                        f'{wi_object["backup_desc"]}' \
                        f'{"<br>" if wi_object["backup_desc"] != "" else ""}' \
                        f'{warning_desc}'
                else:
                    wi_object['desc'] = wi_object['backup_desc']
            elif not any([isinstance(x, dict) or isinstance(x, list) for x in
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
                        errors.append({'position': wi_object['position'],
                                       'title': f'Invalid {wi_object["displayName"]}',
                                       'message': message})
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
                        organisms, settings, errors)
        else:
            if 'input_fields' in wi_object:
                elem, wi_object[
                    'input_fields'], pooled, organisms, warnings, errors = \
                    validate_part(
                        elem, wi_object['input_fields'], warnings, pooled,
                        organisms, settings, errors)
            else:
                if wi_object['value'] is not None and wi_object['value'] != '':
                    if wi_object['input_type'] == 'date':
                        value = wi_utils.date_to_str(wi_object['value'])
                    else:
                        value = wi_object['value']
                    valid, message = validate_yaml.validate_value(
                        value, wi_object['input_type'],
                        wi_object['position'].split(':')[-1])
                    wi_object['error'] = not valid
                    if not valid:
                        errors.append({'position': wi_object["position"],
                                       'title': f'Invalid {wi_object["displayName"]}',
                                       'message': message})
                        error_desc = f'{error_desc}' \
                                     f'{"<br>" if error_desc != "" else ""}' \
                                     f'<font color="red">{message}</font>'
                    warning = False
                    warn_text = None
                    warn_title = ''
                    key = wi_object['position'].split(':')[-1]
                    if key == 'pooled':
                        pooled = wi_object['value']
                    elif key == 'donor_count':
                        warning, warn_text = \
                            validate_yaml.validate_donor_count(
                                pooled, wi_object['value'])
                        warn_title = 'Illogical donor count'
                    elif key == 'organism':
                        organisms.append(wi_object['value'].split(' ')[0])
                    elif key == 'reference_genome':
                        warning, warn_text = \
                            validate_yaml.validate_reference_genome(
                                organisms, wi_object['value'])
                        warn_title = 'Illogical reference genome'
                    wi_object['warning'] = warning
                    if warning:
                        warnings.append({'position': wi_object["position"],
                                         'title': warn_title,
                                         'message': warn_text})
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
                elem, wi_object[i], warnings, pooled, organisms, settings, errors)
    return elem, wi_object, pooled, organisms, warnings, errors
