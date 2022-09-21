import re
from src import utils
from src import generate
from itertools import chain

# This scripts implements functions to find metadata files that contain given
# values


def find_projects(metafile, search, return_dict):
    """
    iterate through a list of dictionaries containing information of yaml
    files  and return a dictionary containing matches
    :param metafile: a read in yaml file (as dictionary)
    :param search_parameters: a nested list - elements in outer list are linked
    via 'or' and the elements within the inner lists are linked via 'and';
    e.g. [['input_id:pul47','name:Jasmin Walter'],['input_id:shu27']] means
    ('input_id:pul47' and 'name:Jasmin Walter') or 'input_id:shu27
    :param return_dict: bool: if True, whole dictionary is returned,
    if False path of dictionary is returned
    :return: a dictionary containing all matches, key=input_id, value=dictionary or
    path depending on return_dict
    """
    # split parameters linked via or into list

    sub_list = ''
    sub = ''
    list_name = []
    depth = -1
    for letter in search:
        if letter == '[':
            depth +=1
            list_name.append(sub.split(' ')[-1])
            sub = sub.replace(list_name[depth], '')
            sub_list += sub
            sub = ''
        elif letter == ']':
            if sub != '':
                res = parse_search_parameters(metafile, sub, list_name[depth] if depth != -1 else None)
                sub_list += str(True) if res else str(False)
            depth -= 1
            if sub_list != ('True' or 'False'):
                res = parse_search_parameters(metafile, sub_list, list_name[depth] if depth != -1 else None)
                sub_list = str(True) if res else str(False)
            sub = ''
        else:
            sub += letter

    if sub_list == '':
        res = parse_search_parameters(metafile, sub, None)
        sub_list += str(True) if res else str(False)

    if sub_list != ('True' or 'False'):
        sub_list = parse_search_parameters(metafile, sub_list, None)

    if sub_list == 'True':
        return True
    else:
        return False


def parse_search_parameters(metafile, search, list_element = None):

    if list_element:
        metafile = list(utils.find_keys(metafile, list_element))

    search_parameters = search.split(' or ')

    for i in range(len(search_parameters)):

        # split parameters linked via 'and' within the 'or-list' -> nested list
        search_parameters[i] = search_parameters[i].split(' and ')

        for j in range(len(search_parameters[i])):

            # parameter to declare if search parameter should occur
            # set to False if 'not' was declared for the search parameter
            # appended to the search parameter with ':' as delimiter

            if search_parameters[i][j] != 'True' or 'False':
                search_parameters[i][j] = get_should_be_in(search_parameters[i][j])

    results = get_matches(metafile, search_parameters)
    if True in results:
        result = True
    else:
        result = False

    return result


def get_matches (metafile, search_parameters):
    results = []
    if isinstance(metafile, list):
        for x in metafile:
            results += get_matches(x, search_parameters)
    else:
        results += [calculate_match(metafile, search_parameters)]
    return results


def calculate_match(metafile, search_parameters):

    or_found = []
    # iterate through outer list -> or
    for or_param in search_parameters:
        and_found = []

        # iterate through inner list -> and
        for and_param in or_param:

            # split search parameter at ':'
            # last element in list saved in 'should-be_found'
            # -> False if 'not' was specified for the parameter
            if '"' in and_param:
                params = []
                should_be_found = and_param.split(':')[-1]
                and_param.rstrip(f':{should_be_found}')
                p = generate.split_cond(and_param)[0]
                if p[0] != '':
                    params = p[0].split(':')
                params.append(p[1])
                params.append(should_be_found)
            else:
                params = and_param.split(':')
                should_be_found = params[-1]
            if len(params) == 2 and params[0] == 'True':
                match = True
            elif len(params) == 2 and params[0] == 'False':
                match = False
            else:
                # call find_entry to get match
                match = find_entry(metafile, params[0:-2], params[-2])
            # test if match was found and if it should be found
            if (match and should_be_found == 'True') or \
                    ( not match and should_be_found == 'False'):
                and_found.append(True)
            else:
                and_found.append(False)
        # test if all parameters for 'and' are True
        if False not in and_found:
            or_found.append(True)
        else:
            or_found.append(False)

    # test if one parameter for 'or' is True
    return True if True in or_found else False


def get_should_be_in(param):
    if isinstance(param, list):
        p = []
        for x in param:
            p.append(get_should_be_in(x))
    else:
        should_be_in = True
        if 'not ' in param:
            should_be_in = False
            param = param.replace('not ', '')
        p = param.strip() + (':' + str(should_be_in))
    return p


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
    if len(targets) >= 1:
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
    for value in result:
        if str(target_value) == str(value):
            return True
    return False