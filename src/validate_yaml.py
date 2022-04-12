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
    invalid_keys, invalid_entries = test_for_valid_keys(metafile, key_yaml)
    missing_mandatory_keys = test_for_mandatory(metafile, key_yaml,
                                                [x.split(':')[-1] for x in
                                                 invalid_keys])
    if len(missing_mandatory_keys) > 0 or len(invalid_keys) > 0 or len(
            invalid_entries) > 0:
        valid = False
    return valid, missing_mandatory_keys, invalid_keys, invalid_entries


# -----------------------------------REPORT-------------------------------------


def print_validation_report(metafile, missing_mandatory_keys, invalid_keys,
                            invalid_values):
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
        id = metafile['project']['id']
    except KeyError:
        id = 'missing'
    invalid_entries = '\n- '.join(invalid_keys)
    missing = '\n- '.join(missing_mandatory_keys)
    values = ''
    for v in invalid_values:
        key = v[0]
        entry = ', '.join(v[1])
        values += entry + ' in ' + key + '\n'
    print(f'{"INVALID FILE".center(80, "-")}\n'
          f'Project ID: {id}\n'
          f'Path: {metafile["path"]}\n\n'
          f'Report:\n')
    if len(invalid_keys) > 0:
        print(f'The following keys were invalid:\n'
              f'- {invalid_entries}\n')
    if len(missing_mandatory_keys) > 0:
        print(f'The following mandatory keys were missing:\n'
              f'- {missing}\n')
    if len(invalid_values) > 0:
        print(f'The following values are invalid:\n'
              f'- {values}')
    print(f'{"".center(80, "-")}')


# ---------------------------------UTILITIES------------------------------------


def test_for_valid_keys(metafile, key_yaml):
    """
    This function checks if all keys in the metadata file are valid. It also
    calls a function to test if the entered values match the whitelist.
    :param metafile: the read in metadata yaml file
    :param key_yaml: the read in structure file 'keys.yaml'
    :return:
    invalid_keys: a list containing invalid keys
    invalid_entry: a list containing invalid entries -> (key, [value])
    """
    file_keys = utils.get_keys_in_dict(metafile, {}, '')
    invalid_keys = []
    invalid_entry = []
    for key in file_keys:
        item = utils.find_list_key(key_yaml, key)
        if len(item) == 0:
            invalid_keys.append(key)
        elif item[0][5]:
            whitelist = test_for_whitelist(key.split(':')[-1], file_keys[key])
            if len(whitelist) > 0:
                invalid_entry.append([key, whitelist])
    return invalid_keys, invalid_entry


def test_for_whitelist(whitelist_key, entry_key):
    """
    This function reads in the whitelist file for a given key and tests if the
    entry value matches the whitelist.
    :param whitelist_key: the key for which the whitelist should be read in
    :param entry_key: the key of the metadata file whose value is to be tested
    :return: invalid: a list containing the invalid keys
    """
    invalid = []
    whitelist = utils.read_whitelist(whitelist_key)
    for element in entry_key:
        if whitelist and element not in whitelist:
            invalid.append(element)
    return invalid


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
    elif is_list:
        for entry in metafile[0]:
            for value in entry:
                if value not in invalid_keys:
                    if values[value][0] == 'mandatory':
                        for y in metafile[0]:
                            if value not in y:
                                missing_keys.append(key + ':' + value)
    return missing_keys
