import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.wi_utils as wi_utils
import copy


def get_factors(organism, key_yaml):
    """
    This function returns all experimental factors with a whitelist of their
    values
    :param key_yaml: the read in general structure
    :param organism: the organism that was selected by the user
    :return: factor_value: a dictionary containing factors and whitelists
    """

    # initialize dictionary with all factors
    factor_value = {'factor': utils.read_whitelist('factor')['whitelist']}

    # initialize empty dictionary to store values of each factor
    values = {}

    # iterate over factors
    for factor in factor_value['factor']:

        # get attributes of factor from general structure
        node = list(utils.find_keys(key_yaml, factor))

        # factor was found in general structure
        if len(node) > 0:

            # call function 'get_factor_values' to get whitelist information
            whitelist, whitelist_type, input_type, headers, w_keys = \
                get_factor_values(factor, node[0], {'organism': organism})

            # change single_autofill to multi_autofill because all factors can
            # have multiple values
            if input_type == 'single_autofill':
                input_type = 'multi_autofill'

            # save whitelist, input_type and whitelist_type for the values of
            # one factor
            values[factor] = {'whitelist': whitelist,
                              'input_type': input_type,
                              'whitelist_type': whitelist_type}

            # add search_info if input is of type single- or multi-autofill
            if input_type == 'multi_autofill':
                values[factor]['search_info'] = {'organism': organism,
                                                 'key_name': factor}

            # add header and whitelist keys if they are defined
            if headers is not None:
                values[factor]['headers'] = headers
            if w_keys is not None:
                values[factor]['whitelist_keys'] = w_keys

    # add the values to the dictionary
    factor_value['values'] = values

    return factor_value


def get_factor_values(key, node, filled_object):
    """
    This function is used to get the whitelists of experimental factors
    including the whitelist type, input type, headers and whitelist keys
    :param key: the name of the experimental factor
    :param node: the part of the general structure containing information of
                 the factor
    :param filled_object: a dictionary storing the used organism and used for
                          parsing of whitelists of type 'depend' (dependent
                          on organism)
    :return:
    whitelist: a list or dictionary of available values for input (type depends
               on whitelist_type)
    whitelist_type: the type of the whitelist (e.g. plain, group, ...)
    input_type: the input type for the input field in the web interface (e.g.
                short_text, select, single_autofill, ...)
    headers: the headers of the whitelist (None if no headers are defined)
    w_keys: the keys of a whitelist of type group that was rewritten to type
            plain (None if the whitelist is not plain group)
    """

    # initialize headers, whitelist keys and whitelist type with None
    headers = None
    w_keys = None
    whitelist_type = None

    # value is a dictionary and no special case
    if isinstance(node['value'], dict) and not (
            'special_case' in node and ('merge' in node['special_case'] or
                                        'value_unit' in node['special_case'])):

        # initialize whitelist as empty list
        whitelist = []

        # iterate over the keys of the value
        for k in node['value']:

            # initialize an empty dictionary to store the properties of
            # the key
            k_val = {}

            # call this function to get the whitelist information for the keys
            k_val['whitelist'], k_val['whitelist_type'], k_val['input_type'], \
                header, whitelist_keys = get_factor_values(k, node['value'][k],
                                                           filled_object)

            # add header and whitelist keys to dictionary if they are defined
            if header is not None:
                k_val['headers'] = header
            if whitelist_keys is not None:
                k_val['whitelist_keys'] = whitelist_keys

            # add key 'unit' if key is of special case value_unit
            if k_val['input_type'] == 'value_unit':
                k_val['unit'] = None

            # add properties from the general structure
            k_val['displayName'] = node['value'][k]['display_name']
            k_val['required'] = node['value'][k]['mandatory']
            k_val['position'] = k
            k_val['value'] = []

            # change single_autofill to multi_autofill because all factors can
            # have multiple values
            if k_val['input_type'] == 'single_autofill':
                k_val['input_type'] = 'multi_autofill'

            # add search info if the input is of type single- or multi-autofill
            if k_val['input_type'] == 'multi_autofill':
                k_val['whitelist'] = None
                k_val['search_info'] = {'organism': filled_object['organism'],
                                        'key_name': k}

            # add dictionary with properties of the key to the whitelist
            whitelist.append(k_val)

        # set input type to nested
        input_type = 'nested'

    # value is not a dictionary or special_case: merge or value_unit
    else:

        # read and parse whitelist
        whitelist, whitelist_type, input_type, headers, w_keys = \
            whitelist_parsing.parse_whitelist(key, node,
                                              filled_object)

    # factor takes a list as value -> can occur multiple times in one condition
    if node['list']:

        # values are single values (no dictionaries)
        if not isinstance(node['value'], dict):

            # change single_autofill to multi_autofill because all factors can
            # have multiple values
            if input_type == 'single_autofill':
                input_type = 'multi_autofill'

            # create a dictionary that contains all properties of the factor
            new_w = {'whitelist': whitelist, 'position': key,
                     'displayName': node['display_name'], 'required': True,
                     'value': [], 'input_type': input_type,
                     'whitelist_type': whitelist_type}

            # add search info if factor is of type single- or multi-autofill
            if input_type == 'multi_autofill':
                new_w['whitelist'] = None
                new_w['search_info'] = {'organism': filled_object['organism'],
                                        'key_name': key}

            # set the dictionary with the properties of the factor as one value
            # of the whitelist
            # -> moved factor down one level
            # -> needed in order to add second key 'Multi' (see below)
            whitelist = [new_w]
            whitelist_type = 'list_select'

            # set input type to nested
            input_type = 'nested'

        # add the key 'Multi'
        # -> used for experimental factors of type list
        # -> True if one factor can occur multiple times in one condition
        whitelist.append({'displayName': 'Multi', 'position': 'multi',
                          'whitelist': [True, False], 'input_type': 'bool',
                          'value': False})

    return whitelist, whitelist_type, input_type, headers, w_keys


def get_conditions(factors, organism_name, key_yaml):
    """
    This function creates all combinations of selected experimental factors and
    their values
    :param key_yaml: the read in general structure
    :param organism_name: the selected organism
    :param factors: multiple dictionaries containing the keys 'factor' and
    'values' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a dictionary containing the following keys:
             conditions: a condition object containing a list of all conditions
                         saved as dictionaries
             whitelist_object: a dictionary containing all keys that store a
                               whitelist and their whitelist
             organism: the organism that was chosen by the user
    """

    # initialize an empty dictionary to store the values as they are displayed
    # on the website -> used if there are headers or whitelist keys
    # e.g. value 'GFP' is displayed as 'GFP (other)' on the website since the
    # value is stored in a grouped whitelist that was refactored to plain
    real_val = {}

    # iterate over factors
    for i in range(len(factors)):

        # extract the properties of the factor from the general structure
        factor_infos = list(utils.find_keys(key_yaml, factors[i]['factor']))

        # sanity check -> factor was found in general structure and
        # list of values contains only one element
        if len(factor_infos) > 0 and len(factors[i]['values'] == 1):

            # set val to the values specified for the factor
            val = factors[i]['values'][0]

            # value is a dictionary -> e.g. disease
            if isinstance(val, dict):

                # initialize multi with False -> bool to define weather a
                # factor can occur multiple times in one condition
                multi = False

                # remove keys with value None or empty lists and dictionaries
                val = {k: v for k, v in val.items() if
                       not (type(v) in [list, dict] and len(v) == 0)
                       and v is not None}

                # add an ident key to the value
                # -> defined in general structure or None
                val['ident_key'] = factor_infos[0]['special_case']['group'] if\
                    'special_case' in factor_infos[0] and 'group' in \
                    factor_infos[0]['special_case'] else None

                # multi was defined in the value (user input)
                if 'multi' in val:

                    # set multi to the value defined by the user if an ident
                    # key is defined else False
                    multi = False if val['ident_key'] is None else \
                            val['multi']

                # test if the value of the factor contains just the 'factor',
                # 'multi' and 'ident_key' as keys
                # -> this is the case if a factor takes a list of single values
                # -> then the value had to be converted to a dictionary to
                # include the key 'multi' which is undone here
                if all(k in ['multi', factors[i]['factor'], 'ident_key'] for k
                       in list(val.keys())):

                    # overwrite val with the values under the key <factor> in
                    # val
                    val = val[factors[i]['factor']]

                # generate combinations of the values of the dictionary for the
                # conditions and overwrite the values with them
                factors[i]['values'] = generate.get_combis(
                    val, factors[i]['factor'], multi)

        # iterate over all values
        for j in range(len(factors[i]['values'])):

            # factor contains whitelist keys
            if 'whitelist_keys' in factors[i]:

                # save the original value as full_value
                full_value = copy.deepcopy(factors[i]['values'][j])

                # save the headers if they are specified for the factor else
                # None
                headers = factors[i]['headers'] if 'headers' in factors[i] \
                    else None

                # rewrite the values by removing the whitelist keys and split
                # them according to the headers if headers were defined
                factors[i]['values'][j] = wi_utils.parse_whitelist_keys(
                    factors[i]['whitelist_keys'], factors[i]['values'][j],
                    headers, mode='str')

                # headers were defined and the whitelist key of the value is
                # defined within the headers
                if headers is not None and full_value.split('(')[-1].replace(
                        ')', '') in headers:

                    # rewrite the value to '<factor>:{<values>}'
                    factors[i]['values'][j] = f'{factors[i]["factor"]}:{"{"}' \
                                              f'{factors[i]["values"][j]}{"}"}'

                # save the original value in real_val with the new value as key
                real_val[factors[i]['values'][j]] = full_value

            # factor contains headers but not whitelist keys
            elif 'headers' in factors[i]:

                # save the original value
                full_value = copy.deepcopy(factors[i]['values'][j])

                # split the value according to the header and save them as a
                # string
                str_value = wi_utils.parse_headers(
                    factors[i]['headers'], factors[i]['values'][j], mode='str')

                # # rewrite the value to '<factor>:{<values>}'
                factors[i]['values'][j] = f'{factors[i]["factor"]}:{"{"}' \
                                          f'{str_value}{"}"}'

                # save the original value in real_val with the new value as key
                real_val[factors[i]['values'][j]] = full_value

    # generate the conditions
    conditions = generate.get_condition_combinations(factors)

    # extract the properties of 'sample' from the general structure
    sample = list(utils.find_keys(key_yaml, 'samples'))

    # initialize a condition- and a whitelist object
    condition_object = []
    whitelist_object = {}

    # sanity check -> sample was found in the general structure
    if len(sample) > 0:

        # create an emtpy wi_object and a whitelist object from the sample
        # structure
        sample, whitelist_object = yto.parse_empty(
            sample[0],
            'experimental_setting:conditions:biological_replicates:samples',
            key_yaml, {'organism': organism_name}, get_whitelist_object=True)

        # overwrite sample with its input fields
        sample = sample['input_fields']

        # iterate over conditions
        for cond in conditions:

            # generate a sample name from the condition
            sample_name = generate.get_short_name(cond, {})

            # split the condition into key-value pairs
            split_condition = generate.split_cond(cond)

            # call functions to fill the samples with the values from the
            # condition
            filled_sample = get_samples(split_condition, copy.deepcopy(sample),
                                        real_val, key_yaml, sample_name)

            # TODO: improve display
            # save the condition as a dictionary with the filled sample as
            # input fields
            d = {'correct_value': cond,
                 'title': cond.replace(':', ': ').replace('|',
                                                          '| ').replace(
                     '#', '# ').replace('-', ' - '),
                 'position': 'experimental_setting:condition',
                 'list': True, 'mandatory': True, 'list_value': [],
                 'input_disabled': False, 'desc': '',
                 'input_fields': copy.deepcopy(filled_sample)}

            # add the dictionary for the condition to the condition object
            condition_object.append(d)

    return {'conditions': condition_object,
            'whitelist_object': whitelist_object, 'organism': organism_name}


def get_samples(split_condition, sample, real_val, key_yaml, sample_name):
    """
    This function created a pre-filled object with the structure of the samples
    to be displayed in the web interface
    :param sample_name: the identifier of the sample build from the condition
    :param key_yaml: the read in general structure
    :param real_val: a dictionary containing the values containing headers and
                     whitelist keys as they should be displayed on the website
    :param split_condition: the condition the sample is created for
    :param sample: the empty structure of the sample
    :return: sample: the pre-filled sample
    """

    # save all factors in a list
    factors = [cond[0] for cond in split_condition]

    # iterate over samples
    for i in range(len(sample)):

        # input field: sample_name
        if sample[i]['position'].endswith('samples:sample_name'):

            # TODO: improve display
            # add whitespaces to sample name to enable line breaks on the
            # website
            sample[i]['value'] = sample_name \
                .replace(':', ': ') \
                .replace('|', '| ') \
                .replace('#', '# ') \
                .replace('-', ' - ') \
                .replace('+', ' + ')

            # save the unchanged sample name as 'correct_value'
            sample[i]['correct_value'] = sample_name

        # input field is a factor
        elif sample[i]['position'].split(':')[-1] in factors:

            # iterate over factors in condition
            for c in split_condition:

                # input field of current factor
                if sample[i]['position'].split(':')[-1] == c[0]:

                    # extract properties of the factor from the general
                    # structure
                    info = list(utils.find_keys(key_yaml, c[0]))

                    # sanity check -> factor was found in general structure
                    if len(info) > 0:

                        # special case value_unit
                        if 'special_case' in info[0] and 'value_unit' \
                                in info[0]['special_case']:

                            # split the value into value and unit
                            value_unit = wi_utils.split_value_unit(c[1])

                            # save the value and unit in the sample
                            sample[i]['value'] = value_unit['value']
                            sample[i]['value_unit'] = value_unit['unit']

                        # value is a dictionary
                        elif isinstance(c[1], dict):

                            # rewrite the value into a string
                            val = "|".join(
                                [f'{key}:"{c[1][key]}"' for key in c[1]])
                            val = f'{c[0]}:{"{"}{val}{"}"}'

                            # save the value from the dictionary real_val if
                            # real_val contains the current value as key
                            if val in real_val:
                                filled_value = real_val[val]

                            # value is not in real_val
                            else:

                                # call this function on the keys of the value
                                # in order to fill them
                                filled_value = get_samples(
                                    [(x, c[1][x]) for x in c[1]],
                                    copy.deepcopy(sample[i]['input_fields']),
                                    info, key_yaml, sample_name)

                            # save the filled value in 'list_value' if the
                            # input field takes a list
                            if sample[i]['list']:
                                sample[i]['list_value'].append(filled_value)

                            # save the filled value in 'input_fields' if the
                            # input field takes a dictionary
                            elif 'input_fields' in sample[i]:
                                sample[i]['input_fields'] = filled_value

                            # save the filled value in 'value'
                            else:
                                sample[i]['value'] = filled_value

                        # value is not a dictionary
                        else:

                            # save the value from the dictionary real_val if it
                            # contains the current value
                            if c[1] in real_val:
                                filled_value = real_val[c[1]]

                            # save the current value
                            else:
                                filled_value = c[1]

                            # save the filled value in 'list_value' if the
                            # input field takes a list
                            if sample[i]['list']:
                                sample[i]['list_value'].append(filled_value)

                            # save the filled value in 'value'
                            else:
                                sample[i]['value'] = filled_value

                        # input field is of type single_autofill
                        if 'input_type' in sample[i] and \
                                sample[i]['input_type'] == 'single_autofill':

                            # initialize the key 'list_value' and move the
                            # value under the key 'value' to the key
                            # 'list_value'
                            sample[i]['list_value'] = [] if \
                                sample[i]['value'] is None \
                                else [sample[i]['value']]

                        # disable the input for the filled input field
                        sample[i]['input_disabled'] = True

    return sample
