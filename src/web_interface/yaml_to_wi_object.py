import src.web_interface.whitelist_parsing as whitelist_parsing

# TODO: example of format in wi_object (Keys)


def get_empty_wi_object(key_yaml):
    """
    This function parses the keys.yaml and returns an empty object for the web
    interface.
    :return: wi_object: object containing all information from the keys.yaml
             in a format readable by the web interface
    """

    # initialize emtpy dict to save wi_object to
    wi_object = {}

    # iterate over all keys in general structure
    for key in key_yaml:

        # parse information of a key into wi_object format
        wi_object[key], whitelist_object = parse_empty(key_yaml[key], key,
                                                       key_yaml, {})

    # add a key 'all_factors' with an empty list as value to the object
    # the experimental factors will be saved here after input on the website
    wi_object['all_factors'] = []

    return wi_object


def parse_empty(node, pos, key_yaml, filled_object,
                get_whitelist_object=False):
    """
    This function parses a part of the key.yaml into an object readable by the
    web-interface
    :param node: a part of the key.yaml that should be parsed
    :param pos: the position of the node (chained keys)
    :param key_yaml: the whole key.yaml
    :param get_whitelist_object: bool, True if whitelists should be written
                                 into a separate object, False if not, default
                                 False
    :return: part_object: an object for the web interface parsed from node
    """

    # disable input for the keys condition_name and sample_name because they
    # are generated
    input_disabled = True if pos.split(':')[-1] \
        in ['condition_name', 'sample_name'] else False

    whitelist_object = {}

    # test if the value of the current node is a dictionary
    if isinstance(node['value'], dict):

        # special case: merge or value_unit
        if 'special_case' in node and ('merge' in node['special_case'] or
                                       'value_unit' in node['special_case']):

            # read and parse whitelist
            whitelist, whitelist_type, input_type, headers, whitelist_keys = \
                whitelist_parsing.parse_whitelist(pos.split(':')[-1], node,
                                                  filled_object)

            # set input type depending on case
            if 'merge' in node['special_case']:
                input_type = 'select'

            elif 'value_unit' in node['special_case']:
                input_type = 'value_unit'

            else:
                input_type = 'short_text'

            # set input type of field organism to 'organism' -> special case
            #if pos.split(':')[-1] == 'organism':
            #    input_type = 'organism_name'

            if get_whitelist_object:

                if input_type == 'value_unit':
                    whitelist_object['unit'] = whitelist
                    whitelist = 'unit'

                elif whitelist is not None:
                    whitelist_object[pos.split(':')[-1]] = whitelist
                    whitelist = pos.split(':')[-1]

            # creation and filling of dictionary containing all necessary
            # information for one input field
            part_object = {'position': pos, 'mandatory': node['mandatory'],
                           'list': node['list'],
                           'displayName': node['display_name'],
                           'desc': node['desc'], 'value': None,
                           'whitelist': whitelist,
                           'whitelist_type': whitelist_type,
                           'input_type': input_type,
                           'input_disabled': input_disabled}

            # special case : value unit -> add key value_unit to dict
            if input_type == 'value_unit':
                part_object['value_unit'] = node['value']['unit']['value']

            if headers is not None:
                part_object['headers'] = headers
            if whitelist_keys is not None:
                part_object['whitelist_keys'] = whitelist_keys

        # no special case -> the value takes a dictionary and should be
        # displayed via an expandable
        else:

            # initialize variable input_fields with empty list
            # it is used to save the keys of the 'value' dictionary as input
            # fields
            input_fields = []

            # iterate over all keys in value
            for key in node['value']:

                # call this function to create a dictionary object for all keys
                # storing their necessary information
                field_infos, w_object = parse_empty(
                    node['value'][key], pos + ':' + key, key_yaml,
                    filled_object, get_whitelist_object=get_whitelist_object)

                input_fields.append(field_infos)
                whitelist_object = {**whitelist_object, **w_object}

            # creation and filling of dictionary containing all necessary
            # information for one expandable with its input fields
            part_object = {'position': pos, 'mandatory': node['mandatory'],
                           'list': node['list'], 'title': node['display_name'],
                           'desc': node['desc'], 'input_fields': input_fields,
                           'input_disabled': input_disabled}

        # test if the key takes multiple values and add the property
        # 'list_value' as a place to save those values to via the website
        if node['list']:
            part_object['list_value'] = []

    # the key does not contain a dictionary as value
    else:

        # read and parse whitelist
        whitelist, whitelist_type, input_type, headers, whitelist_keys = \
            whitelist_parsing.parse_whitelist(pos.split(':')[-1], node,
                                              filled_object)

        if get_whitelist_object and whitelist is not None:

            # set the whitelist to the name of the key if a whitelist was
            # defined
            whitelist_object[pos.split(':')[-1]] = whitelist
            whitelist = pos.split(':')[-1]

        # creation and filling of dictionary containing all necessary
        # information for one input field
        part_object = {'position': pos, 'mandatory': node['mandatory'],
                       'list': node['list'],
                       'displayName': node['display_name'],
                       'desc': node['desc'], 'value': node['value'],
                       'whitelist': whitelist,
                       'whitelist_type': whitelist_type,
                       'input_type': input_type,
                       'input_disabled': input_disabled}

        if headers is not None:
            part_object['headers'] = headers
        if whitelist_keys is not None:
            part_object['whitelist_keys'] = whitelist_keys

        # test if the key takes multiple values or uses autofill and add the
        # property 'list_value' as a place to save those values to via the
        # website
        if node['list'] or input_type == 'single_autofill':
            part_object['list_value'] = []

        # add the key 'search_info' to all fields using autofill to help get
        # the correct whitelist via the website
        if input_type == 'single_autofill' or input_type == 'multi_autofill':
            part_object['search_info'] = {
                'organism': None,
                'key_name': part_object['position'].split(':')[-1]}

    return part_object, whitelist_object
