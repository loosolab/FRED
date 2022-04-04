from src import utils
import itertools

# This script includes functions for the validation of metadata yaml files


def test_for_mandatory(metafile):
    """
    returns False if a mandatory key could not be found in yaml else True
    :param metafile: a dictionary containing the information a yaml file
    :return: bool: True if all mandatory keys are found, False if one is missing
    """
    key_yaml = utils.read_in_yaml('keys.yaml')
    mandatory_keys = []
    for key in key_yaml:
        mandatory_keys += get_mandatory_keys(key_yaml[key],metafile, key, [])
    if False in mandatory_keys:
        return False
    else:
        return True


# test if key is in dictionary + if key is in every list element within dict
def find_key(item, key, is_list):
    for k in key.split(':'):
        item = list(utils.find_keys(item, k))
    if len(item) == 0:
        return False
    if is_list:
        if any(len(item[0][0]) != len(i) for i in item[0]):
            print(key)
            return False
    return True

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

def get_mandatory_keys(node, metafile, pre='', mandatory=[]):
    """
    generator to return all keys in dictionary that fit a given key value
    :param node: a dictionary to be searched
    :param kv: the key value to search for
    """
    if node[0] == 'mandatory':
        mandatory.append(find_key(metafile, pre, node[1]))
        if isinstance(node[4], dict):
            for key in node[4]:
                mandatory = get_mandatory_keys(node[4][key], metafile, pre + ':' + key, mandatory)
    else:
        if find_key(metafile, pre, node[1]):
            if isinstance(node[4], dict):
                for key in node[4]:
                    mandatory = get_mandatory_keys(node[4][key], metafile,
                                                   pre + ':' + key, mandatory)
    return mandatory