import re
import os
from itertools import chain
from tabulate import tabulate
import src.utils as utils
import src.generate_metafile as generate
import src.file_reading as file_reading


# This scripts implements functions to find metadata files that contain values
# specified in a search string


# set parameter size to terminal width in order to display printed tables
# correctly
# if that is not possible, set the size to the default value 80
try:
    size = os.get_terminal_size()
except OSError:
    size = 80


def find_projects(key_yaml, dir_path, search, return_dict):
    """
    This function iterates through the search string and evaluates all parts
    within round brackets from the inside to the outside. It calls the function
    'get_search_parameters' for every sub string within brackets. It returns
    all matching metadata files in a dictionary.
    :param dir_path: a folder path that is searched for metadata files
    :param search: a search string containing values that should match the
                   metadata
    :param return_dict: bool: if True the whole metafile is returned,
                              if False just the metafile path is returned
    :return: a dictionary containing all matches
             key=input_id, value=dictionary or path depending on return_dict
    """
    # split parameters linked via or into list

    # read in all *_metadata.yaml(yml) within the path
    metafiles, validation_reports = file_reading.iterate_dir_metafiles(key_yaml, [dir_path],return_false=True)

    # put round brackets around the search string
    search = '(' + search + ')'

    # initialize parameter result with an empty list
    # it is used to store the matching metadata files
    result = []

    # iterate over the read in metadata files
    for metafile in metafiles:

        if 'project' in metafile and 'id' in metafile['project']:

            # initialize parameter sub_list and sub with empty string
            # sub stores parts of the search string that is read in
            # whenever a bracket is reached, the string in sub is evaluated and
            # the result is added to sub_list
            sub_list = ''
            sub = ''

            # set brace_count to 0 meaning that there is currently no open
            # brace
            brace_count = 0

            # iterate over search string
            for letter in search:

                # if an opening bracket is reached, add 1 to brace_count, add
                # the string within sub to the sub_list and set sub to an empty
                # string
                if letter == '(':
                    brace_count += 1
                    sub_list += sub
                    sub = ''

                # if a closing bracket is reached, subtract 1 from brace_count
                elif letter == ')':
                    brace_count -= 1

                    # test if the closing bracket is the last bracket in the
                    # search string
                    if brace_count != 0:

                        # if it is the last bracket, add the string in sub to
                        # the sub_list
                        sub_list += sub

                    else:

                        # if it is a bracket within the search string and sub
                        # is not an empty string then use the function
                        # parse_search_parameters to evaluate the string in sub
                        # and add the result to the sub_string
                        if sub != '':
                            res = parse_search_parameters(metafile, sub)
                            sub_list += str(True) if res else str(False)

                    # set sub to an empty string again
                    sub = ''

                else:

                    # add the current character of the search string to sub
                    sub += letter

            # evaluate the sub_list with parse_search_parameters if it does not
            # equal True or False
            if sub_list != 'True' and sub_list != 'False':
                sub_list = str(parse_search_parameters(metafile, sub_list))

            # add a dictionary containing information about the metadata file
            # to result if it matches the search
            # key: project id
            # value: whole metafile or path to metafile depending on whether
            # result_dict is set to True or False
            if sub_list == 'True':
                result.append(
                    {metafile['project']['id']: metafile['path']
                        if return_dict == False else metafile})

    # return the list of matching metadata files
    return result


def print_summary(result):
    """
    This function prints information about the metadata files that match the
    search string in a table. The information includes the project id, path to
    the metadata file, project name and name of the owner.
    :param result: a list containing dictionaries with project id as key and
                   metadata dictionary as value for every metadata file that
                   matches the search string
    :return: res: a table containing id, path, name and owner of every project
                  whose metadata matches the search string
    """

    #  initialize res as a list and define the headers of the table as the
    #  first list element
    res = [['ID', 'Path', 'Project name', 'Owner']]

    # iterate over dictionaries for matching metadata files
    for elem in result:

        # iterate over metadata IDs
        for key in elem:

            # add the id, path, project_name and owner to res
            res.append(
                [key, elem[key]['path'], elem[key]['project']['project_name'],
                 elem[key]['project']['owner']['name']])

    # convert res into a table using tabulate
    # set format to fancy_grid, define the headers as the first row and set the
    # column width to fit to the terminal size
    res = tabulate(res, tablefmt='fancy_grid', headers='firstrow',
                   maxcolwidths=[size.columns * 1 / 8, size.columns * 3 / 8,
                                 size.columns * 3 / 8, size.columns * 1 / 8])

    # return the table
    return res


def parse_search_parameters(metafile, search):
    """
    This function splits the search parameters at 'or' and stores them in a
    list. Every element within this list is then additionally split at 'and'
    resulting in a nested list. The function 'get_matches' is the called with
    the metafile and the nested search parameters.
    :param metafile: a dictionary containing information of a metadata file
    :param search: the search string containing the values to search for
    :return: result: True if there is a match, else False
    """

    # split the search string at 'or' and store the parts of the search string
    # in a list
    search_parameters = search.split(' or ')

    # iterate over the parts of the search string that were split at or
    for i in range(len(search_parameters)):

        # split parameters linked via 'and' within the 'or-list' -> nested list
        search_parameters[i] = search_parameters[i].split(' and ')

        # iterate over the parts of the search string split at 'and'
        for j in range(len(search_parameters[i])):

            # test if the part is not equal to True or False
            if search_parameters[i][j] != 'True' or 'False':

                # call get_should_be_in to append True or False to the search
                # parameter separated by ':' (depending on whether there is a
                # 'not' in front of the search parameter)
                search_parameters[i][j] = get_should_be_in(
                    search_parameters[i][j])

    # call function get_matches to find matches in the nested list for 'or'
    # and 'and'
    results = get_matches(metafile, search_parameters)

    # if there is at least one True then there is a match (because the value
    # was found in at least one metadata field) and the result is set to True,
    # otherwise the result is set to False
    if True in results:
        result = True
    else:
        result = False

    # return True if there is a match else False
    return result


def get_matches(metafile, search_parameters):
    """
    This function takes a metafile and is recursively called on every element
    of the metafile if the metafile is a list. Otherwise, it calls the function
    'calculate_match' on the metafile to test if the search parameters occur in
    the metadata.
    :param metafile: a dictionary containing information of a metadata file
    :param search_parameters: a nested list containing all search parameters
                              chained by 'or' (outer list) and 'and'
                              (inner lists)
    :return: result: a list containing all matches as boolean values (True and
                     False)
    """

    # initialize an empty list to store the results
    results = []

    # test if the metafile is a list
    if isinstance(metafile, list):

        # iterate over elements in  metadata list
        for x in metafile:

            # call this function for every element
            results += get_matches(x, search_parameters)

    else:

        # if the metafile is not a list call calculate_match for it and add it
        # to result
        results += [calculate_match(metafile, search_parameters)]

    # return the list containing all matches (True or False)
    return results


def calculate_match(metafile, search_parameters):
    """
    This function iterated through all search values that were chained by 'and'
    or 'or' and calls the function 'find_entry' on them to test whether the
    value occurs in the metadata file.
    :param metafile: a dictionary containing information of a metadata yaml
    :param search_parameters: a nested dictionary containing all parameters
                              split at 'or' (outer list) and 'and'
                              (inner lists)
    :return: True if a match was found else False
    """

    # initialize a list to store all matches within the outer list containing
    # parameters that were chained by 'or'
    or_found = []

    # iterate through outer list -> or
    for or_param in search_parameters:

        # initialize a list to store all matches within the inner list
        # containing parameters that were chained by 'and'
        and_found = []

        # iterate through inner list -> and
        for and_param in or_param:

            # split search parameter at ':'
            # last element in list saved in 'should-be_found'
            # -> False if 'not' was specified for the parameter

            # test if the search parameter contains double quotes
            if '"' in and_param:

                # initialize a list to store
                params = []

                # split the search parameter at ':'
                # the last element of the emerging list declares if the
                # parameter should be found in the metafile and is saved in
                # should_be_found and removed from the search parameter
                should_be_found = and_param.split(':')[-1]
                and_param = and_param.rstrip(f':{should_be_found}')

                # split the search parameter into keys and value
                p = generate.split_cond2(and_param)[0]

                # if there is a value for the keys than split it at ':' to get
                # a list of all chained metadata keys and save them in 'params'
                if p[0] != '':
                    params = p[0].split(':')

                # add the value to the 'params' list
                params.append(p[1])

                # add 'should_be_found' to the 'params' list
                params.append(should_be_found)

            else:

                # if there is no double quote in the search parameter then
                # split ist at ':' and save it into 'params'
                # assign the value of the last element to 'should_be_found'
                params = and_param.split(':')
                should_be_found = params[-1]

            # if there are no keys specified and the value was already
            # evaluated (e.g. as part of a sub search string within brackets)
            # then set the match to True if the value equals 'True' and to
            # False if it equals 'False'
            if len(params) == 2 and params[0] == 'True':
                match = True
            elif len(params) == 2 and params[0] == 'False':
                match = False

            else:

                # call find_entry to evaluate match
                match = find_entry(metafile, params[0:-2], params[-2])

            # set match to True if it was found while it was supposed to be
            # found or if it was not found while not being supposed to be found
            # otherwise set match to False
            if (match and should_be_found == 'True') or \
                    (not match and should_be_found == 'False'):
                and_found.append(True)
            else:
                and_found.append(False)

        # append 'True' to the or_found list if all parameters in the inner
        # list for 'and' are True, otherwise append 'False'
        if False not in and_found:
            or_found.append(True)
        else:
            or_found.append(False)

    # return True if at least one parameter chained by 'or' is True, otherwise
    # return False
    return True if True in or_found else False


def get_should_be_in(param):
    """
    This function tests if a 'not' was stated in front of a search value and
    saves this information into the variable 'should_be_found'. The 'not' gets
    removed from the search value and 'should_be_found' is appended at its end
    divided by ':'.
    :param param: a search parameter containing a value that can be chained
                  with keys (e.g. key1:key2:"value") and can contain a 'not'
    :return: p: the search parameter with the appended value for
                'should_be_found' and the removed 'not'
    """

    # test if the given parameter is a list
    if isinstance(param, list):

        #initialize a list to store results for every list element
        p = []

        # iterate over list elements
        for x in param:

            # call this function on the element and append the result to p
            p.append(get_should_be_in(x))

    # if the parameter is not of type list
    else:

        # set 'should_be_in' to True as a default value
        should_be_in = True

        # test if 'not' is present in the parameter
        if 'not ' in param:

            # set 'should_be_in' to False (if 'not' was found)
            should_be_in = False

            # replace 'not' with empty string
            param = param.replace('not ', '')

        # strip whitespaces from the parameter and append 'should_be_in' at the
        # end divided by ':'
        p = param.strip() + (':' + str(should_be_in))

    # return the parameter containing 'should_be_in'
    return p


def find_entry(metafile, targets, target_value):
    """
    This function tests if a value (and key) is found in a metadata dictionary.
    :param metafile: dictionary containing information of metadata yaml
    :param targets: list of keys in order of depth in yaml
                    -> [key1, key2, key3] for 'key1:key2:key3:value'
    :param target_value: the value that should be found
    :return: True if match was found, else False
    """

    # test if keys were specified to restrict the metadata fields that should
    # be searched
    if len(targets) >= 1:

        # initialize the result with the metafile
        result = [metafile]

        # iterate over the keys
        for key in targets:

            # initialize 'r2' with an empty list
            # this parameter is used to store part results for every element in
            # 'result'
            r2 = []

            # iterate over elements in 'result'
            for item in result:

                # call find_keys from the script utils.py for the current key
                # and result item to get a list of all occurrences of this key
                # within the item
                r2 += list(utils.find_keys(item, key))

            # set the result to the part result
            # this way the metadata fields get restricted because just the
            # parts with matching keys are used
            result = r2

    # iterate through whole dictionary if no key was specified in 'targets'
    else:
        result = list(utils.find_values(metafile, target_value))

    # iterate over the results
    for value in result:

        # test if the values match if they are of type int or boolean and
        # return True if that is the case
        if (type(target_value) is int and type(value) is int) or \
                (type(target_value) is bool and type(value) is bool):
            if target_value == value:
                return True

        # test if the search value is a substring of the metadata value if they
        # are of type string and return True if that is the case
        else:
            if all(elem in str(value).lower() for elem in str(target_value).lower().split(' ')):
                return True

    # return False if no match was found
    return False
