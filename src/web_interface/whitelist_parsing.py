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
            whitelist_keys = whitelist['whitelist_keys'] if \
                'whitelist_keys' in whitelist else None
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
        if whitelist and 'whitelist' in whitelist:
            whitelist = whitelist['whitelist']
        input_type = 'value_unit'

    # boolean value
    elif node['input_type'] == 'bool':

        # set whitelist to True and False, input type to select and whitelist
        # type to plain
        whitelist = [True, False]
        whitelist_type = 'plain'
        input_type = 'select'

    # no whitelist or special case
    else:

        # set input type as defines in general structure
        input_type = node['input_type']

    return whitelist, whitelist_type, input_type, headers, whitelist_keys


# TODO: raus
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
    if 'input_fields' in item:
        for i in item['input_fields']:
            i, whitelists = get_whitelist_object(i, organism_name, whitelists)

    else:

        whitelist, whitelist_type, input_type, headers, whitelist_keys = \
            parse_whitelist(item['position'].split(':')[-1], item,
                            {'organism': organism_name})

        if headers is not None:
            item['headers'] = headers
        if whitelist_keys is not None:
            item['whitelist_keys'] = whitelist_keys
        if whitelist_type is not None:
            item['whitelist_type'] = whitelist_type

        item['whitelist'] = item['position'].split(':')[-1] if \
            whitelist is not None else None

        if input_type in ['single_autofill', 'multi_autofill']:
            print(f'SEARCH {"search_info" in item}')
            item['search_info'] = {'organism': organism_name,
                                   'key_name': item['position'].split(':')[-1]}

            if 'list_value' not in item:
                print('LIST_VALUE')
                item['list_value'] = []

        item['input_type'] = input_type

        if input_type == 'value_unit':
            whitelists['unit'] = whitelist
            if item['value_unit'] not in item:
                print('HIER')
                item['value_unit'] = None
        elif whitelist is not None:
            whitelists[item['position'].split(':')[-1]] = whitelist

    return item, whitelists

