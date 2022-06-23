import os.path
import datetime
from src import utils


# This script includes functions for the validation of metadata yaml files

# ---------------------------------VALIDATION-----------------------------------


def validate_file(metafile):
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
    valid = True
    key_yaml = utils.read_in_yaml('keys.yaml')
    invalid_keys, invalid_entries, invalid_value = new_test(metafile, key_yaml, [], '', [],
                                             [], [], None)
    missing_mandatory_keys = test_for_mandatory(metafile, key_yaml,
                                                [x.split(':')[-1] for x in
                                                 invalid_keys])
    if len(missing_mandatory_keys) > 0 or len(invalid_keys) > 0 or len(
            invalid_entries) > 0 or len(invalid_value) > 0:
        valid = False
    return valid, missing_mandatory_keys, invalid_keys, invalid_entries, invalid_value


# -----------------------------------REPORT-------------------------------------


def print_validation_report(metafile, missing_mandatory_keys, invalid_keys,
                            invalid_values, invalid_value):
    """
    This function outputs a report on invalid files. The report contains the ID
     of the project, the path to the file, as well as the missing mandatory
     keys, invalid keys and invalid entries.
    :param metafile:
    :param missing_mandatory_keys:
    :param invalid_keys:
    :param invalid_values:
    """
    try:
        input_id = metafile['project']['id']
    except KeyError:
        input_id = 'missing'
    try:
        path = metafile['path']
    except KeyError:
        path = 'missing'
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
    print(f'{"INVALID FILE".center(80, "-")}\n'
          f'Project ID: {input_id}\n'
          f'Path: {path}\n\n'
          f'Report:\n')
    if len(invalid_keys) > 0:
        print(f'The following keys were invalid:\n'
              f'- {invalid_entries}\n')
    if len(missing_mandatory_keys) > 0:
        print(f'The following mandatory keys were missing:\n'
              f'- {missing}\n')
    if len(invalid_values) > 0:
        print(f'The following values do not match the whitelist:\n'
              f'- {"- ".join(whitelist_values)}')
    if len(invalid_value) > 0:
        print(f'The following values are invalid:\n'
              f'- {"- ".join(value)}')
    print(f'{"".center(80, "-")}')


# ---------------------------------UTILITIES------------------------------------

def new_test(metafile, key_yaml, sub_lists, key_name, invalid_keys,
             invalid_entry, invalid_value, input_type):
    if isinstance(metafile, dict) and not (
            'value' in metafile and 'unit' in metafile):
        for key in metafile:
            if not key_yaml:
                invalid_keys.append(key)
            elif key not in key_yaml:
                invalid_keys.append(key)
            else:
                res_keys, res_entries, res_values = new_test(metafile[key],
                                                 key_yaml[key][4], sub_lists,
                                                 f'{key_name}:{key}' if
                                                 key_name != '' else key,
                                                 invalid_keys, invalid_entry, invalid_value, key_yaml[key][7] if len(key_yaml[key]) > 5 else None)
                invalid_keys = res_keys
    elif isinstance(metafile, list):
        for item in metafile:
            sub_lists.append(item)
            res_keys, res_entries, res_values = new_test(item, key_yaml, sub_lists,
                                             key_name, invalid_keys,
                                             invalid_entry, invalid_value, input_type)
            invalid_keys = res_keys
            sub_lists = sub_lists[:-1]
    else:
        invalid = new_test_for_whitelist(key_name.split(':')[-1], metafile,
                                         sub_lists)
        if invalid:
            invalid_entry.append(f'{key_name}:{metafile}')

        inv_value, message = validate_value(metafile, input_type)

        if not inv_value:
            invalid_value.append((key_name, metafile, message))

    return invalid_keys, invalid_entry, invalid_value


def new_test_for_whitelist(entry_key, entry_value, sublists):
    whitelist = utils.read_whitelist(entry_key)
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
                whitelist = utils.read_whitelist(value[0])
        if isinstance(whitelist, dict) and whitelist[
                'whitelist_type'] == 'group':
            whitelist = [x for xs in list(whitelist.values()) for x in xs]
    if whitelist and not isinstance(whitelist, list) and not isinstance(
            whitelist, dict) \
            and os.path.isfile(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'whitelists',
            whitelist)):
        whitelist = utils.read_whitelist(whitelist)
    if whitelist and entry_value not in whitelist:
        return True
    return False


def test_for_mandatory(metafile, key_yaml, invalid_keys):
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
                                         invalid_keys, key, [])
    return missing_keys


def get_missing_keys(node, metafile, invalid_keys, pre, missing):
    """
    This function tests if all mandatory keys from the structure file
    'keys.yaml' are present in the metadata file.
    :param node: a key within the read in structure file 'keys.yaml'
    :param metafile: the read in metadata file
    :param invalid_keys: a list containing invalid keys that should be ignored
    :param pre: a string to save and chain keys in order to save their position
    :param missing: a list to save the missing mandatory keys
    """
    res = find_key(metafile, pre, node[1], node[4], invalid_keys)

    if node[0] == 'mandatory':
        missing += res

    if node[0] == 'mandatory' or len(res) == 0:
        if isinstance(node[4], dict):
            for key in node[4]:
                missing = get_missing_keys(node[4][key], metafile,
                                           invalid_keys, pre + ':' + key,
                                           missing)
    return missing


def find_key(metafile, key, is_list, values, invalid_keys):
    """
    
    :param metafile: the read in metadata file
    :param key: a string of chained keys (key1:key2...)
    :param is_list: bool, true if the instance in the structure is a list
    :param values: the default entry for the key within the structure file
    :param invalid_keys: a list containing invalid keys that should be ignored
    :return: missing_keys: a list containing the missing mandatory keys
    """
    missing_keys = []
    for k in key.split(':'):
        metafile = list(utils.find_keys(metafile, k))
    if len(metafile) == 0:
        missing_keys.append(key)
    elif is_list and isinstance(values, list):
        for entry in metafile[0]:
            for value in entry:
                if value not in invalid_keys:
                    if values[value][0] == 'mandatory':
                        for y in metafile[0]:
                            if value not in y:
                                missing_keys.append(key + ':' + value)
    return missing_keys


def validate_value(input_value, value_type):
    valid = True
    message = None
    if value_type == 'bool':
        if input_value not in [True, False]:
            valid = False
            message = 'The value has to be of type bool (True or False).'
    elif value_type == 'int':
        if not isinstance(input_value, int):
            valid = False
            message = 'The value has to be an integer.'
    elif value_type == 'float':
        if not isinstance(input_value, float):
            valid = False
            message = 'The value has to be a float.'
    elif value_type == 'date':
        try:
            input_date = input_value.split('.')
            if len(input_date) != 3 or len(input_date[0]) != 2 or len(
                    input_date[1]) != 2 or len(input_date[2]) != 4:
                raise SyntaxError
            input_value = datetime.date(int(input_date[2]),
                                            int(input_date[1]),
                                            int(input_date[0]))
        except (IndexError, ValueError, SyntaxError) as e:
            valid = False
            message = f'Input must be of type \'DD.MM.YYYY\'.'
    elif input_value == 'str' and '\"' in input_value:
        valid = False
        message = 'The value contains an invalid character (\").'
    return valid, message