import os.path
import datetime
from src import utils


# This script includes functions for the validation of metadata yaml files

# ---------------------------------VALIDATION-----------------------------------

generated = ['condition_name', 'sample_name']
factor = None


def validate_file(metafile, key_yaml, mode, logical_validation=True, yaml=None, generated=True, whitelist_path=None):
    """
    In this function all functions for the validation of a metadata file are
    called. The validation is based on the data in the file 'keys.yaml'. It is
    tested if all mandatory keys are included, if the included keys are valid
    and if the entered values correspond to the whitelist.
    :param metafile: the read in metadata yaml file
    :return:
    valid: bool, true if the file is valid, false if it is invalid
    missing_mandatory_keys: a list containing the missing mandatory keys
    invalid_keys: a list containing the invalid keys
    invalid_entries: a list containing the invalid entries -> (key, [values])
    """
    logical_warn = []
    valid = True

    invalid_keys, invalid_entries, invalid_value = \
        new_test(metafile, key_yaml, [], '', [], [], [], None, [], None, metafile, key_yaml, whitelist_path=whitelist_path, mode=mode)
    missing_mandatory_keys = test_for_mandatory(metafile, key_yaml,
                                                [x.split(':')[-1] for x in
                                                 invalid_keys], generated)
    if len(missing_mandatory_keys) > 0 or len(invalid_keys) > 0 or len(
            invalid_entries) > 0 or len(invalid_value) > 0:
        valid = False
    if logical_validation:
        logical_warn = validate_logic(metafile, mode)
    return valid, missing_mandatory_keys, invalid_keys, invalid_entries, \
        invalid_value, logical_warn


# -----------------------------------REPORT-------------------------------------


def print_full_report(metafile, errors, warnings, size=80):
    report = ''
    try:
        input_id = metafile['project']['id']
    except KeyError:
        input_id = 'missing'
    try:
        path = metafile['path']
    except KeyError:
        path = 'missing'
    report += f'{"VALIDATION REPORT".center(size, "-")}\n' \
              f'Project ID: {input_id}\n' \
              f'Path: {path}\n\n' \

    if errors is not None:
        report += f'{print_validation_report(errors[0], errors[1], errors[2], errors[3], size)}\n'
    if warnings is not None:
        report += f'{print_warning(warnings,size)}\n'
    return report


def print_validation_report(missing_mandatory_keys, invalid_keys,
                            invalid_values, invalid_value, size=80):
    """
    This function outputs a report on invalid files. The report contains the ID
     of the project, the path to the file, as well as the missing mandatory
     keys, invalid keys and invalid entries.
    :param invalid_value: a list containing invalid values
    :param metafile: the metafile that is validated
    :param missing_mandatory_keys: a list containing all missing mandatory keys
    :param invalid_keys: a list containing all invalid keys
    :param invalid_values: a list containing all invalid values
    """
    invalid_entries = '\n- '.join(invalid_keys)
    missing = '\n- '.join(missing_mandatory_keys)
    whitelist_values = []
    for v in invalid_values:
        key = ':'.join(v.split(':')[:-1])
        entry = v.split(':')[-1]
        whitelist_values.append(entry + ' in ' + key + '\n')
    value = []
    for v in invalid_value:
        value.append(f'{v[0]}: {v[1]} -> {v[2]}')
    report = ''
    report += f'{"ERROR".center(size, "-")}\n\n'
    if len(invalid_keys) > 0:
        report += f'The following keys were invalid:\n'\
                  f'- {invalid_entries}\n'
    if len(missing_mandatory_keys) > 0:
        report += f'The following mandatory keys were missing:\n' \
                  f'- {missing}\n'
    if len(invalid_values) > 0:
        report += f'The following values do not match the whitelist:\n' \
                  f'- {"- ".join(whitelist_values)}\n'
    if len(invalid_value) > 0:
        report += f'The following values are invalid:\n' \
                  f'- {"- ".join(value)}\n'
    return report


def print_warning(logical_warn, size=80):
    """
    This function prints a warning message.
    :param metafile: the metafile that contains the warning
    :param pool_warn: a list of warnings concerning pooled and donor_count
    :param ref_genome_warn: a list of warnings concerning the reference_genome
    """

    report = ''
    report += f'{"WARNING".center(size, "-")}\n\n'
    if len(logical_warn) > 0:
        for elem in logical_warn:
            report += f'- {elem[0]}:\n{elem[1]}\n'
    #if len(pool_warn) > 0:
    #    for elem in pool_warn:
    #        print(f'- Sample \'{elem[0]}\':\n{elem[1]}')
    #if len(ref_genome_warn) > 0:
    #    for elem in ref_genome_warn:
    #        print(f'- Run from {elem[0]}:\n{elem[1]}')
    return report

# --------------------------------UTILITIES------------------------------------

def new_test(metafile, key_yaml, sub_lists, key_name, invalid_keys,
             invalid_entry, invalid_value, input_type, is_factor,
             local_factor, full_metadata, full_yaml, whitelist_path=None, mode='metadata'):
    """
    This function test if all keys in the metadata file are valid.
    :param metafile: the metadata file
    :param key_yaml: the read in keys.yaml
    :param sub_lists: a list to save all items within a key if it has a list as
                      value
    :param key_name: the name of the key that is tested
    :param invalid_keys: a list of all invalid keys
    :param invalid_entry: a list of all invalid entries
    :param invalid_value: a list of all invalid values
    :param input_type: the input type that is expected for the value
    :param is_factor: a bool to state if the key is an experimental factor
    :param local_factor: a parameter to save the current experimental factor
    :return:
    invalid_keys: a list containing the invalid keys
    invalid_entries: a list containing the invalid entries
    invalid_value: a list containing the invalid values
    """
    if isinstance(metafile, dict) and not (
            'value' in metafile and 'unit' in metafile):
        for key in metafile:
            if not key_yaml and key_name.split(':')[-1] in is_factor or (key_name.split(':')[-1] == 'values' and local_factor is not None):
                new_yaml1 = full_yaml
                if key_name.split(':')[-1] in is_factor:
                    new_yaml = list(utils.find_keys(new_yaml1, key_name.split(':')[-1]))
                else:
                    new_yaml = list(utils.find_keys(new_yaml1, local_factor))
                if len(new_yaml) > 0:
                    if 'whitelist' in new_yaml[0] and new_yaml[0]['whitelist']:
                        if key_name.split(':')[-1] in is_factor:
                            w = utils.get_whitelist(key_name.split(':')[-1],
                                                    full_metadata, whitelist_path=whitelist_path)
                        else:
                            w = utils.get_whitelist(local_factor, full_metadata, whitelist_path=whitelist_path)
                        if w and 'headers' in w:
                            if isinstance(w['headers'], dict):
                                if 'whitelist_keys' in w:
                                    headers = []
                                    for w_k in w['whitelist_keys']:
                                        if w_k in w['headers']:
                                            headers += w['headers'][w_k].split(' ')
                            else:
                                headers = w['headers'].split(' ')
                            new_yaml[0]['value'] = headers
                    if key not in new_yaml[0]['value']:
                        invalid_keys.append(f'{key_name}:{key}')
                    elif isinstance(metafile[key], list) != new_yaml[0]['list']:
                        invalid_keys.append(f'{key_name}:{key}')
                else:
                    invalid_keys.append(f'{key_name}:{key}')
            elif not key_yaml or (key_yaml and key not in key_yaml):
                invalid_keys.append(f'{key_name}:{key}')
            else:
                print(key, key_yaml, metafile)
                if key == 'factor':
                    global factor
                    factor = metafile[key]
                    local_factor = metafile[key]
                    is_factor.append(metafile[key])
                input_type = None
                if key == 'values' and factor is not None:
                    node = list(utils.find_keys(key_yaml, factor))
                    if len(node) > 0:
                        if 'input_type' in node:
                            input_type = node['input_type']
                elif isinstance(metafile[key], list) != key_yaml[key]['list']:
                    invalid_keys.append(f'{key_name}:{key}')
                elif 'input_type' in key_yaml[key]:
                    input_type = key_yaml[key]['input_type']
                res_keys, res_entries, res_values = new_test(
                    metafile[key], key_yaml[key]['value'], sub_lists,
                    f'{key_name}:{key}' if key_name != '' else key,
                    invalid_keys, invalid_entry, invalid_value, input_type,
                    is_factor, local_factor, full_metadata, full_yaml, whitelist_path=whitelist_path, mode=mode)
                invalid_keys = res_keys
    elif isinstance(metafile, list):
        for item in metafile:
            sub_lists.append(item)
            res_keys, res_entries, res_values = new_test(
                item, key_yaml, sub_lists, key_name, invalid_keys,
                invalid_entry, invalid_value, input_type, is_factor,
                local_factor, full_metadata, full_yaml, whitelist_path=whitelist_path, mode=mode)
            invalid_keys = res_keys
            sub_lists = sub_lists[:-1]
    else:
        #TODO: Value unitb + check for whitelist but fast
        #has_whitelist = list(utils.find_keys(utils.read_in_yaml(key_yaml_path), key_name.split(':')[-1]))
        #if len(has_whitelist) > 0 and 'whitelist' in has_whitelist[0]:
            #has_whitelist = True
        #else:
            #has_whitelist = False
        invalid = new_test_for_whitelist(key_name.split(':')[-1], metafile,
                                         sub_lists, whitelist_path=whitelist_path)
        if invalid:
            invalid_entry.append(f'{key_name}:{metafile}')

        inv_value, message = validate_value(metafile, input_type,
                                            key_name.split(':')[-1], mode=mode)

        if not inv_value:
            invalid_value.append((key_name, metafile, message))

    return invalid_keys, invalid_entry, invalid_value


def new_test_for_whitelist(entry_key, entry_value, sublists, whitelist_path=None):
    """
    This function tests if the value of a key matches the whitelist.
    :param entry_key: the key that is tested
    :param entry_value: the value that has to match the whitelist
    :param sublists: a list to save all items within a key if it has a list as
                      value
    :return: True if the entry does not match the whitelist else False
    """
    if entry_value == None:
        entry_value = 'None'
    if whitelist_path == None:
        whitelist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            'metadata_whitelists')

    whitelist = utils.read_whitelist(entry_key, whitelist_path=whitelist_path)
    if whitelist and whitelist['whitelist_type'] == 'plain':
        whitelist = whitelist['whitelist']
    if isinstance(whitelist, dict):
        while isinstance(whitelist, dict) and whitelist[
                'whitelist_type'] == 'depend':
            whitelist_key = whitelist['ident_key']
            for i in reversed(range(len(sublists))):

                value = list(utils.find_keys(sublists[i], whitelist_key))

                if len(value) > 0:
                    if len(value) == 1:
                        break
                    else:
                        print("ERROR: multiple values")
                        break

            if value[0] in whitelist:
                whitelist = whitelist[value[0]]
            else:
                whitelist = utils.read_whitelist(value[0], whitelist_path=whitelist_path)
                if whitelist and whitelist['whitelist_type'] == 'plain':
                    whitelist = whitelist['whitelist']
        if isinstance(whitelist, dict) and whitelist[
                'whitelist_type'] == 'group':
            #TODO: linked whitelists
            whitelist = utils.read_grouped_whitelist(whitelist, {})
            whitelist = [x for xs in list(whitelist['whitelist'].values())
                         if xs is not None for x in xs]
    if whitelist and not isinstance(whitelist, list) and not isinstance(
            whitelist, dict) \
            and os.path.isfile(os.path.join(
            whitelist_path, 'whitelists', whitelist)):
        whitelist = utils.read_whitelist(whitelist, whitelist_path=whitelist_path)
        if whitelist:
            whitelist = whitelist['whitelist']
    if whitelist and entry_value not in whitelist:
        return True
    return False


def test_for_mandatory(metafile, key_yaml, invalid_keys, generated):
    """
    This function calls a function to get the missing mandatory keys for every 
    part of the metadata object.
    :param metafile: the read in metadata yaml file
    :param key_yaml: the read in structure file 'keys.yaml'
    :param invalid_keys: a list of keys that are invalid and should be ignored
    :return: missing_keys: a list containing the missing mandatory keys
    """
    missing_keys = []
    for key in key_yaml:
        missing_keys += get_missing_keys(key_yaml[key], metafile,
                                         invalid_keys, key, [], len(metafile[key]) if key in metafile and key_yaml[key]['list'] else 1, generated)
    return missing_keys


def get_missing_keys(node, metafile, invalid_keys, pre, missing, list_len, generated):
    """
    This function tests if all mandatory keys from the structure file
    'keys.yaml' are present in the metadata file.
    :param node: a key within the read in structure file 'keys.yaml'
    :param metafile: the read in metadata file
    :param invalid_keys: a list containing invalid keys that should be ignored
    :param pre: a string to save and chain keys in order to save their position
    :param missing: a list to save the missing mandatory keys
    """

    metafile = find_key(metafile, pre)

    if len(metafile) == 0:
        if node['mandatory'] and (('special_case' in node and 'generated' in node['special_case'] and node['special_case']['generated'] == 'end' and generated) or not ('special_case' in node and 'generated' in node['special_case'] and node['special_case']['generated'] == 'end')):
            missing.append(pre)
    else:
         if pre.split(':')[-1] not in invalid_keys:
            if isinstance(node['value'], dict) and not set(['mandatory', 'list',
                                                    'desc', 'display_name',
                                                    'value']) <= \
            set(node['value'].keys()):
                if isinstance(metafile[0], list):
                    for elem in metafile[0]:
                        for key in node['value']:
                            missing = get_missing_keys(node['value'][key], elem,
                                           invalid_keys, pre + ':' + key,
                                           missing, len(metafile[0]) if node['list'] else 1, generated)
                else:
                    for key in node['value']:
                        missing = get_missing_keys(node['value'][key], metafile[0],
                                                   invalid_keys,
                                                   pre + ':' + key,
                                                   missing,
                                                   len(metafile[0]) if node[
                                                       'list'] else 1, generated)
    return list(set(missing))


def find_key(metafile, key):
    """
    This function searches for a key of the keys.yaml in the metafile.
    :param metafile: the read in metadata file
    :param key: a string of chained keys (key1:key2...)
    :param is_list: bool, true if the instance in the structure is a list
    :param values: the default entry for the key within the structure file
    :param invalid_keys: a list containing invalid keys that should be ignored
    :return: missing_keys: a list containing the missing mandatory keys
    """
    for k in key.split(':'):
        new_metafile = list(utils.find_keys(metafile, k))
    return new_metafile


def validate_value(input_value, value_type, key, mode='metadata'):
    """
    This function tests if an entered value matches its type and contains
    invalid characters.
    :param input_value: the value to be valiated
    :param value_type: the type of which the value should be
    :param key: the key that contains the value
    :return:
    valid: a boolean that states if the value is valid
    message: a string that contains information about the error if tha value
             is invalid
    """
    valid = True
    message = None
    if input_value is not None:
        if value_type == 'bool':
            if input_value not in [True, False]:
                valid = False
                message = 'The value has to be of type bool (True or False).'
        elif value_type == 'number':
            if not isinstance(input_value, int):
                valid = False
                message = 'The value has to be an integer.'
        elif value_type == 'date':
            try:
                if mode == 'metadata':
                    input_date = input_value.split('.')
                    date_message = f'Input must be of type \'DD.MM.YYYY\'.'
                elif mode == 'mamplan':
                    input_date = input_value.split('/')
                    date_message = f'Input must be of type \'DD/MM/YYYY\'.'
                if len(input_date) != 3 or len(input_date[0]) != 2 or len(
                        input_date[1]) != 2 or not ((mode == 'mamplan' and len(input_date[2]) == 2) or len(input_date[2]) == 4):
                    raise SyntaxError
                input_value = datetime.date(int(input_date[2]),
                                            int(input_date[1]),
                                            int(input_date[0]))
            except (IndexError, ValueError, SyntaxError) as e:
                valid = False
                message = date_message
        elif type(input_value) == str and ('\"' in input_value or '{' in input_value or '}' in
                 input_value or '|' in input_value) and key not in generated:
            if mode != 'mamplan':
                valid = False
                message = 'The value contains an invalid character ' \
                          '(\", {, } or |).'
    return valid, message


def validate_logic(metafile, mode='metadata'):
    """
    This functions tests the logic of the input data.
    :param metafile: the metafile to be validated
    :return:
    pool_warn: a list containing warnings about the donor_count and pooled
    ref_genome_warn: a list containing warnings about the reference genome
    """
    logical_warn = []

    if mode == 'metadata':
        techniques = list(utils.find_keys(metafile, 'setting'))
        setting_ids = list(utils.find_keys(metafile, 'setting_id'))
        warning, warn_message = validate_techniques(setting_ids, techniques)
        if warning:
            logical_warn.append((f'Invalid techniques:', warn_message))
        invalid_file, invalid_sample, file_message, sample_message = validate_filenames(metafile)
        print(invalid_file, invalid_sample)
        if invalid_file:
            logical_warn.append((f'Invalid number of filenames:', file_message))
        if invalid_sample:
            logical_warn.append((f'Invalid number of sample names:', sample_message))
        samples = list(utils.find_keys(metafile, 'samples'))
        for cond in samples:
            for sample in cond:
                if isinstance(sample, dict) and 'pooled' in sample and 'donor_count' in sample:
                    warning, warn_message = validate_donor_count(sample['pooled'],
                                                                 sample['donor_count'])
                    if warning:
                        logical_warn.append((f'Sample \'{sample["sample_name"]}\'', warn_message))
        organisms = list(utils.find_keys(metafile, 'organism_name'))
        runs = list(utils.find_keys(metafile, 'runs'))
        if len(runs) > 0:
            for run in runs[0]:
                if 'reference_genome' in run:
                    warning, warn_message = validate_reference_genome(
                        organisms, run['reference_genome'])
                    if warning:
                        logical_warn.append((f'Run from {run["date"]}', warn_message))
    elif mode == 'mamplan':
        if 'tags' in metafile and 'organization' in metafile['tags'] and metafile['tags']['organization'] is not None:
            if 'public' in metafile['tags']['organization']:
                if 'pubmedid' not in metafile['tags'] or metafile['tags']['pubmedid'] is None:
                    logical_warn.append(('tags:pubmedid', 'The pubmed ID is missing for this public project'))
        if 'project' in metafile and 'id' in metafile['project'] and metafile['project']['id'] is not None and metafile['project']['id'] != metafile['project']['id'].lower():
            logical_warn.append(('project:id', 'The ID should be lowercase'))
    return logical_warn


def validate_filenames(metafile):
    invalid_file = False
    invalid_sample = False
    file_message = ''
    sample_message = ''
    technique = list(utils.find_keys(metafile, 'techniques'))
    if len(technique) > 0:
        techniques = {}
        for elem in technique[0]:
            techniques[elem['setting']] = elem['technique']
        print(techniques)
        settings = list(utils.find_keys(metafile, 'experimental_setting'))
        if len(settings) > 0:
            for setting in settings[0]:
                if 'setting_id' in setting and setting['setting_id'] in techniques:
                    used_techniques = techniques[setting['setting_id']]
                    samples = list(utils.find_keys(setting, 'samples'))
                    if len(samples) > 0:
                        for sample in samples[0]:
                            sample_name = sample['sample_name'] if 'sample_name' in sample else ''
                            m = sample['number_of_measurements'] if 'number_of_measurements' in sample else 0
                            t = sample['technical_replicates']['count'] if 'technical_replicates' in sample and 'count' in sample['technical_replicates'] else 0
                            tech = len(used_techniques)
                            file_count = m * t * tech
                            print('FC', file_count)
                            if file_count > 0:
                                if 'technical_replicates' in sample:
                                    if 'sample_name' in sample['technical_replicates']:
                                        if len(sample['technical_replicates']['sample_name']) != file_count:
                                            invalid_sample = True
                                            sample_message += f'Number of sample names ({len(sample["technical_replicates"]["sample_name"])}) for sample \'{sample_name}\' does not match expected number of sample names ({file_count})\n'
                                    if 'filenames' in sample['technical_replicates']:
                                        if len(sample['technical_replicates']['filenames']) != file_count:
                                            invalid_file = True
                                            file_message += f'Number of filenames ({len(sample["technical_replicates"]["sample_name"])}) for sample \'{sample_name}\' does not match expected number of filenames ({file_count})\n'
    return invalid_file, invalid_sample, file_message, sample_message


def validate_techniques(setting_ids, techniques):
    invalid = False
    message = None
    missing_technique = list(set(setting_ids)-set(techniques))
    unknown_techniques = list(set(techniques)- set(setting_ids))
    if len(missing_technique) > 0 or len(unknown_techniques) > 0:
        invalid = True
        message = ''
        if len(missing_technique) > 0:
            message += f'Techniques are missing for experimental setting ' \
                       f'{", ".join(missing_technique)}.'
        if len(unknown_techniques) > 0:
            message += f'Techniques were given for experimental setting ' \
                       f'{", ".join(unknown_techniques)} which was not ' \
                       f'defined.'
    return invalid, message


def validate_reference_genome(organisms, reference_genome):
    """
    This function tests if the reference genome matches the organism.
    :param organisms: a list of all organisms in the metadata file
    :param reference_genome: the reference genome that was specified
    :return:
    invalid: boolean to state if the reference genome is invalid
    message: a string explaining the logical error
    """
    invalid = False
    message = None
    ref_genome_whitelist = utils.get_whitelist('reference_genome', None)
    if ref_genome_whitelist:
        if not(any(organism in ref_genome_whitelist['whitelist'] for organism in organisms)) or not any([reference_genome in ref_genome_whitelist['whitelist'][organism] for
                    organism in organisms if organism in ref_genome_whitelist['whitelist']]):
            invalid = True
            organisms = [f'\'{organism}\'' for organism in organisms]
            message = (f'The reference genome \'{reference_genome}\' does not '
                       f'match the input organism ({", ".join(organisms)}).')
    return invalid, message


def validate_donor_count(pooled, donor_count):
    """
    This function tests if the donor_count matches the value stated for pooled.
    :param pooled: a boolean stating if a sample is pooled
    :param donor_count: the donor_count of a sample
    :return:
    invalid: boolean to state if the value is invalid
    message: a string explaining the logical error
    """
    invalid = False
    message = None
    if pooled in [True, 'True'] and donor_count <= 1:
        invalid = True
        message = (f'Found donor count {donor_count} for pooled sample. '
                   f'The donor count should be greater than 1.')
    elif pooled in [False, 'False'] and donor_count > 1:
        invalid = True
        message = (f'Found donor count {donor_count} for sample that is not '
                   f'pooled. The donor count should be 1.')
    return invalid, message
