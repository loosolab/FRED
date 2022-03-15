import re
from src import utils

# This scripts implements functions to find metadata files that contain given
# values


def find_projects(metafiles_list, search_parameters, return_dict):
    """
    iterate through a list of dictionaries containing information of yaml
    files  and return a dictionary containing matches
    :param metafiles_list: a list of read in yaml files (as dictionaries)
    :param search_parameters: a nested list - elements in outer list are linked
    via 'or' and the elements within the inner lists are linked via 'and';
    e.g. [['id:pul47','name:Jasmin Walter'],['id:shu27']] means
    ('id:pul47' and 'name:Jasmin Walter') or 'id:shu27
    :param return_dict: bool: if True, whole dictionary is returned,
    if False path of dictionary is returned
    :return: a dictionary containing all matches, key=id, value=dictionary or
    path depending on return_dict
    """
    matches = []
    for metafile in metafiles_list:
        or_found = []
        print('searching file ' + metafile['path'])

        # iterate through outer list -> or
        for or_param in search_parameters:
            and_found = []

            # iterate through inner list -> and
            for and_param in or_param:

                # split search parameter at ':'
                # last element in list saved in 'should-be_found'
                # -> False if 'not' was specified for the parameter
                params = and_param.split(':')
                should_be_found = params[-1]

                # call find_entry to get match
                match = find_entry(metafile, params[0:-2], params[-2])

                # test if match was found and if it should be found
                if (match and should_be_found == 'True') or \
                        (not match and should_be_found == 'False'):
                    and_found.append(True)
                else:
                    and_found.append(False)

            # test if all parameters for 'and' are True
            if False not in and_found:
                or_found.append(True)

        # test if one parameter for 'or' is True
        if True in or_found:
            match_dict = {metafile['project']['id']: metafile['path'] if return_dict==False else metafile}
            matches.append(match_dict)

    return matches


def find_entry(metafile, targets, target_value):
    """
    test if a value (and key) is found in a metadata dictionary
    :param metafile: dictionary containing information of metadata yaml
    :param targets: list of keys in order of depth in yaml
    -> [key1, key2, key3] for 'key1:key2:key3:value'
    :param target_value: the value that should be found
    :return: True if match was found, else None
    """
    # iterate through keys in 'targets' and search for match
    if len(targets)>=1:
        result = [metafile]
        for key in targets:
            r2 = []
            for item in result:
                r2 += list(utils.find_keys(item, key))
            result = r2
    # iterate through whole dictionary if no key was specified in 'targets'
    else:
        result = list(utils.find_values(metafile, target_value))

    # test if target_value was found
    if target_value in result:
        return True