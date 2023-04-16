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
    whitelist_type = None
    whitelist_keys = None

    filled_object = {'organism': copy.deepcopy(organism)}
    organism = organism.split(' ')[0]

    options = list(utils.find_keys(key_yaml, key))

    if len(options) > 0:

        if isinstance(options[0]['value'], dict):
            if 'special_case' in options[0] and ('merge' in options[0]['special_case'] or 'value_unit' in options[0]['special_case']):
                whitelist, whitelist_type, input_type, headers, \
                    whitelist_keys = parse_whitelist(key, options, filled_object)
            else:
                val = []
                for k in options[0]['value']:
                    k_val = {}
                    k_val['whitelist'], k_val['whitelist_type'], \
                        k_val['input_type'], \
                        header, whitelist_keys = get_whitelist_with_type(
                        k, key_yaml, organism, headers)
                    if header is not None:
                        k_val['headers'] = header
                    if whitelist_keys is not None:
                        k_val['whitelist_keys'] = whitelist_keys
                    node = list(utils.find_keys(key_yaml, k))[0]
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None
                    k_val['displayName'] = node['display_name']
                    k_val['required'] = node['mandatory']
                    k_val['position'] = k
                    k_val['value'] = []
                    val.append(k_val)
                val.append({'displayName': 'Multi', 'position': 'multi',
                            'whitelist': [True, False], 'input_type': 'bool',
                            'value': False})
                input_type = 'nested'
                return val, whitelist_type, input_type, headers, whitelist_keys
        else:
            whitelist, whitelist_type, input_type, headers, whitelist_keys = \
                parse_whitelist(key, options, filled_object)
    else:
        input_type = 'short_text'

    if options['list']:
        new_w = [
            {'whitelist': whitelist, 'position': key,
             'displayName': options['display_name'], 'required': True, 'value': [],
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

    whitelist = None
    whitelist_type = None
    input_type = 'short_text'
    headers = None
    whitelist_keys = None

    if ('whitelist' in node and node['whitelist']) or (
            'special_case' in node and 'merge' in node['special_case']):

        # read in whitelist
        whitelist = utils.get_whitelist(key_name, filled_object)

        # test if the right keys are present in the whitelist
        # -> format check
        if whitelist is not None and 'whitelist_type' in whitelist and 'whitelist' in whitelist:

            # set whitelist type and whitelist
            whitelist_type = whitelist['whitelist_type']
            headers = whitelist['headers'] if 'headers' in whitelist else None
            whitelist_keys = whitelist['whitelist_keys'] if 'whitelist_keys' in \
                                                            whitelist else None
            whitelist = whitelist['whitelist']

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
                             'whitelist': whitelist['whitelist'][key]})
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

    elif 'special_case' in node and 'value_unit' in node['special_case']:

        whitelist = utils.get_whitelist('unit', filled_object)
        input_type = 'value_unit'

    elif node['input_type'] == 'bool':

        whitelist = ['True', False]
        input_type = 'select'

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

