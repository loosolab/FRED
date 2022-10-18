import src.utils as utils
import src.validate_yaml as validate_yaml
from dateutil import parser
import pytz
import os


def read_gene_whitelist(path):
    gene_name = []
    ensembl_id = []
    sublist = utils.read_whitelist(path)['whitelist']
    for elem in sublist:
        gene_name.append(elem.split(' ')[0])
        ensembl_id.append(elem.split(' ')[1])
    return gene_name, ensembl_id


def validate_part(elem, wi_object, warnings, pooled, organisms, errors):
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
                    valid, message = validate_yaml.validate_value(sub_elem,
                                                                  wi_object[
                                                                      'input_type'],
                                                                  wi_object[
                                                                      'position'].split(
                                                                      ':')[-1])
                    if not valid:
                        error = True
                        messages.append((sub_elem, message))
                        errors.append(
                            f'{wi_object["position"]}: Value {sub_elem} - {message}')
                wi_object['error'] = error
                if error:
                    message = ', '.join(
                        [f'{msg[0]}: {msg[1]}' for msg in messages])
                    error_desc = f'{error_desc}{"<br>" if error_desc != "" else ""}<font color="red">{message}</font>'
                wi_object[
                    'desc'] = f'{wi_object["backup_desc"]}{"<br>" if wi_object["backup_desc"] != "" else ""}{error_desc}{"<br>" if error_desc != "" else ""}{warning_desc}'
            else:
                elem, wi_object[
                    'list_value'], pooled, organisms, warnings, errors = validate_part(
                    elem, wi_object['list_value'], warnings, pooled, organisms,
                    errors)
        else:
            if 'input_fields' in wi_object:
                elem, wi_object[
                    'input_fields'], pooled, organisms, warnings, errors = validate_part(elem,
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
                                                                      'input_type'],
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
                        organisms.append(wi_object['value'].split(' ')[0])
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
            elem, wi_object[i], pooled, organisms, warnings, errors = validate_part(
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
        sub_keys = list(utils.find_keys(key_yaml, wi_object['position'].split(':')[-1]))[0]['value'].keys()
        new_samp = {'position': wi_object['position'],
                    'mandatory': wi_object['mandatory'],
                    'list': wi_object['list'],
                    'title': wi_object['displayName'],
                    'desc': wi_object['desc']}
        input_fields = []
        for key in sub_keys:
            node = list(utils.find_keys(key_yaml, key))[0]
            input_field = parse_empty(node, f'{wi_object["position"]}:{key}', key_yaml, False)
            if gn is not None and embl is not None:
                input_field['value'] = gn if key == 'gene_name' else embl
            input_fields.append(input_field)
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
                    for sub_elem in elem:
                        if sub_elem['position'].split(':')[-1] == 'number_of_measurements':
                            nom = sub_elem['value']
                    if all(sub_elem['position'].split(':')[-1] == wi_object['position'].split(':')[-1] for sub_elem in elem):
                        for sub_elem in elem:
                            test.append(sub_elem['value'])
                    else:
                        test.append(parse_part(elem, factors, organism, id, nom))
            return test
        else:
            if 'whitelist' in wi_object and wi_object['whitelist'] and 'headers' in wi_object['whitelist']:
                new_obj = {'position': wi_object['position'],
                            'mandatory': wi_object['mandatory'],
                            'list': wi_object['list'],
                            'title': wi_object['displayName'],
                            'desc': wi_object['desc']}
                input_fields = []
                for j in range(len(wi_object['whitelist']['headers'].split(' '))):
                    node = list(utils.find_keys(key_yaml, wi_object['whitelist']['headers'].split(' ')[j]))[0]
                    input_fields.append(parse_empty(node, f'{wi_object["position"]}:{wi_object["whitelist"]["headers"].split(" ")[j]}', key_yaml, False))
                    input_fields[j]['value'] = wi_object['value'].split(' ')[j]
                new_obj['input_fields'] = input_fields
                wi_object = new_obj
            if 'input_fields' in wi_object:
                return parse_part(wi_object['input_fields'], factors, organism, id, nom)
            else:
                if wi_object['value'] and wi_object[
                        'input_type'] == 'value_unit':
                    unit = wi_object['value_unit']
                    value = wi_object['value']
                    return {'unit': unit, 'value': value}
                else:
                    if 'correct_value' in wi_object:
                        if wi_object['position'].split(':')[-1] == 'sample_name':
                            sample_count = int(wi_object['value'].split('_')[-1])
                            return f'{wi_object["correct_value"]}_b{"{:02d}".format(sample_count)}'
                        return wi_object['correct_value']
                    else:
                        return wi_object['value']
    elif isinstance(wi_object, list):
        for i in range(len(wi_object)):
            if wi_object[i]['position'].split(':')[-1] == 'organism':
                organism = wi_object[i]['value'].split(' ')[0]

            if wi_object[i]['position'].split(':')[-1] == 'conditions':
                test = []
                for j in range(len(wi_object[i]['list_value'])):
                    value = parse_part(wi_object[i]['list_value'][j], factors, organism, id, nom)
                    if ((isinstance(value, list) or isinstance(value,
                                                               dict)) and len(
                        value) > 0) or (
                            not isinstance(value, list) and not isinstance(
                        value,
                        dict) and value is not None and value != ''):
                        test.append({'condition_name':
                                         wi_object[i]['list_value'][j][
                                             'correct_value'],
                                     'biological_replicates': {
                                         'count': len(value),
                                         'samples': value}})
                    else:
                        test.append({'condition_name':
                                         wi_object[i]['list_value'][j][
                                             'correct_value']})
                return_dict['conditions'] = test
            elif wi_object[i]['position'].split(':')[
                -1] == 'technical_replicates':
                technical_replicates = parse_part(wi_object[i], factors, organism, id, nom)
                sample_name = []
                for c in range(technical_replicates['count']):
                    for m in range(nom):
                        sample_name.append(
                            f'{id}_{organism}_{return_dict["sample_name"]}_t{"{:02d}".format(c+1)}_m{"{:02d}".format(m+1)}')
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
                                    if all(k == d['factor'] for k in d['values'][j]):
                                        d['values'] = d['values'][j][d['factor']]
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
                value = parse_part(wi_object[i], factors, organism, id, nom)
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