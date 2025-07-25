from fred.src import generate_metafile
import fred.src.utils as utils
import copy
import os


def edit_file(path, mode, mandatory_only, size=80):

    if mode == 'metadata':
        key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'keys.yaml'))
    else:
        key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'mamplan_keys.yaml'))

    file = utils.read_in_yaml(path)

    options = [key for key in key_yaml]

    print(f'Choose the parts you want to edit (1,...,{len(options)}) divided '
          f'by comma.\n')

    generate_metafile.print_option_list(options, False)
    edit_keys = generate_metafile.parse_input_list(options, True)

    for key in edit_keys:

        if key in file:
            file[key] = edit_item(key, file[key], key_yaml[key], key_yaml,
                                  file, mandatory_only, mode)

        else:

            file[key] = generate_metafile.get_redo_value(
                key_yaml[key], key, True, mandatory_only, file, True, False,
                True, mode, key_yaml)

        while True:

            print(generate_metafile.get_summary(file[key], size=size))

            correct = generate_metafile.parse_list_choose_one(
                ['True ', 'False '], f'\nIs the input correct? You can redo '
                                     f'it by selecting \'False\'')

            if correct:
                break

            else:
                file[key] = edit_item(key, file[key], key_yaml[key], key_yaml,
                                      file, mandatory_only, mode, size=size)

    utils.save_as_yaml(file, path)
    print(f'Changes were saved to {path}')


# TODO: split into multiple functions
def edit_item(key_name, item, key_yaml, full_yaml, result_dict, mandatory_mode,
              mode, size=80, not_editable=None):
    """
    This function is used to edit a dictionary. Therefor it requests
    information from the user via a dialog
    :param key_name: The name of the key whose values should be edited
    :param item: the value to be edited
    :param key_yaml: a part of the underlying structure containing the key
                     whose values should be edited
    :param full_yaml: the complete general structure
    :param result_dict: the filled dictionary
    :param mandatory_mode: a bool that states if the mandatory mode is active
    :param mode: the mode the program runs in ('metadata' or 'mamplan')
    :param size: the window size (default 80)
    :param not_editable: a list of keys that is not editable
    :return: item: the edited value
    """

    # TODO: handle special cases

    if not_editable is None:
        not_editable = []

    # test if item to edit is a list
    if isinstance(item, list):

        # test that the list elements are not of type dict or if they are that
        # they are treated as 'merge' special case
        if not isinstance(key_yaml['value'], dict):

            # call 'get_redo_value' function to repeat the input
            item = generate_metafile.get_redo_value(
                key_yaml, key_name, not key_yaml['mandatory'], mandatory_mode,
                result_dict, True, False, True, mode, key_yaml)

        # list elements contain dictionary
        else:

            # initialize a list to hold list elements as options for the user
            # to choose to edit and set the first element to an option to
            # remove list elements
            all_options = ['remove element from list']

            # iterate over the list
            for i in range(len(item)):

                # TODO: enhance display of dictionary

                # if the item is a dictionary, convert it to a string
                # add the item to the option list
                if isinstance(item[i], dict):
                    str_dict = '\n'.join(f'{x}: {item[i][x]}' for x in item[i])
                    all_options.append(f'edit: {str_dict}')
                else:
                    all_options.append(f'edit: {item[i]}')

            # add the option to add a new element to the list
            all_options.append('add element to list')

            # request user input
            print(f'Please choose the how you want to edit the list choosing '
                  f'from the following options (1-{len(item)}) divided by '
                  f'comma.')

            # print the list elements as options and parse the user input
            generate_metafile.print_option_list(all_options, False)
            chosen_options = generate_metafile.parse_input_list(all_options,
                                                                False)

            # remove the options that do not represent a distinct list element
            all_options.remove('remove element from list')
            all_options.remove('add element to list')

            # initialize a list to store list elements that should be removed
            remove_options = []

            # test if user chose to remove elements
            if 'remove element from list' in chosen_options:

                # request user to state elements to delete
                print(f'Please choose the list elements you want to remove'
                      f' (1-{len(item)}) divided by comma.')

                # print a list of removable elements and parse user input
                generate_metafile.print_option_list(all_options, False)
                remove_options = generate_metafile.parse_input_list(
                    all_options, False)

            # initialize a dictionary to save editing information for all list
            # elements
            edit_options = {}

            # iterate over all list elements
            for i in range(len(all_options)):

                # define an action for the element depending on the users input
                # possible values are:
                # 'remove': if the element should be removed from the list
                # 'edit': if the element should be edited
                # None: if the element should stay as it is
                if all_options[i] in remove_options:
                    action = 'remove'
                elif all_options[i] in chosen_options:
                    action = 'edit'
                else:
                    action = None

                # add the list element and its according action to the dict
                edit_options[all_options[i]] = {'element': item[i],
                                                'action': action}

            # initialize a new list to save all elements to which do not get
            # removed (edited as well as not edited)
            new_list = []

            # iterate over all list elements
            for key in edit_options:

                # test if the element should be edited
                if edit_options[key]['action'] == 'edit':

                    # TODO: enhance line breaks (if display name > size)

                    # print header for current element
                    display_name = key.replace('\n', ' | ')
                    print(f'\n'
                          f'{"".center(size, "-")}\n'
                          f'{f"{display_name}".center(size, " ")}\n'
                          f'{"".center(size, "-")}\n')

                    # call this function to overwrite the list element with its
                    # edited version
                    edit_options[key]['element'] = edit_item(
                        key_name, edit_options[key]['element'], key_yaml,
                        full_yaml, result_dict, mandatory_mode, mode)

                # test if the list element should NOT be removed
                if edit_options[key]['action'] != 'remove':

                    # save the list element to the new list
                    new_list.append(edit_options[key]['element'])

            # overwrite the list with the edited list
            item = new_list

            # test if the user chose to add new list elements
            if 'add element to list' in chosen_options:

                # set the display_name and print it as header for the new
                # element
                display_name = key_yaml['display_name']
                print(f'\n'
                      f'{"".center(size, "-")}\n'
                      f'{f"New {display_name}".center(size, " ")}\n'
                      f'{"".center(size, "-")}\n')

                # get input for new element
                item += generate_metafile.get_redo_value(
                    key_yaml, key_name, not key_yaml['mandatory'],
                    mandatory_mode, result_dict, True, False, True, mode, key_yaml)

    # item to edit is a dictionary
    elif isinstance(item, dict):

        # request input from the user
        print(f'Please choose the keys (1-{len(item.keys())}) you want to edit'
              f' divided by comma.')

        # TODO: remove not_editable

        # create a list of options from the dictionary keys (only add them if
        # they are supposed to be edited)
        edit_index = [key for key in key_yaml['value'] if key not in
                      not_editable]

        # add option 'all' to redo the complete dictionary
        edit_index.insert(0, 'all')

        # print options for the user and parse the given input
        generate_metafile.print_option_list(edit_index, False)
        edit_index = generate_metafile.parse_input_list(edit_index, False)

        # test if 'all' was selected
        if 'all' in edit_index:

            # redo input for the whole dictionary
            new_item = generate_metafile.get_redo_value(
                key_yaml, key_name, not key_yaml['mandatory'], mandatory_mode,
                result_dict, True, False, False, mode, key_yaml)

            # input value is a list
            if isinstance(new_item, list):

                # overwrite the old value with the new one
                item = new_item

            # input value is a dictionary
            else:

                # combine and update the old value with the new one
                item = {**result_dict[key_name],
                        **new_item}

        # keys were selected but not 'all'
        else:

            # iterate over keys
            for key in edit_index:

                # the key 'organism' was selected (part experimental_setting)
                if key == 'organism':

                    # redo the whole dictionary because the latter parts depend
                    # on the organism
                    item = generate_metafile.get_redo_value(
                        key_yaml, 'experimental_setting',
                        not key_yaml['mandatory'], mandatory_mode, result_dict,
                        True, False, False, mode, key_yaml)[0]

                # the key 'experimental_factors was selected and not the key
                # 'organism' (part experimental_setting)
                elif key == 'experimental_factors' and 'organism' not in \
                        edit_index:

                    # copy the underlying structure (new_yaml) and remove the
                    # key 'organism'
                    new_yaml = copy.deepcopy(key_yaml)
                    new_yaml['value'].pop('organism')

                    # redo all except 'organism' since all keys below the key
                    # 'experimental_factors' depend on its values
                    item = generate_metafile.get_redo_value(
                        new_yaml, 'experimental_setting',
                        not key_yaml['mandatory'], mandatory_mode,
                        copy.deepcopy(item), True, False, False, mode, key_yaml)[0]

                # the key 'conditions was selected and not the keys 'organism'
                # or 'experimental_factors'
                elif key == 'conditions' and 'experimental_factors' not in \
                        edit_index and 'organism' not in edit_index:

                    # The following loop is needed so get the experimental
                    # factors into the structure they were directly after input
                    # before parsing into the yaml structure. This is needed
                    # for the conditions (combinations of all selected factors
                    # and values) to be created again.

                    # iterate over the experimental factors
                    for i in range(len(item['experimental_factors'])):

                        # extract the properties of the experimental factor
                        # from the underlying structure
                        fac_yaml = list(utils.find_keys(
                            full_yaml,
                            item['experimental_factors'][i]['factor']))

                        # test if the factor was found in the general structure
                        if len(fac_yaml) > 0:

                            # define if the factor takes a list as element
                            item['experimental_factors'][i]['is_list'] = \
                                fac_yaml[0]['list']

                            # set the ident_key from the general structure
                            # if special_case group was defined
                            if 'special_case' in fac_yaml[0] and 'group' in \
                                    fac_yaml[0]['special_case']:
                                item['experimental_factors'][i]['values'][
                                    'ident_key'] = fac_yaml[0]['special_case'][
                                    'group']

                    # copy the underlying structure (new_yaml) and remove the
                    # keys 'organism' and 'experimental_factors'
                    new_yaml = copy.deepcopy(key_yaml)
                    new_yaml['value'].pop('organism')
                    new_yaml['value'].pop('experimental_factors')

                    # redo the conditions
                    item = generate_metafile.get_redo_value(
                        new_yaml, 'experimental_setting',
                        not key_yaml['mandatory'], mandatory_mode,
                        copy.deepcopy(item), True, False, False, mode, key_yaml)[0]

                # no special case -> used for all the other keys
                else:

                    # key was already filled out
                    if key in item:

                        # call this function to edit the value of the key
                        item[key] = edit_item(
                            key, item[key], key_yaml['value'][key], full_yaml,
                            result_dict, mandatory_mode, mode)

                    # key was not filled out yet
                    else:

                        # call function to input information
                        item[key] = generate_metafile.get_redo_value(
                            key_yaml['value'][key], key, True, mandatory_mode,
                            result_dict, True, False, True, mode, key_yaml)

    # item is a single value
    else:

        # call function to input value
        item = generate_metafile.parse_input_value(
            key_name, key_yaml['desc'], key_yaml['whitelist'],
            key_yaml['input_type'], item)

    return item
