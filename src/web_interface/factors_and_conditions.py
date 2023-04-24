import src.utils as utils
import src.generate_metafile as generate
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.wi_utils as wi_utils
import copy


def get_factors(organism, key_yaml):
    """
    This function returns all experimental factors with a whitelist of their
    values.
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
    their values.
    :param organism_name: the selected organism
    :param factors: multiple dictionaries containing the keys 'factor' and
    'values' with their respective values grouped in a list
    e.g. [{'factor': 'gender', 'values': ['male', 'female']},
          {'factor: 'life_stage', 'values': ['child', 'adult']}]
    :return: a list containing all combinations of conditions
    """

    real_val = {}

    for i in range(len(factors)):

        factor_infos = list(utils.find_keys(key_yaml, factors[i]['factor']))

        if len(factor_infos) > 0:

            val = factors[i]['values'][0]

            if isinstance(val, dict):

                multi = False

                val = {k: v for k, v in val.items() if v is not None}

                val['ident_key'] = factor_infos[0]['special_case']['group'] if\
                    'special_case' in factor_infos[0] and 'group' in \
                    factor_infos[0]['special_case'] else None

                if 'multi' in val:

                    multi = False if val['ident_key'] is None else \
                            val['multi']

                if all(k in ['multi', factors[i]['factor'], 'ident_key'] for k
                       in list(val.keys())):
                    val = val[factors[i]['factor']]

                factors[i]['values'] = generate.get_combis(
                    val, factors[i]['factor'], multi)

        for j in range(len(factors[i]['values'])):
            if 'whitelist_keys' in factors[i]:

                full_value = copy.deepcopy(factors[i]['values'][j])
                headers = factors[i]['headers'] if 'headers' in factors[i] \
                    else None
                factors[i]['values'][j] = wi_utils.parse_whitelist_keys(
                    factors[i]['whitelist_keys'], factors[i]['values'][j],
                    headers, mode='str')

                if headers is not None:
                    factors[i]['values'][j] = f'{factors[i]["factor"]}:{"{"}' \
                                              f'{factors[i]["values"][j]}{"}"}'

                real_val[factors[i]['values'][j]] = full_value

            # TODO: real_val?
            elif 'headers' in factors[i]:

                str_value = wi_utils.parse_headers(
                    factors[i]['headers'], factors[i]['values'][j], mode='str')
                factors[i]['values'][j] = f'{factors[i]["factor"]}:{"{"}' \
                                          f'{str_value}{"}"}'

    conditions = generate.get_condition_combinations(factors)

    sample = list(utils.find_keys(key_yaml, 'samples'))
    whitelists = {}
    condition_object = []

    if len(sample) > 0:
        sample, whitelist_object = yto.parse_empty(
            sample[0], 'experimental_setting:conditions:biological_replicates:samples', key_yaml, {'organism': organism_name},
            get_whitelist_object=True)
        sample = sample['input_fields']

        #for item in sample:
        #    item, whitelists = whitelist_parsing.get_whitelist_object(
        #        item, organism, whitelists)

        for cond in conditions:
            cond_sample = copy.deepcopy(sample)
            cond_sample = get_samples(cond, cond_sample, real_val, key_yaml)
            d = {'correct_value': cond,
                 'title': cond.replace(':', ': ').replace('|',
                                                          '| ').replace(
                     '#', '# ').replace('-', ' - '),
                 'position': 'experimental_setting:condition',
                 'list': True, 'mandatory': True, 'list_value': [],
                 'input_disabled': False, 'desc': '',
                 'input_fields': copy.deepcopy(cond_sample)}
            condition_object.append(d)

    return {'conditions': condition_object,
            'whitelist_object': whitelist_object, 'organism': organism_name}


def get_samples(condition, sample, real_val, key_yaml):
    """
    This function created a pre-filled object with the structure of the samples
    to be displayed in the web interface.
    :param condition: the condition the sample is created for
    :param sample: the empty structure of the sample
    :return: sample: the pre-filled sample
    """
    conds = generate.split_cond(condition)

    for i in range(len(sample)):
        if sample[i]['position'] == 'experimental_setting:conditions:biological_replicates:samples:sample_name':
            sample_name = generate.get_short_name(condition, {})
            sample[i]['value'] = sample_name \
                .replace(':', ': ') \
                .replace('|', '| ') \
                .replace('#', '# ') \
                .replace('-', ' - ') \
                .replace('+', ' + ')
            sample[i]['correct_value'] = sample_name
        for c in conds:
            if sample[i]['position'] == f'experimental_setting:conditions:biological_replicates:samples:{c[0]}':
                info = list(utils.find_keys(key_yaml, c[0]))
                if len(info)>0 and 'special_case' in info[0] and 'value_unit' in info[0]['special_case']:
                    unit = c[1].lstrip('0123456789')
                    value = c[1][:len(c[1]) - len(unit)]
                    sample[i]['value'] = int(value)
                    sample[i]['value_unit'] = unit
                elif isinstance(c[1], dict):
                    val = f'{c[0]}:{"{"}'
                    for l in range(len(list(c[1].keys()))):
                        val = f'{val}{"|" if l > 0 else ""}{list(c[1].keys())[l]}:"{c[1][list(c[1].keys())[l]]}"'
                    val = f'{val}{"}"}'
                    if val in real_val:
                        sample[i]['value'] = real_val[val]
                    else:
                        if sample[i]['list']:
                            filled_sample = copy.deepcopy(sample[i]
                                                          ['input_fields'])
                            for j in range(len(filled_sample)):
                                for x in c[1]:
                                    if filled_sample[
                                        j]['position'].split(':')[-1] == x:
                                        sub_info = list(utils.find_keys(key_yaml, x))
                                        if len(sub_info)>0 and 'special_case' in sub_info[0] and 'value_unit' in sub_info[0]['special_case']:
                                            unit = c[1][x].lstrip('0123456789')
                                            value = c[1][x][:len(c[1][x]) -
                                                             len(unit)]
                                            filled_sample[j]['value'] = \
                                                int(value)
                                            filled_sample[j]['value_unit'] = \
                                                unit
                                        else:
                                            filled_sample[j]['value'] = c[1][x]
                                        filled_sample[j]['input_disabled'] = \
                                            True
                            sample[i]['list_value'].append(filled_sample)
                        else:
                            if 'input_fields' in sample[i]:
                                for j in range(len(sample[i]['input_fields'])):
                                    for x in c[1]:
                                        if sample[i]['input_fields'][j][
                                            'position'].split(':')[-1] == x:
                                            sub_info = utils.find_keys(
                                                key_yaml, x)
                                            if len(sub_info) > 0 and 'special_case' in sub_info[0] and 'value_unit' in sub_info[0]['special_case']:
                                                unit = c[1][x].lstrip(
                                                    '0123456789')
                                                value = c[1][x][
                                                        :len(c[1][x]) - len(
                                                            unit)]
                                                sample[i]['input_fields'][j][
                                                    'value'] = int(value)
                                                sample[i]['input_fields'][j][
                                                    'value_unit'] = unit
                                            else:
                                                sample[i]['input_fields'][j][
                                                    'value'] = c[1][x]
                            else:
                                val = ""
                                for key in c[1]:
                                    val = f'{val}{" " if val != "" else ""}{c[1][key]}'
                                sample[i]['value'] = val
                else:
                    if sample[i]['list']:
                        sample[i]['list_value'].append(c[1])
                        sample[i]['input_disabled'] = True
                    else:
                        if c[1] in real_val:
                            sample[i]['value'] = real_val[c[1]]
                        else:
                            sample[i]['value'] = c[1]
                if 'input_type' in sample[i] and sample[i]['input_type'] == 'single_autofill':
                    sample[i]['list_value'] = [] if sample[i][
                                                        'value'] is None else [
                        sample[i]['value']]
                sample[i]['input_disabled'] = True
    return sample
