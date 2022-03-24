from src import utils

# This script includes functions for the validation of metadata yaml files


def test_for_mandatory(metafile):
    """
    returns False if a mandatory key could not be found in yaml else True
    :param metafile: a dictionary containing the information a yaml file
    :return: bool: True if all mandatory keys are found, False if one is missing
    """
    key_yaml = utils.read_in_yaml('keys.yaml')
    all_keys = list(utils.get_keys_as_list(key_yaml, True))
    mandatory_keys = []
    for x in all_keys:
        res = parse_nested(x)
        if res:
            mandatory_keys.append(res)

    res = []
    for a_key in mandatory_keys:
        res.append(find_key(metafile,a_key))

    if False in res:
        return False
    else:
        return True


# test if key is in dictionary + if key is in every list element within dict
def find_key(item, key):
    if isinstance(key, list):
        r = []
        for x in key:
            r.append(find_key(item, x))
        if not any(len(r[0]) != len(i) for i in r):
            return True
    else:
        r = item
        for k in key.split(':'):
            r = list(utils.find_keys(r, k))
        return r
    return False


# returns key with value 'mandatory' within nested list
def parse_nested(keys):
    if isinstance(keys, list):
        test = []
        for x in keys:
            res = parse_nested(x)
            if res:
                test.append(res)
        if len(test) > 0:
            return test
    else:
        key, value = utils.split_str(keys)
        if 'mandatory' in value:
            return key
