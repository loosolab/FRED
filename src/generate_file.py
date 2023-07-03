import src.generate_metafile as generate_functions
import src.edit_file as edit_file
import src.utils as utils
import os
import sys

# TODO: remove not editable

not_editable = ['id', 'sample_name', 'pooled', 'donor_count',
                'technical_replicates']


def generate_file(path, input_id, mandatory_mode, mode, size=80):
    """
    This function is used to generate metadata by calling functions to compute
    user input. It writes the metadata into a yaml file after validating it.
    :param path: the path to the folder the metadata file should be saved to
    :param input_id: the ID of the experiment
    :param name: the name of the experiment
    :param mandatory_mode: if True only mandatory files are filled out
    """

    # TODO: search for id
    filename = [f'{input_id}_{mode}.yaml', f'{input_id}_{mode}.yml']

    # test if metadata for given id already exists
    exist = None
    for f in filename:
        if os.path.exists(os.path.join(path, f)):
            exist = os.path.join(path, f)
            break

    if exist is not None:

        # request user input if file should be edited or overwritten
        print(f'The metadata file for ID {input_id} already exists.')

        # set options how to handle the existing data
        options = ['overwrite file', 'edit file', 'exit']

        # parse user input
        handling = generate_functions.parse_list_choose_one(
            options, f'\nPlease choose what you want to do.')

        # exit program if file should not be edited or overwritten
        if handling == 'exit':
            sys.exit(f'Program terminated.')

        # edit metafile
        elif handling == 'edit file':
            edit_file.edit_file(exist, mode, mandatory_mode, size=size)

        # overwrite metafile
        else:
            generate(path, input_id, mandatory_mode, mode, size=size)
    else:
        generate(path, input_id, mandatory_mode, mode, size=size)


def generate(path, input_id, mandatory_mode, mode, size=80):

    # read in structure file depending on mode
    if mode == 'metadata':
        key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'keys.yaml'))
    else:
        key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'mamplan_keys.yaml'))

    # create metadata dictionary and fill it with the given id
    result_dict = {'project': {'id': input_id}}

    # iterate over main keys of structure
    for item in key_yaml:

        # set parameter to store if the key is mandatory
        mandatory = key_yaml[item]['mandatory']

        # test if the key is optional
        if not mandatory:

            # request user input if the optional key should be filled
            print(f'Do you want to add information for the optional key '
                  f'{item}?')

            # print options and set mandatory to user input
            generate_functions.print_option_list([True, False], False)
            mandatory = generate_functions.parse_input_list([True, False],
                                                            False)

        # test if the key should be filled
        # -> all mandatory keys
        # -> optional keys the user requested
        if mandatory:

            # test if the key is already present in the result dictionary
            if item in result_dict:

                # call function to fill in values and merge them with prefilled
                # information
                result_dict[item] = {**result_dict[item],
                                     **generate_functions.get_redo_value(
                                         key_yaml[item], item, False,
                                         mandatory_mode, result_dict, True,
                                         False, True, mode, key_yaml)}

            # key is not present in the result dictionary
            else:

                # call fucntion to fill in values
                result_dict[item] = generate_functions.get_redo_value(
                    key_yaml[item], item, not key_yaml[item]['mandatory'],
                    mandatory_mode, result_dict, True, False, True, mode, key_yaml)

            # start a loop for editing
            while True:

                # print a summary of the partial result (for the key)
                print(generate_functions.get_summary(result_dict[item],
                                                     size=size))

                # request and parse user input if the filled in values are
                # correct
                correct = generate_functions.parse_list_choose_one(
                    ['True ', 'False '], f'\nIs the input correct? You can '
                                         f'redo it by selecting \'False\'')

                # stop the loop if the input is correct
                if correct:
                    break

                # call the editing function for the part if the input contains
                # errors
                else:
                    result_dict[item] = edit_file.edit_item(
                        item, result_dict[item], key_yaml[item], key_yaml,
                        result_dict, mandatory_mode, mode, size=size,
                        not_editable=not_editable)

    # print full summary
    print(generate_functions.get_summary(result_dict, size=size))

    # print validation report
    print(generate_functions.get_validation(result_dict, mode, size=size))

    # save information to a yaml file and print the filename
    print(f'File is saved to {os.path.join(path, f"{input_id}_{mode}.yaml")}')
    utils.save_as_yaml(result_dict,
                       os.path.join(path, f'{input_id}_{mode}.yaml'))

    # create and print sample names for metadata
    if mode == 'metadata':
        generate_functions.print_sample_names(result_dict, input_id, path,
                                              size=size)
