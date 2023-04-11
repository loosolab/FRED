import src.utils as utils
import os

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
        wi_object[key] = parse_empty(key_yaml[key], key, key_yaml)

    # add a key 'all_factors' with an empty list as value to the object
    # the experimental factors will be saved here after input on the website
    wi_object['all_factors'] = []

    return wi_object


def parse_empty(node, pos, key_yaml, get_whitelists=True):
    """
    This function parses a part of the key.yaml into an object readable by the
    web-interface
    :param node: a part of the key.yaml that should be parsed
    :param pos: the position of the node (chained keys)
    :param key_yaml: the whole key.yaml
    :param get_whitelists: bool, True if whitelists should be included,
                           False if not, default True
    :return: part_object: an object for the web interface parsed from node
    """

    # disable input for the keys condition_name and sample_name because they
    # are generated
    input_disabled = True if pos.split(':')[-1] \
        in ['condition_name', 'sample_name'] else False

    # initialize whitelist type with None
    whitelist_type = None

    # test if the value of the current node is a dictionary
    if isinstance(node['value'], dict):

        # test for special case 'merge' -> it is used when two keys share a
        # whitelist (e.g. gene -> gene_name, ensemble_id)
        if 'special_case' in node and 'merge' in node['special_case']:

            # set the input type to select
            input_type = 'select'

            # test if whitelist should be included in the object
            if get_whitelists:

                # TODO: own function
                # read in whitelist
                whitelist = utils.get_whitelist(pos.split(':')[-1], {})

                # test if the right keys are present in the whitelist
                # -> format check
                if 'whitelist_type' in whitelist and 'whitelist' in whitelist:

                    # set whitelist type and whitelist
                    whitelist_type = whitelist['whitelist_type']
                    whitelist = whitelist['whitelist']

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

            else:

                # set whitelist to None if it should not be included
                whitelist = None

            # test if whitelist is longer than 30
            if whitelist and len(whitelist) > 30:

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

            # set input type of field organism to 'organism' -> special case
            if pos.split(':')[-1] == 'organism':
                input_type = 'organism_name'

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
                input_fields.append(parse_empty(node['value'][key],
                                                pos + ':' + key,
                                                key_yaml, get_whitelists))

            # test if the input fields are value_units
            if 'special_case' in node and 'value_unit' in node['special_case']:

                # initialize a whitelist for units
                unit_whitelist = []

                # iterate over the input fields to find the unit and save its
                # values to the unit_whitelist
                for i in range(len(input_fields)):
                    if input_fields[i]['position'].split(':')[-1] == 'unit':
                        unit_whitelist = input_fields[i]['whitelist']

                # creation and filling of dictionary containing all necessary
                # information for one input field of type value_unit
                part_object = {'position': pos, 'mandatory': node['mandatory'],
                               'list': node['list'],
                               'displayName': node['display_name'],
                               'desc': node['desc'], 'value': None,
                               'value_unit': node['value']['unit']['value'],
                               'whitelist': unit_whitelist,
                               'input_type': 'value_unit',
                               'input_disabled': input_disabled}

            # no special case -> display as expandable
            else:

                # creation and filling of dictionary containing all necessary
                # information for one expandable with its input fields
                part_object = {'position': pos, 'mandatory': node['mandatory'],
                               'list': node['list'],
                               'title': node['display_name'],
                               'desc': node['desc'],
                               'input_fields': input_fields,
                               'input_disabled': input_disabled}

        # test if the key takes multiple values and add the property
        # 'list_value' as a place to save those values to via the website
        if node['list']:
            part_object['list_value'] = []

    # the key does not contain a dictionary as value
    else:

        # set the input type as defined in the general structure
        input_type = node['input_type']

        # test if whitelists should be included in the object
        if get_whitelists:

            # test if a whitelist is defined for the current key
            if node['whitelist']:

                # read in whitelist
                whitelist = utils.get_whitelist(pos.split(':')[-1], {})

                # test if the right keys are present in the whitelist
                # -> format check
                if 'whitelist_type' in whitelist and 'whitelist' in whitelist:

                    # set whitelist type and whitelist
                    whitelist_type = whitelist['whitelist_type']
                    whitelist = whitelist['whitelist']

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

            # set whitelist to ['True', 'False'] and input type to 'select' if
            # a value of type boolean is requested
            elif input_type == 'bool':
                whitelist = [True, False]
                input_type = 'select'

            # set whitelist to None if none is defined
            else:
                whitelist = None

            # TODO: better solution for department
            # test if whitelist is longer than 30
            if whitelist and len(whitelist) > 30 and \
                    pos.split(':')[-1] != 'department':

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

        # whitelist should not be included
        else:

            # set the whitelist to the name of the key if a whitelist was
            # defined
            if node['whitelist'] or input_type == 'bool':
                whitelist = pos.split(':')[-1]

            # set the whitelist to None if no whitelist was defined
            else:
                whitelist = None

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

    return part_object
