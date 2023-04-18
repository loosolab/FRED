import src.utils as utils
import copy


def get_single_whitelist(ob):
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
    whitelist = utils.get_whitelist(ob['key_name'], infos, all_plain)

    # test if the whitelist was found and read in correctly and return the list
    # of whitelist values
    if whitelist and 'whitelist' in whitelist:
        return whitelist['whitelist']

    # return None if no whitelist was found
    else:
        return None


# TODO: redundant?
def get_whitelist_with_type(key, key_yaml, organism, headers):
    """
    This function reads in a whitelist and returns it together with its type.
    :param key: the key containing a whitelist
    :param key_yaml: the read in keys.yaml
    :param organism: the selected organism
    :param headers: the headers that a whitelist may contain
    :return:
    whitelist: the read in whitelist
    whitelist_type: the whitelist type
    input_type: the type of the expected value
    headers: the headers that might occur in the whitelist
    """

    # initialize whitelist_type and whitelist_keys with None
    whitelist_type = None
    whitelist_keys = None

    # define an object containing the organism to be able to parse whitelists
    # of type 'depend'
    filled_object = {'organism': organism}

    # TODO: direkt gesplitted übergeben
    organism = organism.split(' ')[0]

    # extract the properties of the key from the general structure
    options = list(utils.find_keys(key_yaml, key))

    # key was found in general structure
    if len(options) > 0:

        # value of key is a dictionary
        if isinstance(options[0]['value'], dict):

            # special case: merge or value unit
            if 'special_case' in options[0] and (
                    'merge' in options[0]['special_case'] or 'value_unit' in
                    options[0]['special_case']):

                # read in and parse whitelist
                whitelist, whitelist_type, input_type, headers, \
                    whitelist_keys = parse_whitelist(key, options[0],
                                                     filled_object)

            else:

                # initialize an empty list to store the dictionaries of the
                # keys
                val = []

                # iterate over the keys of the value
                for k in options[0]['value']:

                    # initialize an empty dictionary to store the properties of
                    # the key for the wi_object
                    k_val = {}

                    # read in and parse
                    k_val['whitelist'], k_val['whitelist_type'], \
                        k_val['input_type'], \
                        header, whitelist_keys = parse_whitelist(
                        k, key_yaml, organism, headers)

                    # set header
                    if header is not None:
                        k_val['headers'] = header

                    # set whitelist keys
                    if whitelist_keys is not None:
                        k_val['whitelist_keys'] = whitelist_keys

                    # extract properties of the key from general structure
                    node = list(utils.find_keys(key_yaml, k))[0]

                    # set key 'unit' for special case value_unit
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None

                    # set properties
                    k_val['displayName'] = node['display_name']
                    k_val['required'] = node['mandatory']
                    k_val['position'] = k
                    k_val['value'] = []

                    # add dictionary with properties of the key to the list
                    val.append(k_val)

                # add the key 'Multi'
                # -> used for experimental factors of type list
                # -> one factor can occur multiple times in one condition
                val.append({'displayName': 'Multi', 'position': 'multi',
                            'whitelist': [True, False], 'input_type': 'bool',
                            'value': False})

                # set input type to nested
                input_type = 'nested'

                return val, whitelist_type, input_type, headers, whitelist_keys
        else:
            whitelist, whitelist_type, input_type, headers, whitelist_keys = \
                parse_whitelist(key, options[0], filled_object)
    else:
        input_type = 'short_text'

    if options[0]['list']:
        new_w = [
            {'whitelist': whitelist, 'position': key,
             'displayName': options[0]['display_name'], 'required': True, 'value': [],
             'input_type': input_type, 'whitelist_type': whitelist_type},
            {'displayName': 'Multi', 'position': 'multi',
             'whitelist': [True, False], 'input_type': 'bool',
             'value': False}]
        for i in range(len(new_w)):
            if new_w[i]['input_type'] == 'multi_autofill' or new_w[i]['input_type'] == 'single_autofill':
                new_w[i]['search_info'] = {'key_name': key, 'organism': organism}
        whitelist = new_w
        whitelist_type = 'list_select'
        input_type = 'nested'
    return whitelist, whitelist_type, input_type, headers, whitelist_keys


def parse_whitelist(key_name, node, filled_object):

    # initialize return values
    whitelist = None
    whitelist_type = None
    input_type = 'short_text'
    headers = None
    whitelist_keys = None

    # whitelist is defined or special case merge
    if ('whitelist' in node and node['whitelist']) or (
            'special_case' in node and 'merge' in node['special_case']):

        # read in whitelist
        whitelist = utils.get_whitelist(key_name, filled_object)

        # test if the right keys are present in the whitelist
        # -> format check
        if whitelist is not None and 'whitelist_type' in whitelist and \
                'whitelist' in whitelist:

            # set whitelist type , headers, whitelist_keys, whitelist and
            # input_type
            whitelist_type = whitelist['whitelist_type']
            headers = whitelist['headers'] if 'headers' in whitelist else None
            whitelist_keys = whitelist['whitelist_keys'] if 'whitelist_keys' in \
                                                            whitelist else None
            whitelist = whitelist['whitelist']
            input_type = 'select'

            # TODO: raus?
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
                    key_name != 'department':

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
        whitelist = utils.get_whitelist('unit', filled_object)
        input_type = 'value_unit'

    # boolean value
    elif node['input_type'] == 'bool':

        # set whitelist to True and False and set input type to select
        whitelist = [True, False]
        input_type = 'select'

    # no whitelist or special case
    else:

        # set input type as defines in general structure
        input_type = node['input_type']

    # TODO: one tier higher / raus
    # set headers and whitelist keys
    if headers is not None:
        whitelist = {'whitelist': whitelist,
                     'whitelist_type': whitelist_type,
                     'headers': headers}
        whitelist_type = None
        if whitelist_keys is not None:
            whitelist['whitelist_keys'] = whitelist_keys

    return whitelist, whitelist_type, input_type, headers, whitelist_keys


def get_whitelist_object(item, organism_name, whitelists):
    """
    This function creates a whitelist object containing the whitelists of all
    keys of  sample.
    :param item: a key containing a whitelist
    :param organism_name: the selected organism
    :param whitelists: a dictionary to save the whitelists to
    :return:
    item: the key containing the whitelist
    whitelists: the whitelist object
    """
    if 'input_type' in item:
        input_type = item['input_type']
        if input_type == 'select' or input_type == 'single_autofill' or input_type == 'multi_autofill' or input_type == 'dependable':
            whitelist = utils.get_whitelist(item['position'].split(':')[-1],
                                            {'organism': organism_name})
            if 'headers' in whitelist:
                item['headers'] = whitelist['headers']
            if 'whitelist_keys' in whitelist:
                item['whitelist_keys'] = whitelist['whitelist_keys']

            if whitelist['whitelist_type'] == 'group':
                input_type = 'group_select'
            if whitelist['whitelist_type'] == 'plain' or \
                    whitelist['whitelist_type'] == 'plain_group':
                whitelist = whitelist['whitelist']
        elif input_type == 'bool':
            whitelist = [True, False]
            input_type = 'select'
        elif input_type == 'value_unit':
            if 'value_unit' not in item:
                item['value_unit'] = None
            whitelist = utils.read_whitelist('unit')
            if 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'plain':
                whitelist = whitelist['whitelist']
        else:
            whitelist = None

        item['whitelist'] = item['position'].split(':')[-1] if whitelist is not None else None
        if whitelist and isinstance(whitelist, list) and len(whitelist) > 30:
            if item['list']:
                input_type = 'multi_autofill'
            else:
                input_type = 'single_autofill'
            item['search_info'] = {'organism': organism_name,
                                   'key_name': item['position'].split(':')[-1]}
            if not 'list_value' in item:
                item['list_value'] = []
            whitelist = None
        item['input_type'] = input_type
        if input_type == 'group_select':
            w = []
            for key in whitelist['whitelist']:
                w.append({'title': key,
                          'whitelist': whitelist['whitelist'][key]})
            whitelist = w
        if whitelist:
            whitelists[item['position'].split(':')[-1]] = whitelist
        if input_type == 'value_unit':
            whitelists['unit'] = whitelist
    elif 'input_fields' in item:
        for i in item['input_fields']:
            i, whitelists = get_whitelist_object(i, organism_name, whitelists)
    return item, whitelists

