import sys
from tabulate import tabulate
import src.utils as utils
import src.validate_yaml as validate_yaml
import datetime
import os
import readline
import re
import copy

try:
    size = os.get_terminal_size()
except OSError:
    size = 80
factor = []
not_editable = ['id', 'project_name', 'sample_name', 'pooled', 'donor_count',
                'technical_replicates']
id = ''

class WhitelistCompleter:
    def __init__(self, whitelist):
        self.whitelist = whitelist

    def complete(self, text, state):
        results = [x for x in self.whitelist if
                   re.search(text, x, re.IGNORECASE) is not None] + [None]
        if len(results) > 30:
            results = results[:30]
        return results[state]


# ---------------------------------GENERATE-------------------------------------

def generate_file(path, input_id, name, mandatory_mode):
    """
    This function is used to generate metadata by calling functions to compute
    user input. It writes the metadata into a yaml file after validating it.
    :param path: the path to the folder the metadata file should be saved to
    :param input_id: the ID of the experiment
    :param name: the name of the experiment
    :param mandatory_mode: if True only mandatory files are filled out
    """

    # TODO:
    global id
    id = input_id

    # TODO: overwrite?
    # test if metadata for give id already exists
    if os.path.exists(
            os.path.join(path, f'{input_id}_metadata.yaml')) or os.path.exists(
            os.path.join(path, f'{input_id}_metadata.yml')):
        sys.exit(
            f'The metadata file for ID {input_id} already exists.')

    # read in structure file
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))

    # create metadata dictionary and fill it with the given id and name
    result_dict = {'project': {'id': input_id, 'project_name': name}}

    # parse through metadata structure and fill it for every key
    for item in key_yaml:
        if item in result_dict:
            result_dict[item] = {**result_dict[item],
                                 **get_redo_value(key_yaml[item], item, False,
                                                  mandatory_mode, result_dict,
                                                  True, False)}
        else:
            result_dict[item] = get_redo_value(key_yaml[item], item, False,
                                               mandatory_mode, result_dict,
                                               True, False)

    # TODO: extra function for summary
    # print summary
    print(f'{"".center(size.columns, "-")}\n'
          f'{"SUMMARY".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    sum = print_summary(result_dict, 1, False)
    print(sum)
    print(f'\n\n')
    print(f'{"".center(size.columns, "-")}\n')

    print(f'{"".center(size.columns, "-")}\n'
          f'{"FILE VALIDATION".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    valid, missing_mandatory_keys, invalid_keys, invalid_entries, \
        invalid_values, pool_warn, ref_genome_warn = validate_yaml.\
        validate_file(result_dict)
    if not valid:
        validate_yaml.print_validation_report(
            result_dict, missing_mandatory_keys, invalid_keys,
            invalid_entries, invalid_values)
    else:
        print(f'Validation complete. No errors found.\n')

        utils.save_as_yaml(result_dict,
                           os.path.join(path, f'{input_id}_metadata.yaml'))
    print_sample_names(result_dict, input_id, path)


# TODO: add docs
# TODO: rename function
def get_redo_value(node, item, optional, mandatory_mode, result_dict,
                   first_node, is_factor):
    """

    :param node:
    :param item:
    :param optional:
    :param mandatory_mode:
    :param result_dict:
    :param first_node:
    :param is_factor:
    :return:
    """
    # test if the input value is of type list
    if node['list']:

        # test if one list element contains a dictionary
        if isinstance(node['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) <= \
                set(node['value'].keys()):
            # test if the input value is an experimental factor
            if is_factor:

                # TODO:
                value = fill_metadata_structure(node['value'], item, {}, optional,
                                                mandatory_mode, result_dict,
                                                first_node, is_factor)
            else:

                # repeat the input prompt for the keys of the list element
                # until the user specifies it is complete
                redo = True
                value = []
                while redo:
                    value.append(
                        fill_metadata_structure(node, item, {}, optional,
                                                mandatory_mode, result_dict,
                                                first_node, is_factor))
                    redo = parse_list_choose_one([True, False],
                                                 f'\nDo you want to add '
                                                 f'another {item}?')
        else:
            # enable the input of multiple elements of the whitelist
            value = get_input_list(node, item, result_dict)

    else:

        # test if the input value is an experimental factor and is either not
        # a dictionary or a dictionary that contains the key 'merge' as special
        # case (means that the input is treated like a single value and then
        # split into a dictionary, e.g. gene -> gene_name, ensembl_id)
        if is_factor and (not isinstance(node['value'], dict) or (isinstance(node['value'], dict) and \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) <= \
                set(node['value'].keys()) or \
                ('special_case' in node and 'merge' in node['special_case']))):

            # ask the user to put in a list of experimental factors
            value = get_input_list(node, item, result_dict)

        else:
            # call function to fill in value
            value = fill_metadata_structure(node, item, {}, optional,
                                            mandatory_mode, result_dict,
                                            first_node, is_factor)
    return value


# TODO: add docs
def fill_metadata_structure(node, key, return_dict, optional, mandatory_mode,
                            result_dict, first_node, is_factor):
    """

    :param node:
    :param key:
    :param return_dict:
    :param optional:
    :param mandatory_mode:
    :param result_dict:
    :param first_node:
    :param is_factor:
    :return:
    """

    # test if the given part of the metadata structure is a dictionary
    if isinstance(node, dict) and not \
            set(['mandatory', 'list', 'desc', 'display_name', 'value']) <= \
            set(node.keys()):

        # test if the input is of type value_unit
        if len(node.keys()) == 2 and 'value' in node.keys() and 'unit' in \
                node.keys():

            if is_factor:

                # call function to get a list of value_units if the input value
                # is an experimental factor
                return get_list_value_unit(result_dict, key)

            else:

                # call function to fill a single value_unit
                return get_value_unit(result_dict)

        else:

            # create a lists to store optional keys and their description
            optionals = []
            desc = []

            # iterate through all keys in the given part of the metadata
            # structure
            for item in node:

                # parameter to declare if a key is optional, False per default
                optional = False

                # if the key is 'experimental_factors', call a function to
                # choose the analyzed experimental factors and their respective
                # values and save them into the metadata dictionary
                if item == 'experimental_factors':
                    return_dict[item] = get_experimental_factors(node,
                                                                 return_dict)

                # if the key is 'conditions', call a function to create and
                # choose the analyzed conditions from the entered experimental
                # factors  and save them into the metadata dictionary
                elif item == 'conditions':
                    return_dict[item] = get_conditions(
                        copy.deepcopy(return_dict['experimental_factors']),
                        node[item]['value'],
                        mandatory_mode, return_dict)

                # test if the key is editable
                elif item not in not_editable:

                    # TODO: specify function
                    # if the key is mandatory, call the ... function on it
                    if node[item]['mandatory']:
                        return_dict[item] = get_redo_value(node[item], item,
                                                           optional,
                                                           mandatory_mode,
                                                           return_dict, False,
                                                           is_factor)

                    else:

                        # TODO:
                        if node[item]['list'] or item not in factor or is_factor:
                            optionals.append(item)
                            desc.append(node[item]['desc'])

            # if there are optional keys and mandatory mode is not active, ask
            # the user whether he wants to add optional information
            if len(optionals) > 0 and mandatory_mode == False:

                # set te optional parameter to True
                optional = True

                print(
                    f'\nDo you want to add any of the following optional keys?'
                    f' (1,...,{len(optionals)} or n)')

                # print a list of all optional keys
                print_option_list(optionals, desc)

                # parse the user input
                options = parse_input_list(optionals, True)

                if options:

                    # if the user chose optional keys, iterate through every
                    # chosen optional key
                    for option in options:

                        # TODO: runter rücken?
                        new_element = True

                        # test if the value for the optional key is of type
                        # list
                        if node[option]['list']:

                            # TODO: ??
                            if option in return_dict and all(
                                    isinstance(x, dict) for x in
                                    return_dict[option]):

                                # set the new_element parameter to False
                                new_element = False

                                # read in the structure file
                                key_yaml = utils.read_in_yaml(
                                    os.path.join(os.path.dirname(
                                        os.path.abspath(__file__)), '..',
                                        'keys.yaml'))

                                # list all possible keys that can occur in one
                                # list element of the optional key
                                possible_keys = list(list(
                                    utils.find_keys(
                                        key_yaml, option))[0]['value'].keys())

                                # create lists for list elements that contain
                                # optional keys that have no value yet and the
                                # descriptions of the list elements
                                elems = []
                                desc = []

                                # iterate through all list elements that
                                # already exist for the optional key
                                for i in range(len(return_dict[option])):

                                    # test if optional keys are missing in the
                                    # list element
                                    if not all(k in return_dict[option][i] for
                                               k in possible_keys):

                                        # add the list element with missing
                                        # optional keys to the 'elems' list
                                        elems.append(', '.join(
                                            [f'{k}: '
                                             f'{return_dict[option][i][k]}'
                                             for k in return_dict[option][i]]))

                                        # add a description of the list element
                                        # with missing optional keys to the
                                        # 'desc' list
                                        keys = ', '.join(
                                            [x for x in possible_keys if x
                                             not in return_dict[option][i]])
                                        desc.append(
                                            f'Possible information to add: '
                                            f'{keys}')

                                # test if list with list elems containing
                                # unfilled optional keys is not empty
                                if len(elems) > 0:

                                    # add an option for adding a new list value
                                    # to the 'elems' list (with empty desc)
                                    elems.append(f'Add new {option}')
                                    desc.append('')

                                    # print information for user that there are
                                    # existing list elements for the optional
                                    # key and let the user select if he wants
                                    # to add information to an existing list
                                    # element or create a new one + parse the
                                    # user input
                                    print(
                                        f'\nThere are existing elements for '
                                        f'{option}. Please select the elements'
                                        f' for which you want to add '
                                        f'information.\n')
                                    print_option_list(elems, desc)
                                    list_elems = parse_input_list(
                                        range(len(return_dict[option]) + 1),
                                        False)

                                    # iterate through the list elements the
                                    # user chose to add information
                                    for indc in list_elems:

                                        # test if the user chose an existing
                                        # list element to add information
                                        if int(indc) - 1 < len(
                                                return_dict[option]):

                                            # set a caption to show the user
                                            # which existing list element he is
                                            # about to edit and print it
                                            caption = elems[
                                                int(indc) - 1].replace("\n",
                                                                       ", ").\
                                                center(size.columns, ' ')
                                            line = ''.center(size.columns, '_')
                                            print(f'\n'
                                                  f'{line}\n\n'
                                                  f'List element: {caption}\n'
                                                  f'{line}\n')

                                            # save all unfilled optional keys
                                            # of the list element into a list
                                            possible_input = [
                                                x for x in possible_keys
                                                if x not in list(
                                                    return_dict[option]
                                                    [int(indc) - 1].keys())]

                                            # test if there are multiple
                                            # unfilled keys in the list element
                                            if len(possible_input) > 1:

                                                # copy the metadata structure
                                                # of the optional key
                                                part_node = copy.deepcopy(
                                                    node[option])

                                                # iterate through the keys
                                                # contained as value of the
                                                # optional key and those keys
                                                # to a list if they are
                                                # already filled
                                                remove_keys = []
                                                for k in part_node['value']:
                                                    if k not in possible_input:
                                                        remove_keys.append(k)

                                                # remove the filled keys from
                                                # the metadata structure of
                                                # the optional key
                                                for k in remove_keys:
                                                    part_node['value'].pop(k)

                                                # call the
                                                # fill_metadata_structure
                                                # function for the structure
                                                # of the optional key without
                                                # the already filled keys
                                                val = fill_metadata_structure(
                                                    part_node, option, {},
                                                    optional, mandatory_mode,
                                                    result_dict, False,
                                                    is_factor)

                                                # merge the prefilled optional
                                                # key with the new input
                                                # information
                                                return_dict[
                                                    option][int(indc) - 1] \
                                                    = merge_dicts(
                                                    return_dict[option][
                                                        int(indc) - 1], val)

                                            # if there is just one unfilled key
                                            else:

                                                # find the structure of the
                                                # unfilled key in the metadata
                                                # structure and save it
                                                part_node = list(
                                                    utils.find_keys(
                                                        key_yaml,
                                                        possible_input[0]))[0]

                                                # call function to fill the
                                                # unfilled key
                                                val = get_redo_value(
                                                    part_node,
                                                    possible_input[0],
                                                    optional, mandatory_mode,
                                                    result_dict, False,
                                                    is_factor)

                                                # save the now filled key in
                                                # the dictionary
                                                return_dict[option][
                                                    int(indc) - 1][
                                                    possible_input[0]] = val

                                        else:

                                            # if the user chose to add a new
                                            # element to the list, print a
                                            # caption for the new element and
                                            # set new_element to True

                                            h_line = ''.center(size.columns,
                                                               '_')
                                            caption = f'New {option}'.center(
                                                size.columns, ' ')
                                            print(f'\n'
                                                  f'{h_line}\n\n'
                                                  f'{caption}\n'
                                                  f'{h_line}\n')
                                            new_element = True

                                else:

                                    # set new_element to True if there are no
                                    # list elements with unfilled keys
                                    new_element = True

                        # create a new list element if new_element is set to
                        # True
                        if new_element:

                            if 'special_case' in node[option] and 'merge' in \
                                    node[option]['special_case']:
                                value = parse_input_value(option,
                                                          node[option]['desc'],
                                                          True, 'str',
                                                          result_dict)
                                return_dict[option] = value
                            else:
                                val = get_redo_value(node[option],
                                                     option,
                                                     optional,
                                                     mandatory_mode,
                                                     result_dict, False,
                                                     is_factor)
                                if node[option]['list']:
                                    if option in return_dict:
                                        return_dict[option] += val
                                    else:
                                        return_dict[option] = val
                                else:
                                    return_dict[option] = val
    else:
        if node['mandatory'] or optional or is_factor:
            if 'special_case' in node and 'merge' in node['special_case']:
                value = parse_input_value(key, node['desc'], True, 'str',
                                          result_dict)
            else:
                value = enter_information(node, key, return_dict, optional,
                                          mandatory_mode, result_dict,
                                          first_node, is_factor)
            return value
    return return_dict


#---------------------------EXPERIMENTAL SETTING-------------------------------


def get_experimental_factors(node, result_dict):
    """
    This function prompts the user to specify the examined experimental
    factors, as well as the analyzed values for each selected factor.
    :param node: TODO
    :param result_dict: a dictionary that contains all the information already
                        specified by the user
    :return: experimental_factors: a list containing a dictionary for every
             selected experimental factor with the factor and its values
    """

    # read in experimental factors from the factor whitelist
    factor_list = utils.get_whitelist('factor', result_dict)['whitelist']

    # ask the user to choose experimental factors and parse the user input
    print(
        f'\nPlease select the analyzed experimental factors '
        f'(1-{len(factor_list)}) divided by comma:\n')
    print_option_list(factor_list, False)
    used_factors = parse_input_list(factor_list, False)

    # create a list to store experimental factors with their selected values
    experimental_factors = []

    # iterate through all user chosen experimental factors
    for fac in used_factors:

        # search for the structure of the factor in the metadata structure and
        # save it
        fac_node = list(utils.find_keys(node, fac))[0]

        # call the get_redo_value function to fill in the values for the
        # experimental factor
        used_values = get_redo_value(fac_node, fac, False, False, result_dict,
                                     False, True)

        # if the experimental factor contains a dictionary as value and the
        # structure of the factor contains a group key than add the group key
        # to the values as ident_key
        # TODO: what is ident key for?
        if isinstance(
                fac_node['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) \
                <= set(fac_node['value'].keys()) and 'special_case' in \
                fac_node:
            if 'group' in fac_node['special_case']:
                used_values['ident_key'] = fac_node['special_case']['group']
            #elif 'merge' in fac_node['special_case']:
            #    used_values['ident_key'] = fac_node['special_case']['merge']

        # add a dictionary containing the experimental factor, its values and
        # if it contains a list to the experimental_factors list
        experimental_factors.append({'factor': fac,
                                     'values': used_values,
                                     'is_list': fac_node['list']})

    # set the global parameter factor to the user chosen experimental factors
    global factor
    factor = used_factors

    # return all chosen experimental factors with their values
    return experimental_factors


# elif fac_node[5]:
#    value_list = utils.get_whitelist(fac, result_dict)
#    if value_list and 'headers' in value_list:
#        headers = value_list['headers']
#    else:
#        headers = None
#    if value_list and 'whitelist_keys' in value_list:
#        whitelist_keys = value_list['whitelist_keys']
#    else:
#        whitelist_keys = None
#    if value_list and 'whitelist_type' in value_list:
#        whitelist_type = value_list['whitelist_type']
#        value_list = value_list['whitelist']
#    else:
#        whitelist_type = None
#    used_values = []
#    if whitelist_type == 'group':
#        if whitelist_keys is not None:
#            for i in range(len(used_values)):
#                for w_key in whitelist_keys:
#                    if used_values[i].endswith(f' ({w_key})'):
#                        used_values[i] = used_values[i].replace(f' ({w_key})', '')
#                        if headers is not None and w_key in headers:
#                            part_vals = used_values[i].split(' ')
#                           header = headers[w_key].split(' ')
#                            new_val = {}
#                            for j in range(len(header)):
#                                new_val[header[j]] = part_vals[j]
#                            used_values[i] = new_val
#                        break


def get_conditions(factors, node, mandatory_mode, result_dict):
    """

    :param factors:
    :param node:
    :param mandatory_mode:
    :param result_dict:
    :return:
    """

    # list to save all experimental factors that contain a dictionary
    is_dict = []

    # iterate through experimental_factors
    for i in range(len(factors)):

        # if the values of the experimental factor are in a dictionary or the
        # factor contains a list (so the factor can occur multiple times in a
        # condition) than call the function get_combinations to create all
        # possible combinations of this factor with its values
        if (isinstance(factors[i]['values'], dict) and
                'value' not in factors[i]['values']
                and 'unit' not in factors[i]['values']) \
                or ('is_list' in factors[i] and factors[i]['is_list']):

            # add the factor to is_dict if it contains a dictionary
            if isinstance(factors[i]['values'], dict):
                is_dict.append(factors[i]['factor'])

            # overwrite the values with the combinations
            factors[i]['values'] = get_combinations(factors[i]['values'],
                                                    factors[i]['factor'],
                                                    factors[i]['factor'])

            # remove ident_key from result dictionary
            if 'ident_key' in result_dict['experimental_factors'][i]['values']:
                result_dict['experimental_factors'][i]['values'].pop(
                    'ident_key')

        # if the values of the experimental factors are a list and a list
        # elements contain dictionary and are not of type value_unit than
        # combine all keys and their values to a single string value
        elif isinstance(factors[i]['values'], list) and (
                any(isinstance(elem, dict) and 'value' not in elem and 'unit'
                    not in elem for elem in factors[i]['values'])):

            # add the factor to is_dict
            is_dict.append(factors[i]['factor'])

            # iterate through the values
            for k in range(len(factors[i]['values'])):

                # test if the value is a dictionary
                if isinstance(factors[i]['values'][k], dict):

                    # create a new value by chaining the keys and their values
                    # in the following way:
                    # factor:{key1:value1|key2:value2|...}
                    val = factors[i]['values'][k]
                    new_val = f'{factors[i]["factor"]}:{"{"}'
                    for j in range(len(list(factors[i]['values'][k].keys()))):
                        new_val = f'{new_val}{"|" if j > 0 else ""}' \
                                  f'{list(val.keys())[j]}:' \
                                  f'\"{val[list(val.keys())[j]]}\"'
                    new_val = f'{new_val}{"}"}'

                    # overwrite the value
                    factors[i]['values'][k] = new_val

        # remove is_list key from result dictionary
        if 'is_list' in result_dict['experimental_factors'][i]:
            result_dict['experimental_factors'][i].pop('is_list')

    # parameter to declare if there are multiple conditions, default True
    multi_conditions = True

    # call get_condition_combinations to create all conditions
    combinations = get_condition_combinations(factors)

    # if there is only one experimental factor and the combinations match
    # the values for the factor than set multi_combinations to False and apply
    # the combinations as the used_combinations (= chosen by user)
    if len(factors) == 1 and combinations == factors[0]['values']:
        multi_conditions = False
        used_combinations = combinations

    # iterate through all factors
    for fac in factors:

        # test if the factor contains a dictionary
        if fac['factor'] in is_dict:

            # create a list to store the dictionaries that represent the value
            # of the experimental factors
            vals = []

            # iterate through the values of the factor, split them into
            # a list of tuples containing factor and values and save the values
            # in vals
            for cond in fac['values']:
                val = ([x[1] for x in split_cond(cond)])
                for y in val:
                    vals.append(y)

            # remove duplicates in vals
            vals = [dict(t) for t in {tuple(d.items()) for d in vals}]

            # TODO: if value_unit
            for elem in vals:
                for key in elem:
                    if key == 'treatment_duration':
                        unit = elem[key].lstrip('0123456789')
                        value = elem[key][:len(elem[key]) - len(unit)]
                        elem[key] = {'unit': unit, 'value': int(value)}

    # if there are multiple conditions, prompt the user to choose the ones he
    # analyzed and parse the user input
    if multi_conditions:
        print(
            f'\nPlease select the analyzed combinations of experimental '
            f'factors (1-{len(combinations)}) divided by comma:\n')
        print_option_list(combinations, False)
        used_combinations = parse_input_list(combinations, False)

    # call get_replicate_count to fill in information for every condition
    conditions = get_replicate_count(used_combinations, node, mandatory_mode,
                                     result_dict)

    # return the filled conditions
    return conditions


def get_replicate_count(conditions, node, mandatory_mode, result_dict):
    """

    :param conditions:
    :param node:
    :param mandatory_mode:
    :param result_dict:
    :return:
    """

    # create a list to save the information for every condition
    condition_infos = []

    # iterate through every condition
    for condition in conditions:

        # create a dictionary for the biological replicates and save the
        # condition name
        replicates = {'condition_name': condition}

        # print a caption for the condition, ask the user to enter the
        # number of biological replicated and parse the user input
        print(f'{"".center(size.columns, "_")}\n\n'
              f'{f"Condition: {condition}".center(size.columns, " ")}\n'
              f'{"".center(size.columns, "_")}\n\n'
              f'Please enter the number of biological replicates:')
        bio = parse_input_value('count', '', False, 'number',
                                result_dict)

        # test if there are biological replicates
        if bio > 0:

            # parse user input to declare if the samples are pooled
            input_pooled = parse_list_choose_one([True, False],
                                                 f'\nAre the samples pooled?')

            # print a caption for the biological replicate
            print(f'{"".center(size.columns, "_")}\n\n'
                  f'\033[1m{"Biological Replicates".center(size.columns, " ")}'
                  f'\033[0m\n')

            # call fill_replicates to enter information for the replicate and
            # save it in the replicates dictionary
            replicates['biological_replicates'] = fill_replicates(
                'biological_replicates', condition, bio, input_pooled,
                node, mandatory_mode, result_dict)

            # add the replicates dictionary to the list containing
            # condition information
            condition_infos.append(replicates)

    # return the condition information
    return condition_infos


def fill_replicates(type, condition, bio, input_pooled, node,
                    mandatory_mode, result_dict):
    """

    :param type:
    :param condition:
    :param bio:
    :param input_pooled:
    :param node:
    :param mandatory_mode:
    :param result_dict:
    :return:
    """

    # read in metadata structure
    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))

    # split the conditions into a list of tuples containing the factors and
    # values
    conditions = split_cond(condition)

    # set organism to its abbreviated version by reading in the abbrev
    # whitelist for organism and matching the input organism with the whitelist
    organism = utils.get_whitelist(os.path.join('abbrev', 'organism_name'),
                                   result_dict)['whitelist']
    print(result_dict['organism'])
    organism = organism[result_dict['organism']['organism_name']]

    # create a dictionary for the biological replicates and fill it with the
    # number of biological replicates and an empty list to append the samples
    # to
    replicates = {'count': bio, 'samples': []}

    # iterate through the biological replicates
    for i in range(1, bio+1):

        # create a dictionary to save all information about the sample
        samples = {}

        # build the sample name out of the condition and the index of the
        # biological replicate
        sample_name = f'{condition}_b{"{:02d}".format(i)}'

        # call get_short_name to create an abbreviated sample name
        short_name = f'{get_short_name(condition, result_dict)}' \
                     f'_b{"{:02d}".format(i)}'

        # save the abbreviated sample name in the sampled dictionary
        samples['sample_name'] = short_name

        # print a caption for the sample
        print(f'{f"Sample: {sample_name}".center(size.columns, "-")}\n')

        # save if the sample is pooled in the sample dictionary
        samples['pooled'] = input_pooled

        # prompt the user to enter a donor count if the sample is pooled or
        # set the donor_count to 1 otherwise and save it into the sample
        # dictionary
        samples['donor_count'] = parse_input_value(
            'donor_count', '', False, 'int', result_dict) if input_pooled \
            else 1

        # iterate through factors and values in the condition
        for cond in conditions:

            # find structure of the factor in metadata structure and save it
            part_node = list(utils.find_keys(key_yaml, cond[0]))[0]

            # test if the value is of type value_unit
            if isinstance(part_node['value'], dict) and 'value' in \
                    part_node['value'] and 'unit' in part_node['value']:

                # split the value of the factor into value and unit, save them
                # in a dictionary and overwrite the value of the factor with
                # the dictionary
                unit = cond[1].lstrip('0123456789')
                value = cond[1][:len(cond[1]) - len(unit)]
                samples[cond[0]] = {'unit': unit, 'value': int(value)}

            else:

                # set the input input type for the factor
                if 'input_type' in part_node:
                    input_type = part_node['input_type']
                else:
                    input_type = None

                # test if the factor takes a list as value
                if part_node['list']:

                    # test if the value is a dictionary and if a key of the
                    # dictionary takes a value_unit as input
                    if isinstance(cond[1], dict):
                        for key in cond[1]:
                            #TODO: value unit
                            if key == 'treatment_duration':

                                # split the input value into unit an value,
                                # save them into a dictionary and overwrite the
                                # input value with the dictionary
                                unit = cond[1][key].lstrip('0123456789')
                                value = cond[1][key][
                                        :len(cond[1][key]) - len(unit)]
                                cond[1][key] = {'unit': unit,
                                                'value': int(value)}

                    if cond[0] not in samples:

                        # if the factor is not yet in the sample, save the
                        # factor value as a list
                        samples[cond[0]] = [
                            int(cond[1]) if input_type == 'int' else cond[1]]
                    else:

                        # if the factor is already in the sample, append the
                        # factor value to the value list
                        samples[cond[0]].append(
                            int(cond[1]) if input_type == 'int' else cond[1])

                else:

                    # if the factor does not contain a list as value, save the
                    # value to the sample
                    samples[cond[0]] = int(cond[1]) if input_type == 'int' \
                        else cond[1]

        # merge the samples containing the factors with a dictionary returned
        # by the fill_metadata_structure function called on the sample
        # structure
        samples = merge_dicts(
            samples, fill_metadata_structure(
                node[type]['value']['samples']['value'], 'samples', samples,
                False, mandatory_mode, result_dict, False, False))

        # set number of measurements to 1 if it is not yet specified
        if 'number_of_measurements' not in samples:
            samples['number_of_measurements'] = 1

        # call the get_technical_replicates function to create the technical
        # replicates and save them to the sample
        samples['technical_replicates'] = get_technical_replicates(
            short_name, organism, samples['number_of_measurements'])

        # add the filled sample to the replicate
        replicates['samples'].append(samples)

    # return the replicates for one condition
    return replicates


def get_technical_replicates(sample_name, organism, nom):
    """

    :param sample_name:
    :param organism:
    :param nom:
    :return:
    """

    # prompt user to input number of technical replicates and parse user input
    print(f'\nPlease enter the number of technical replicates:')
    count = parse_input_value('count', '', False, 'number', [])

    # print error message and redo input if number <1 was stated
    while count < 1:
        print(f'The number of technical replicates has to be at least 1.')
        count = parse_input_value('count', '', False, 'number', [])

    # create a list to save the sample names
    samples = []

    # iterate over the number of technical replicates
    for i in range(count):

        # iterate over the number of measurements
        for j in range(nom):

            # add sample name containing id, organism, sample identifier,
            # index of technical replicate and index of measurement to samples
            # list
            samples.append(f'{id}_{organism}_{sample_name}_'
                           f't{"{:02d}".format(i + 1)}_'
                           f'm{"{:02d}".format(j + 1)}')

    # return a dictionary containing the number of technical replicates and the
    # sample names
    return {'count': count, 'sample_name': samples}


def get_condition_combinations(factors):
    """
    This function returns all possible combinations for experimental factors
    :param factors: multiple dictionaries containing the factors and their
                    respective values
    :return: a list containing all combinations of conditions
    """

    # create a list to store all conditions
    combinations = []

    # iterate over the factor dictionaries
    for i in range(len(factors)):

        # iterate over the values in a dictionary
        for value in factors[i]['values']:

            # if the value is of type value_unit, chain the value and its unit
            # in a string
            if isinstance(value, dict) and 'value' in value \
                    and 'unit' in value:
                value = f'{value["value"]}{value["unit"]}'

            # if the value starts with '<factor>:' then add it to the
            # combinations list, otherwise put the '<factor>:' in front of the
            # value and add it to the combinations list
            if type(value) == str and \
                    value.split(':')[0] == factors[i]['factor']:
                combinations.append(f'{value}')
            else:
                combinations.append(f'{factors[i]["factor"]}:"{value}"')

            # iterate over the factor dictionarie starting at i+1
            for j in range(i + 1, len(factors)):

                # call this function on the sublist of factors from i+1
                comb = get_condition_combinations(factors[j:])

                # iterate over the combinations created from the sublist of
                # factors
                for c in comb:

                    # if the value starts with '<factor>:' than chain it to the
                    # created combination otherwise do the same but add
                    # '<factor>:' in front of the value
                    # add the chained combination to the combinations list
                    if type(value) == str and \
                            value.split(':')[0] == factors[i]['factor']:
                        combinations.append(f'{value}-{c}')
                    else:
                        combinations.append(
                            f'{factors[i]["factor"]}:"{value}"-{c}')

    # return a list of all combinations
    return combinations


# ---------------------------------SUMMARY--------------------------------------


def print_summary(result, depth, is_list):
    """

    :param result:
    :param depth:
    :param is_list:
    :return:
    """
    summary = ''
    if isinstance(result, dict):
        for key in result:
            if key == list(result.keys())[0] and is_list:
                summary = f'{summary}\n{"    " * (depth - 1)}{"  - "}{key}: ' \
                          f'{print_summary(result[key], depth + 1, is_list)}'
            else:
                summary = f'{summary}\n{"    " * depth}{key}: ' \
                          f'{print_summary(result[key], depth + 1, is_list)}'
    elif isinstance(result, list):
        for elem in result:
            if not isinstance(elem, list) and not isinstance(elem, dict):
                summary = f'{summary}\n{"    " * (depth - 1)}{"  - "}{elem}'
            else:
                summary = f'{summary}{print_summary(elem, depth, True)}'
    else:
        summary = f'{summary}{result}'
    return summary


def print_sample_names(result, input_id, path):
    samples = list(
        utils.find_list_key(result, 'technical_replicates:sample_name'))
    print(f'{"".center(size.columns, "-")}\n'
          f'{"SAMPLE NAMES".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    sample_names = ''
    for elem in samples:
        for name in elem:
            sample_names += f'- {name}\n'
    print(sample_names)
    save = parse_list_choose_one(
        [True, False], 'Do you want to save the sample names into a file?')
    if save:
        text_file = open(os.path.join(path, f'{input_id}_samples.txt'), 'w')
        text_file.write(sample_names)
        text_file.close()
        print(
            f'The sample names have been saved to file \'{path}/{input_id}'
            f'_samples.txt\'.')


# ---------------------------------UTILITIES------------------------------------


def enter_information(node, key, return_dict, optional, mandatory_mode,
                      result_dict, first_node, is_factor):
    """

    :param node:
    :param key:
    :param return_dict:
    :param optional:
    :param mandatory_mode:
    :param result_dict:
    :param first_node:
    :param is_factor:
    :return:
    """
    # test if the key contains a dictionary
    if isinstance(node['value'], dict) and \
            not set(['mandatory', 'list', 'desc', 'display_name', 'value']) <= \
            set(node['value'].keys()):
        display_name = node['display_name']
        if first_node:

            # if the key is on top level, print a bigger caption
            print(f'{"".center(size.columns, "_")}\n\n'
                  f'{f"{display_name}".center(size.columns, " ")}\n'
                  f'{"".center(size.columns, "_")}\n')
        else:

            # if the key is on a lower level, print a smaller caption
            print(f'\n'
                  f'{"".center(size.columns, "-")}\n'
                  f'{f"{display_name}".center(size.columns, " ")}\n'
                  f'{"".center(size.columns, "-")}\n')

        # print a description if one is stated in the metadata structure
        if node['desc'] != '':
            print(f'{node["desc"]}\n')

        # call fill_metadata_structure to fill in the dictionary
        return fill_metadata_structure(node['value'], key, return_dict, optional,
                                       mandatory_mode, result_dict, False,
                                       is_factor)

    else:
        # call parse_input_value to fill in a single value
        return parse_input_value(key, node['desc'], node['whitelist'],
                                 node['input_type'], result_dict)


def parse_list_choose_one(whitelist, header):
    """
    This function prints an indexed whitelist and prompts the user to choose a
    value by specifying the index.
    :param whitelist: a list of values for the user to choose from
    :param header: a headline or description that should be printed
    :return: value: the whitelist value chosen by the user
    """

    # print the given header and indexed whitelist and parse the user input
    try:
        print(f'{header}')
        print_option_list(whitelist, False)
        value = whitelist[int(input()) - 1]

    # redo the input prompt if the user input is not an integer
    except (IndexError, ValueError) as e:
        print(f'Invalid entry. Please enter a number between 1 and '
              f'{len(whitelist)}')
        value = parse_list_choose_one(whitelist, header)

    # return the user input
    return value


def parse_input_value(key, desc, has_whitelist, value_type, result_dict):
    """

    :param key:
    :param desc:
    :param has_whitelist:
    :param value_type:
    :param result_dict:
    :return:
    """

    # read in whitelist if the key has one or set the whitelist to None
    if has_whitelist:
        whitelist = utils.get_whitelist(key, result_dict)
    else:
        whitelist = None

    # test if the whitelist is not None
    if whitelist is not None:

        # test if the whitelist is a dictionary
        if isinstance(whitelist['whitelist'], dict):

            # create a list containing the values of every key in the whitelist
            w = [x for xs in list(whitelist['whitelist'].values()) if xs is
                 not None for x in xs]

            # use autocomplete if the whitelist contains more than 30 values
            if len(w) > 30:
                input_value = complete_input(w, key)

                # repeat if the input value does not match the whitelist
                if input_value not in w:
                    print(f'The value you entered does not match the '
                          f'whitelist. Try tab for autocomplete.')
                    input_value = parse_input_value(
                        key, desc, has_whitelist, value_type, result_dict)

            else:

                # parse grouped whitelist if the whitelist contains less than
                # 30 values
                input_value = parse_group_choose_one(whitelist['whitelist'],
                                                     w, f'{key}:')

        # use autocomplete if the whitelist is a list longer than 30
        elif len(whitelist['whitelist']) > 30:
            input_value = complete_input(whitelist['whitelist'], key)

            # repeat if the input value does not match the whitelist
            if input_value not in whitelist['whitelist']:
                print(f'The value you entered does not match the '
                      f'whitelist. Try tab for autocomplete.')
                input_value = parse_input_value(key, desc, has_whitelist,
                                                value_type,
                                                result_dict)

        # call parse_list_choose_one to print indexed whitelist and parse user
        # input
        else:
            input_value = parse_list_choose_one(whitelist['whitelist'],
                                                f'{key}:')

        # test if the whitelist contains the key 'headers'
        if 'headers' in whitelist:

            # split the headers and the input value at ' ' and save each to
            # a list
            headers = whitelist['headers'].split(' ')
            vals = input_value.split(' ')

            # create a dictionary to store the new value
            value = {}

            # iterate through the headers and save the header and value of the
            # same index into a dictionary with header as key
            for i in range(len(headers)):
                value[headers[i]] = vals[i]

            # overwrite the input value with the dictionary
            input_value = value

    # if there is no whitelist
    else:

        # print a description if one is stated in the metadata structure
        if desc != '':
            print(f'\n{desc}')

        # prompt the user to choose between True and False if the input value
        # is of type boolean
        if value_type == 'bool':
            input_value = parse_list_choose_one([True, False],
                                                f'Is the sample {key}')

        else:

            # print the key, add a newline if a description was printed
            if desc == '':
                input_value = input(f'\n{key}: ')
            else:
                input_value = input(f'{key}: ')

            # repeat input if nothing is passed
            if input_value == '':
                print(f'Please enter something.')
                input_value = parse_input_value(key, desc, whitelist,
                                                value_type, result_dict)

            # test if input fits the input_type int and repeat the input if not
            if value_type == 'number':
                try:
                    input_value = int(input_value)
                except ValueError:
                    print(f'Input must be of type int. Try again.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type,
                                                    result_dict)

            # if the input_type is date, test if the date fits the format
            # dd.mm.yyyy and repeat the input if not
            elif value_type == 'date':
                try:
                    input_date = input_value.split('.')
                    if len(input_date) != 3 or len(
                            input_date[0]) != 2 or len(
                            input_date[1]) != 2 or len(input_date[2]) != 4:
                        raise SyntaxError
                    input_value = datetime.date(int(input_date[2]),
                                                int(input_date[1]),
                                                int(input_date[0]))
                    input_value = input_value.strftime("%d.%m.%Y")
                except (IndexError, ValueError, SyntaxError) as e:
                    print(f'Input must be of type \'DD.MM.YYYY\'.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type,
                                                    result_dict)

            else:

                # repeat input if it is of type string and contains an
                # invalid character
                if '\"' in input_value:
                    print(f'Ivalid symbol \'\"\'. Please try again.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type, result_dict)
                elif '{' in input_value:
                    print(f'Ivalid symbol \'{"{"}\'. Please try again.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type, result_dict)
                elif '}' in input_value:
                    print(f'Ivalid symbol \'{"}"}\'. Please try again.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type, result_dict)
                elif '|' in input_value:
                    print(f'Ivalid symbol \'|\'. Please try again.')
                    input_value = parse_input_value(key, desc, whitelist,
                                                    value_type, result_dict)

    # return the user input
    return input_value


def parse_group_choose_one(whitelist, w, header):
    """

    :param whitelist:
    :param w:
    :param header:
    :return:
    """

    try:

        # print a header or description
        print(f'{header}\n')

        # set index to 1
        i = 1

        # iterate through keys in whitelist
        for key in whitelist:

            # print the indexed whitelist values with the keys as captions
            if whitelist[key] is not None:
                print(f'\033[1m{key}\033[0m')
                for value in whitelist[key]:
                    print(f'{i}: {value}')
                    i += 1

        # select the ehitelist value that fits the input index
        value = w[int(input()) - 1]

    # redo the input if the passed value is not an integer >1
    except (IndexError, ValueError) as e:
        print(f'Invalid entry. Please enter a number between 1 and '
              f'{len(whitelist)}')
        value = parse_list_choose_one(whitelist, header)

    # return the user input
    return value


def get_short_name(condition, result_dict):
    conds = split_cond(condition)
    whitelist = utils.get_whitelist(os.path.join('abbrev', 'factor'),
                                    result_dict)['whitelist']
    if whitelist and 'whitelist_type' in whitelist and whitelist[
            'whitelist_type'] == 'plain':
        whitelist = whitelist['whitelist']
    short_cond = []
    for c in conds:
        if whitelist and c[0] in whitelist:
            k = whitelist[c[0]]
        else:
            k = c[0]
        if isinstance(c[1], dict):
            cond_whitelist = utils.get_whitelist(os.path.join('abbrev', c[0]),
                                                 result_dict)
            new_vals = {}
            for v in c[1]:
                if cond_whitelist and v in cond_whitelist['whitelist']:
                    val_whitelist = utils.get_whitelist(
                        os.path.join('abbrev', v), result_dict)
                    if val_whitelist and c[1][v].lower() in val_whitelist['whitelist']:
                        new_vals[cond_whitelist["whitelist"][v]] = val_whitelist["whitelist"][
                            c[1][v].lower()]
                    elif val_whitelist and c[1][v] in val_whitelist['whitelist']:
                        new_vals[cond_whitelist["whitelist"][v]] = val_whitelist["whitelist"][
                            c[1][v]]
                    else:
                        new_vals[cond_whitelist["whitelist"][v]] = c[1][v]
            val = '+'.join([f'{x}.{new_vals[x].replace(" ", "")}' for x in
                            list(new_vals.keys())])
            short_cond.append(f'{k}#{val}')
        else:
            val_whitelist = utils.get_whitelist(os.path.join('abbrev', c[0]),
                                                result_dict)
            if val_whitelist and c[1].lower() in val_whitelist['whitelist']:
                short_cond.append(f'{k}.{val_whitelist["whitelist"][c[1].lower()]}')
            elif val_whitelist and c[1] in val_whitelist['whitelist']:
                short_cond.append(f'{k}.{val_whitelist["whitelist"][c[1]]}')
            else:
                short_cond.append(f'{k}.{c[1]}')
    short_condition = '-'.join(short_cond)
    return short_condition


def split_cond(condition):
    conditions = []
    sub_cond = {}
    sub = False
    key = ''
    sub_key = ''
    value = ''
    count = 0
    start = 0
    for i in range(len(condition)):
        if condition[i] == '{':
            sub = True
            key = condition[start:i].rstrip(':')
            start = i + 1
        elif condition[i] == '|':
            sub_cond[sub_key] = value
            start = i + 1
        elif condition[i] == '}':
            sub_cond[sub_key] = value
            conditions.append((key, sub_cond))
            sub_cond = {}
        elif condition[i] == '\"':
            count += 1
            if count % 2 == 0:
                value = condition[start:i]
            else:
                if sub:
                    sub_key = condition[start:i].rstrip(':')
                else:
                    key = condition[start:i].rstrip(':')
                start = i + 1
        elif condition[i] == '-' and count % 2 == 0:
            if sub:
                sub = False
            else:
                conditions.append((key, value))
            start = i + 1
    if not sub:
        conditions.append((key, value))
    return conditions


def merge_dicts(a, b):
    if isinstance(a, list):
        res = []
        for i in range(len(a)):
            res.append(merge_dicts(a[i], b[i]))
    elif isinstance(a, dict):
        b_keys = list(b.keys())
        res = {}
        for key in a.keys():
            if key in b_keys:
                res[key] = merge_dicts(a[key], b[key])
                b_keys.remove(key)
            else:
                res[key] = a[key]
        for key in b_keys:
            res[key] = b[key]
    else:
        res = a
    return res


def get_combinations(values, key, key_name):
    is_dict = False
    if 'ident_key' in values:
        is_dict = True
        if values['ident_key'] in values and len(
                values[values['ident_key']]) > 1:
            multi = parse_list_choose_one(
                [True, False],
                f'\nCan one sample contain multiple {key_name}s?')
        else:
            multi = False
            values.pop('ident_key')
    else:
        multi = parse_list_choose_one(
            [True, False], f'\nCan one sample contain multiple {key_name}s?')

    if multi or is_dict:
        merge_values = get_combis(values, key, multi)
        print(
            f'\nPlease select the analyzed combinations for {key} '
            f'(1-{len(merge_values)}) divided by comma:\n')
        print_option_list(merge_values, False)
        used_values = parse_input_list(merge_values, False)
    else:
        used_values = values
    return used_values


def get_combis(values, key, multi):
    if 'multi' in values:
        values.pop('multi')
    if 'ident_key' in values and (
            values['ident_key'] not in values or values['ident_key'] is None):
        values.pop('ident_key')
    if isinstance(values, list):
        if multi:
            possible_values = []
            for i in range(len(values)):
                s = f'{key}:"{values[i]}"'
                possible_values.append(s)
                for j in range(i + 1, len(values)):
                    s = f'{s}-{key}:"{values[j]}"'
                    possible_values.append(s)
            return possible_values
        else:
            return values
    else:
        if multi:
            possible_values = {}
            disease_values = []
            ident_key = values['ident_key']
            depend = values[ident_key]
            values.pop(ident_key)
            values.pop('ident_key')
            for elem in depend:
                possible_values[elem] = []
                value = [f'{ident_key}:"{elem}"']
                for i in range(len(values.keys())):
                    value2 = []
                    for x in value:
                        val = x
                        for v in values[list(values.keys())[i]]:
                            if isinstance(
                                    v, dict) and 'value' in v and 'unit' in v:
                                v = f'{v["value"]}{v["unit"]}'
                            value2.append(
                                f'{val}|{list(values.keys())[i]}:"{v}"')
                    value = value2
                possible_values[elem] = value
                for z in possible_values:
                    if z != elem:
                        for x in possible_values[elem]:
                            for y in possible_values[z]:
                                disease_values.append(
                                    f'{key}:{"{"}{x}{"}"}-{key}:{"{"}{y}{"}"}')

        else:
            disease_values = []
            possible_values = []
            if 'ident_key' in values and values['ident_key'] in values:
                start = values['ident_key']
                values.pop('ident_key')
            else:
                start = list(values.keys())[0]
            for elem in values[start]:
                v = [f'{start}:\"{elem}\"']
                for k in values:
                    if k != start:
                        v2 = []
                        for i in v:
                            for x in values[k]:
                                if isinstance(x, dict) and 'value' in x \
                                        and 'unit' in x:
                                    v2.append(
                                        f'{i}|{k}:\"{x["value"]}{x["unit"]}\"')
                                else:
                                    v2.append(f'{i}|{k}:\"{x}\"')
                        v = v2
                possible_values = v
                for z in possible_values:
                    disease_values.append(f'{key}:{"{"}{z}{"}"}')
        return disease_values


def get_input_list(node, item, filled_object):
    if 'whitelist' in node and node['whitelist'] or 'special_case' in node and 'merge' in node['special_case']:
        whitelist = utils.get_whitelist(item, filled_object)
        if whitelist:
            if len(whitelist['whitelist']) > 30:
                used_values = []
                redo = True
                print(f'\nPlease enter the values for experimental factor '
                      f'{item}.')
                while redo:
                    input_value = complete_input(whitelist['whitelist'],
                                                 item)
                    if input_value in whitelist['whitelist']:
                        used_values.append(input_value)
                        redo = parse_list_choose_one(
                            [True, False],
                            f'\nDo you want to add another {item}?')
                    else:
                        print(f'The value you entered does not match the '
                              f'whitelist. Try tab for autocomplete.')
            else:
                print('\nPlease enter the list')
                if whitelist['whitelist_type'] == 'plain':
                    print_option_list(whitelist['whitelist'], '')
                    used_values = parse_input_list(whitelist['whitelist'],
                                                   False)
                elif whitelist['whitelist_type'] == 'group':
                    w = [x for xs in list(whitelist['whitelist'].values()) for
                         x in xs]
                    i = 1
                    for w_key in whitelist['whitelist']:
                        print(f'\033[1m{w_key}\033[0m')
                        for value in whitelist['whitelist'][w_key]:
                            print(f'{i}: {value}')
                            i += 1
                    used_values = parse_input_list(w, False)
            if 'headers' in whitelist:
                headers = whitelist['headers'].split(' ')
                for i in range(len(used_values)):
                    vals = used_values[i].split(' ')
                    used_values[i] = {}
                    for j in range(len(headers)):
                        used_values[i][headers[j]] = vals[j]
        else:
            print('No whitelist')
            used_values = [0]
    else:
        value_type = node['input_type']
        print(f'\nPlease enter a list of {value_type} values for experimental'
              f' factor {item} divided by comma:\n')
        used_values = parse_input_list(value_type, False)
    return used_values


def print_option_list(options, desc):
    if desc:
        data = [[f'{i + 1}:', f'{options[i]}', desc[i]] for i in
                range(len(options))]
        print(tabulate(data, tablefmt='plain',
                       maxcolwidths=[size.columns * 1 / 8,
                                     size.columns * 3 / 8,
                                     size.columns * 4 / 8]))
    else:
        data = [[f'{i + 1}:', f'{options[i]}'] for i in range(len(options))]
        print(tabulate(data, tablefmt='plain',
                       maxcolwidths=[size.columns * 1 / 8,
                                     size.columns * 7 / 8]))


def parse_input_list(options, terminable):
    input_list = input()
    if terminable and input_list.lower() == 'n':
        return None
    else:
        if isinstance(options, list):
            try:
                input_list = [options[int(i.strip()) - 1] for i in
                              input_list.split(',')]
            except (IndexError, ValueError) as e:
                print(f'Invalid entry, try again:')
                input_list = parse_input_list(options, terminable)
        else:
            try:
                input_list = [x.strip() for x in input_list.split(',')]
                if options == 'number':
                    for i in range(len(input_list)):
                        input_list[i] = int(input_list[i])
            except (ValueError, IndexError) as e:
                print(f'Invalid entry. Please enter {options} numbers divided '
                      f'by comma.')
                input_list = parse_input_list(options, terminable)
    return input_list


def complete_input(whitelist, key):
    """

    :param whitelist:
    :param key:
    :return:
    """
    print(f'\nPress tab once for autofill if'
          f' possible or to get a list of up to'
          f' 30 possible input values.')
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set show-all-if-ambiguous On")
    readline.parse_and_bind("set show-all-if-unmodified On")
    completer = WhitelistCompleter(whitelist)
    readline.set_completer(completer.complete)
    readline.set_completer_delims('')
    input_value = input(f'{key}: ')
    readline.parse_and_bind('tab: self-insert')
    return input_value


def get_value_unit(result_dict):
    val_un = {'unit': parse_input_value('unit', '', True, str, result_dict),
              'value': parse_input_value('value', '', False, int, result_dict)}
    return val_un


def get_list_value_unit(result_dict, factor):
    print(f'\nPlease enter the unit for factor {factor}:')
    unit = parse_input_value('unit', '', True, 'select', result_dict)
    val_un = []
    print(f'\nPlease enter int values for factor {factor} (in {unit}) '
          f'divided by comma:')
    value = parse_input_list('number', False)
    for val in value:
        val_un.append({'unit': unit, 'value': val})
    return val_un