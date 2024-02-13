import src.utils as utils
import src.web_interface.whitelist_parsing as whitelist_parsing
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.wi_utils as wi_utils
import copy
import re


def get_factors(organism, key_yaml):
    """
    This function returns all experimental factors with a whitelist of their
    values
    :param key_yaml: the read in general structure
    :param organism: the organism that was selected by the user
    :return: factor_value: a dictionary containing factors and whitelists
    """

    factor_desc = list(utils.find_keys(key_yaml, 'experimental_factors'))[0]['factor_desc']
    f_node = list(utils.find_keys(key_yaml, 'factor'))[0]
    # initialize dictionary with all factors
    factor_list, whitelist_type, input_type, headers, whitelist_keys, double = \
        whitelist_parsing.parse_whitelist(
            'factor', f_node, {'organism': organism})

    factor_value = {'factor': factor_list, 'desc': factor_desc}
    plain_factors = []

    for elem in factor_list:
        plain_factors += elem['whitelist']
    # initialize empty dictionary to store values of each factor
    values = {}

    # iterate over factors
    for factor in plain_factors:

        # get attributes of factor from general structure
        node = list(utils.find_keys(key_yaml, factor))

        # factor was found in general structure
        if len(node) > 0:

            # call function 'get_factor_values' to get whitelist information
            whitelist, whitelist_type, input_type, headers, w_keys, double, nested_infos = \
                get_factor_values(factor, node[0], {'organism': organism})

            # change single_autofill to multi_autofill because all factors can
            # have multiple values
            if input_type == 'single_autofill':
                input_type = 'multi_autofill'

            # save whitelist, input_type and whitelist_type for the values of
            # one factor
            values[factor] = {'whitelist': whitelist,
                              'input_type': input_type,
                              'whitelist_type': whitelist_type,
                              'displayName': node[0]['display_name'],
                              'desc': utils.print_desc(node[0]['factor_desc'] if 'factor_desc' in node[0] else node[0]['desc'], 'html').replace('\n','<br>')}

            # add search_info if input is of type single- or multi-autofill
            if input_type == 'multi_autofill':
                values[factor]['search_info'] = {'organism': organism,
                                                 'key_name': factor}

            if input_type == 'restricted_short_text':
                # default
                values[factor]['restriction'] = {'regex': ' ',
                                                 'max_length': 10}

                if 'special_case' in node and 'restriction' in node['special_case']:
                    if 'regex' in node['special_case']['restriction']:
                        values[factor]['restriction']['regex'] = \
                            node['special_case']['restriction']['regex']
                    if 'max_length' in node['special_case']['restriction']:
                        values[factor]['restriction']['max_length'] = \
                            node['special_case']['restriction']['max_length']

            # add header and whitelist keys if they are defined
            if headers is not None:
                values[factor]['headers'] = headers
            if w_keys is not None:
                values[factor]['whitelist_keys'] = w_keys
            if len(double) > 0:
                values[factor]['double'] = double
            if nested_infos is not None:
                values[factor]['nested_infos'] = nested_infos

    # add the values to the dictionary
    factor_value['values'] = values

    return factor_value


def get_factor_values(key, node, filled_object, nested_infos=None):
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
    double = []

    # value is a dictionary and no special case
    if isinstance(node['value'], dict) and not (
            'special_case' in node and ('merge' in node['special_case'] or
                                        'value_unit' in node['special_case'])):

        # initialize whitelist as empty list
        whitelist = []
        nested_infos = {}

        # iterate over the keys of the value
        for k in node['value']:

            key_info = {}

            # initialize an empty dictionary to store the properties of
            # the key
            k_val = {}

            # call this function to get the whitelist information for the keys
            k_val['whitelist'], k_val['whitelist_type'], k_val['input_type'], \
                header, whitelist_keys, doubled, nested_infos = get_factor_values(k, node['value'][k],
                                                           filled_object, nested_infos=nested_infos)

            # add header and whitelist keys to dictionary if they are defined
            if header is not None:
                k_val['headers'] = header
                key_info['headers'] = header
            if whitelist_keys is not None:
                k_val['whitelist_keys'] = whitelist_keys
                key_info['whitelist_keys'] = whitelist_keys
            if len(doubled) > 0:
                k_val['double'] = doubled
                key_info['double'] = doubled

            # add key 'unit' if key is of special case value_unit
            if k_val['input_type'] == 'value_unit':
                k_val['unit'] = None

            # add properties from the general structure
            k_val['displayName'] = node['value'][k]['display_name']
            k_val['required'] = node['value'][k]['mandatory']
            k_val['position'] = k
            k_val['value'] = []
            k_val['desc'] = node['value'][k]['desc']

            # change single_autofill to multi_autofill because all factors can
            # have multiple values
            if k_val['input_type'] == 'single_autofill':
                k_val['input_type'] = 'multi_autofill'

            if k_val['input_type'] == 'restricted_short_text':

                # default
                k_val['restriction'] = {'regex': ' ', 'max_length': 10}

                if 'special_case' in node['value'][k] and 'restriction' in  \
                        node['value'][k]['special_case']:
                    if 'regex' in  node['value'][k]['special_case'][
                            'restriction']:
                        k_val['restriction']['regex'] = \
                            node['value'][k]['special_case']['restriction'][
                                'regex']
                    if 'max_length' in node['value'][k]['special_case'][
                            'restriction']:
                        k_val['restriction']['max_length'] = \
                            node['value'][k]['special_case']['restriction'][
                                'max_length']

            # add search info if the input is of type single- or multi-autofill
            if k_val['input_type'] == 'multi_autofill':
                k_val['whitelist'] = None
                k_val['search_info'] = {'organism': filled_object['organism'],
                                        'key_name': k}

            # add dictionary with properties of the key to the whitelist
            whitelist.append(k_val)
            if len(key_info) > 0:
                nested_infos[k] = key_info

        # set input type to nested
        input_type = 'nested'
        if len(nested_infos) == 0:
            nested_infos = None

    # value is not a dictionary or special_case: merge or value_unit
    else:

        # read and parse whitelist
        whitelist, whitelist_type, input_type, headers, w_keys, double = \
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

    return whitelist, whitelist_type, input_type, headers, w_keys, double, nested_infos


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
        if len(factor_infos) > 0 and len(factors[i]['values']) == 1:

            # set val to the values specified for the factor
            val = factors[i]['values'][0]

            # value is a dictionary -> e.g. disease
            if isinstance(val, dict):

                # remove keys with value None or empty lists and dictionaries
                val = {k: v for k, v in val.items() if
                       not (type(v) in [list, dict] and len(v) == 0)
                       and v is not None}

                # add an ident key to the value
                # -> defined in general structure or None
                val['ident_key'] = factor_infos[0]['special_case']['group'] if\
                    'special_case' in factor_infos[0] and 'group' in \
                    factor_infos[0]['special_case'] else None

                val['control'] = factor_infos[0]['special_case']['control'] if\
                    'special_case' in factor_infos[0] and 'control' in \
                    factor_infos[0]['special_case'] else None

                for key in [x for x in list(val.keys()) if x not in ['multi', 'ident_key']]:

                    # TODO: headers + whitelist_keys

                    if key == 'gene':
                        for v in range(len(val[key])):

                            headers = 'gene_name ensembl_id'

                            # save the original value
                            full_value = copy.deepcopy(val[key][v])

                            # split the value according to the header and save them as a
                            # string
                            str_value = wi_utils.parse_headers(
                                        headers, val[key][v],
                                        mode='str')

                            # # rewrite the value to '<factor>:{<values>}'
                            val[key][v] = f'{key}:{"{"}' \
                                          f'{str_value}{"}"}'
                            # save the original value in real_val with the new value as key
                            real_val[val[key][v]] = full_value

                # generate combinations of the values of the dictionary for the
                # conditions and overwrite the values with them
                factors[i]['values'] = utils.get_combis(
                    val, factors[i]['factor'], {'organism': organism_name.split(' ')[0]}, key_yaml)

        elif factor_infos[0]['list']:

            factors[i]['values'] = utils.get_combis(factors[i]['values'], factors[i]['factor'], {'organism': organism_name.split(' ')[0]}, key_yaml)

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
    conditions = utils.get_condition_combinations(factors)

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
        sample_desc = sample['desc']
        sample = sample['input_fields']

        # iterate over conditions
        for cond in conditions:

            # generate a sample name from the condition
            sample_name = utils.get_short_name(cond, {'organism': organism_name}, key_yaml)

            # split the condition into key-value pairs
            split_condition = utils.split_cond(cond)
            search_condition = []

            # TODO: remove list (can there be a list?) or own function for items
            for elem in split_condition:
                if isinstance(elem[1], dict):
                    val = "|".join([f'{k}:"{elem[1][k]}"' for k in elem[1]])
                    val = f'{elem[0]}:{"{"}{val}{"}"}'
                    if val in real_val:
                        search_condition.append(f'{elem[0]}:"{real_val[val]}"'.lower())
                    else:
                        for key in elem[1]:
                            if isinstance(elem[1][key], dict):
                                val = "|".join(
                                    [f'{k}:"{elem[1][key][k]}"' for k in elem[1][key]])
                                val = f'{key}:{"{"}{val}{"}"}'
                                if val in real_val:
                                    search_condition.append(f'{elem[0]}:"{real_val[val]}"'.lower())
                            else:
                                search_condition.append(f'{elem[0]}:"{elem[1][key]}"'.lower())
                elif isinstance(elem[1], list):
                    for item in elem[1]:
                        search_condition.append(f'{elem[0]}:"{item}"'.lower())
                else:
                    if elem[1] in real_val:
                        search_condition.append(f'{elem[0]}:"{real_val[elem[1]]}"'.lower())
                    else:
                        search_condition.append(f'{elem[0]}:"{elem[1]}"'.lower())

            # call functions to fill the samples with the values from the
            # condition
            filled_sample = get_samples(split_condition, copy.deepcopy(sample),
                                        real_val, key_yaml, sample_name,
                                        organism_name)

            # rewrite condition into title and string to readd deleted
            # conditions
            title, readd = get_condition_title(split_condition)

            # save the condition as a dictionary with the filled sample as
            # input fields
            d = {'correct_value': cond,
                 'title': title,
                 'search': search_condition,
                 'readd': readd,
                 'position': 'experimental_setting:condition',
                 'list': True, 'mandatory': True, 'list_value': [],
                 'input_disabled': False, 'desc': sample_desc,
                 'input_fields': copy.deepcopy(filled_sample)}

            # add the dictionary for the condition to the condition object
            condition_object.append(d)

    return {'conditions': condition_object,
            'whitelist_object': whitelist_object, 'organism': organism_name}


def get_condition_title(split_condition):
    """
    This function rewrites a condition into a table to be displayed as a title
    on the website. It also creates a string that is shown when removed
    conditions have to be re-added
    :param split_condition: a list containing the factors and values the
                            condition consists of
    :return: html: the title as a table in html
             readd: the string shown when re-adding deleted conditions
    """

    # initialize the html string with the table header and style
    html = '<table class="table_style_condition_title"><tbody>'

    # initialize readd as an empty string
    readd = ''

    # iterate over the factors and values
    for i in range(len(split_condition)):

        # start the row of the table with the style depending on the index of
        # the element that is written into the row (the style creates a
        # horizontal line below the row and includes padding)
        if len(split_condition) > 1 and i < len(split_condition) - 1:
            html += '<tr class="tr_style_condition_title">'
        else:
            html += '<tr>'

        # add the factor to readd
        readd += f'{split_condition[i][0]}:\n'

        # add the factor to the table as a data cell with the style of a value
        # (padding)
        html += f'<td class="td_style_condition_title_value">' \
                f'{split_condition[i][0]}:</td>'

        vals, readd = get_title_value(split_condition[i][1], readd)

        # add the string with the values to the table as a data cell
        html += f'<td class="td_style_condition_title_value">{vals}'\
                f'</td></tr>'

        # if the condition consists of multiple factors than write a '---'
        # between them in readd
        if len(split_condition) > 1 and i < len(split_condition) - 1:
            readd += '---\n'

    # close the html table
    html += f'</tbody></table>'

    return html, readd


def get_title_value(cond_value, readd):

    # value is a dictionary
    if isinstance(cond_value, dict):

        # initialize an empty string to save the values to
        vals = ''

        # iterate over the keys
        for key in cond_value:

            value, readd = get_title_value(cond_value[key], readd)

            # add the value to the string with a <br> if it is not in the
            # last row
            if key != list(cond_value.keys())[-1]:
                vals += f'{value}<br>'
            else:
                vals += f'{value}'

    # value is not a dictionary
    else:

        # replace more than 3 zeros with 3 dots to shorten the value
        vals = f'"{re.sub("0000(0)*", "...", cond_value)}"'

        # add the value to readd
        readd += f'{vals}\n'

    return vals, readd


def get_samples(split_condition, sample, real_val, key_yaml, sample_name,
                organism_name, is_factor=True):
    """
    This function created a pre-filled object with the structure of the samples
    to be displayed in the web interface
    :param is_factor: a boolean defining if the input field is an experimental
                      factor
    :param organism_name: the name of the selected organism
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
            sample[i]['correct_value'] = sample_name.split('_')[0]

        #elif sample[i]['position'].endswith('samples:sequencer_name'):
        #    sample[i]['value'] = sequencer_name
        #    sample[i]['input_disabled'] = True

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

                            if isinstance(c[1], dict):
                                value_unit = c[1]
                            else:
                                # split the value into value and unit
                                value_unit = utils.split_value_unit(c[1])

                            # save the value and unit in the sample
                            sample[i]['value'] = value_unit['value']
                            sample[i]['value_unit'] = value_unit['unit']
                            if is_factor:
                                sample[i]['input_disabled'] = True

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

                                # TODO: rework with real_val

                                if 'input_fields' in sample[i]:
                                    # call this function on the keys of the
                                    # value in order to fill them
                                    filled_value = get_samples(
                                        [(x, c[1][x]) for x in c[1] #if not (
                                                #c[1] == 'technical_replicates'
                                                #and x == 'sample_name')
                                        ],
                                        copy.deepcopy(
                                            sample[i]['input_fields']),
                                        info, key_yaml, sample_name,
                                        organism_name, is_factor=is_factor)
                                # TODO: als real_val?
                                elif 'headers' in sample[i]:
                                    headers = [x for x in c[1]]
                                    w_key = None
                                    if isinstance(sample[i]['headers'], dict):

                                        for k in sample[i]['headers']:
                                            if sorted(
                                                    sample[i]['headers'][
                                                        k].split(' ')) == \
                                                    sorted(headers):
                                                w_key = k
                                                break
                                    else:
                                        if sorted(headers) != sorted(
                                                sample[i]['headers'].split(
                                                    ' ')):
                                            headers = None

                                    if headers is not None:
                                        filled_value = ''
                                        for header in headers:
                                            filled_value = filled_value + ' ' \
                                                           + c[1][header]
                                        filled_value = filled_value.lstrip(
                                            ' ').rstrip(' ')

                                    if filled_value is not None and w_key is \
                                            not None and \
                                            sample[i]['whitelist_type'] == \
                                            'plain_group':
                                        filled_value = f'{filled_value} ' \
                                                       f'({w_key})'

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

                                if sample[i]['whitelist_type'] == \
                                        'plain_group' and 'whitelist_keys' \
                                        in sample[i]:
                                    w = utils.get_whitelist(
                                        sample[i]['position'].split(':')[-1],
                                        {'organism': organism_name})

                                    for key in sample[i]['whitelist_keys']:
                                        if f'{c[1]} ({key})' in w['whitelist']:
                                            filled_value = f'{c[1]} ({key})'
                                            break
                                else:
                                    if 'input_type' in info[0] and info[0]['input_type'] == 'number':
                                        filled_value = int(c[1])
                                    else:
                                        filled_value = c[1]

                            # save the filled value in 'list_value' if the
                            # input field takes a list
                            if sample[i]['list']:
                                sample[i]['list_value'].append(filled_value)

                            # save the filled value in 'value'
                            else:
                                sample[i]['value'] = filled_value

                            if is_factor:
                                sample[i]['input_disabled'] = True

                        # input field is of type single_autofill
                        if 'input_type' in sample[i] and \
                                sample[i]['input_type'] in [
                                'single_autofill', 'restricted_short_text']:
                            # initialize the key 'list_value' and move the
                            # value under the key 'value' to the key
                            # 'list_value'
                            sample[i]['list_value'] = [] if \
                                sample[i]['value'] is None \
                                else [sample[i]['value']]
                            sample[i]['value'] = None

                            if is_factor:
                                # disable the input for the filled input field
                                sample[i]['input_disabled'] = True

                        if 'input_type' in sample[i] and sample[i]['input_type'] == 'bool':
                            if sample[i]['value']:
                                sample[i]['value'] = 'True'
                            else:
                                sample[i]['value'] = 'False'

    return sample
