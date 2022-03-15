from src import utils
from src import find_metafiles


# This script includes functions for the validation of metadata yaml files


def test_for_mandatory(metafile):
    """
    returns False if a mandatory key could not be found in yaml else True
    :param metafile: a dictionary containing the information a yaml file
    :return: bool: True if all mandatory keys are found, False if one is missing
    """
    key_yaml = utils.read_in_yaml('keys.yaml')
    mandatory_keys = [x.replace(':mandatory', '').split(':') for x in
                      list(utils.get_keys_as_list(key_yaml)) if
                      'mandatory' in x]
    for a_key in mandatory_keys:
        result = [metafile]
        for key in a_key:
            r2 = []
            for item in result:
                r2 += list(utils.find_keys(item, key))
            result = r2
            if len(result) == 0:
                return False
    return True
