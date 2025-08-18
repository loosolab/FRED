import os

import src.utils as utils

def get_whitelist_object(pgm_object):
    key_yaml = pgm_object['structure']
    whitelist_object = read_in_whitelists(pgm_object['whitelist_path'])
    return whitelist_object


def read_in_whitelists(path):
    files = os.listdir(os.path.join(path, 'misc', 'json'))
    whitelists_object=test(files, {}, path)
    return whitelists_object


def test(files, whitelist_object, path):
    for file in files:
        if os.path.isfile(os.path.join(path, 'misc', 'json', file)) and not '.' in file:
            whitelist_object[file] = utils.read_whitelist(file, whitelist_path=path)
        elif os.path.isdir(os.path.join(path, 'misc', 'json', file)):
            new_files = [os.path.join(file, f) for f in os.listdir(os.path.join(path, 'misc', 'json', file))]
            whitelist_object = test(new_files, whitelist_object, path)
    return whitelist_object


def get_single_whitelist(ob, whitelist_object):
    """
    This functions returns a single whitelist of type 'plain' for a key that is
    specified within a given dictionary. If the organism is specified as well,
    dependent whitelists only contain the values for said organism.
    (-> used for metadata generation and editing) If no organism is given, the
    whitelists of multiple organisms are merged together. (-> used for
    searching)
    :param ob: a dictionary containing the key 'key_name' and optionally the
               key 'organism'
    :return: either a whitelist or None if no whitelist exists
    """

    # test if an organism was specified
    if 'organism' in ob:

        # save the organism in a dictionary to work like a result dict
        infos = {'organism': ob['organism']}

        # set all_plain to False since dependencies from the organism can be
        # taken into account
        all_plain = False

    else:

        # set an empty dictionary to work like a result dict -> no info was
        # given
        infos = {}

        # set all_plain to True since dependencies cannot be considered
        all_plain = True

    # read in the whitelist
    whitelist = utils.get_whitelist(ob['key_name'], infos, whitelist_object=whitelist_object, all_plain=all_plain)

    # test if the whitelist was found and read in correctly and return the list
    # of whitelist values
    if whitelist and 'whitelist' in whitelist:
        return whitelist['whitelist']

    # return None if no whitelist was found
    else:
        return None


def parse_whitelist(key_name, node, filled_object, whitelist_object):
    """
    This function read in a whitelist and parses it according to type, headers
    and whitelist keys
    :param key_name: the key for which a whitelist is defined
    :param node: the part of the read in metadata structure that contains the
                 key
    :param filled_object: a partially filled whitelist object
    :return: whitelist: the read in whitelist
             whitelist_type: the type of the whitelist
             input_type: the type of the input field in the web interface
             headers: a string containing headers
             whitelist_keys: the headings of a grouped whitelist
    """

    # initialize return values
    whitelist = None
    whitelist_type = None
    input_type = 'short_text'
    headers = None
    whitelist_keys = None
    double = []

    # whitelist is defined or special case merge
    if ('whitelist' in node and node['whitelist']) or (
            'special_case' in node and 'merge' in node['special_case']):

        # read in whitelist
        whitelist = utils.get_whitelist(key_name, filled_object, whitelist_object=whitelist_object)

        if whitelist is not None:

            if 'double' in whitelist:
                double = whitelist['double']

            # test if the right keys are present in the whitelist
            # -> format check
            if 'whitelist_type' in whitelist and 'whitelist' in whitelist:

                # set whitelist type , headers, whitelist_keys, whitelist and
                # input_type
                whitelist_type = whitelist['whitelist_type']
                headers = whitelist['headers'] if 'headers' in whitelist else None
                whitelist_keys = whitelist['whitelist_keys'] if \
                    'whitelist_keys' in whitelist else None
                whitelist = whitelist['whitelist']
                input_type = 'select'

                # TODO: remove?
                if whitelist_type == 'depend':
                    whitelist = None
                    input_type = 'dependable'

                # TODO: test if plain_group is already there
                elif whitelist_type == 'group':
                    if isinstance(whitelist, dict):
                        new_w = []
                        for key in whitelist:
                            new_w.append(
                                {'title': key,
                                 'whitelist': whitelist[key]})
                        input_type = 'group_select'
                        whitelist = new_w
                    else:
                        input_type = 'select'
                        whitelist_type = 'plain_group'

                # TODO: better solution for department
                # test if whitelist is longer than 30
                if whitelist and len(whitelist) > 30 and \
                        key_name not in ['department', 'factor']:

                    # set whitelist type to multi_autofill if it is a list
                    if node['list']:
                        input_type = 'multi_autofill'

                    # set whitelist type to single_autofill if it is a string
                    else:
                        input_type = 'single_autofill'

                    # set whitelist to None
                    # -> whitelists on the website will be called with
                    # get_single_whitelist function (from whitelist_parsing) and
                    # used with an autocompletion
                    # -> whitelist only gets send to website if the field is
                    # actually entered which saves space and time
                    whitelist = None

    # special case: value unit
    elif 'special_case' in node and 'value_unit' in node['special_case']:

        # read in unit whitelist and set input type to value_unit
        whitelist = utils.get_whitelist('unit', filled_object, whitelist_object=whitelist_object)
        if whitelist and 'whitelist' in whitelist:
            whitelist = whitelist['whitelist']
        input_type = 'value_unit'

    # boolean value
    elif node['input_type'] == 'bool':

        # set whitelist to True and False, input type to select and whitelist
        # type to plain
        whitelist = ['True', 'False']
        whitelist_type = 'plain'
        input_type = 'select'

    # no whitelist or special case
    else:

        # set input type as defines in general structure
        input_type = node['input_type']

    return whitelist, whitelist_type, input_type, headers, whitelist_keys, double
