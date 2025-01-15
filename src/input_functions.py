import os
from src import utils
import datetime
from tabulate import tabulate
import readline
import copy
import json
import re
from src.web_interface import wi_utils


class WhitelistCompleter:
    def __init__(self, whitelist):
        self.whitelist = whitelist

    def complete(self, text, state):
        results = [x for x in self.whitelist if
                   text.lower() in x.lower()] + [None]
        if len(results) > 30:
            results = results[:30]
        return results[state]


class Input:

    def __init__(self, path, project_id, mandatory_only, filename, key_yaml):
        self.path = path
        self.project_id = project_id
        self.mandatory_only = mandatory_only
        self.filename = filename
        self.key_yaml = key_yaml
        self.result_dict = {}
        self.size = os.get_terminal_size().columns
        self.conditions = {}
        self.publications = {}
        self.generate_end = []

    def parse_input_value(self, key, structure, allow_float=False):
        """
        This function lets the user enter an input and tests if the input is
        valid.
        :param key: the key that should be filled
        :param structure: dictionary containing information about the key
        """

        # read in whitelist if the key has one or set the whitelist to None
        if structure['whitelist']:
            whitelist = utils.get_whitelist(key, self.result_dict)
        else:
            whitelist = None

        # test if a whitelist is defined
        if whitelist is not None:

            # test if the whitelist is a dictionary
            if isinstance(whitelist['whitelist'], dict):

                # rewrite the whitelist to a list
                w = [x for xs in list(whitelist['whitelist'].values()) if xs is
                     not None for x in xs]

                # use autocomplete if the whitelist > 30 values
                if len(w) > 30:
                    # TODO: print_desc Funktion
                    print(f'\n---\n{structure["desc"]}')
                    input_value = self.complete_input(w, key)

                    # repeat if the input value does not match the whitelist
                    while input_value not in w:
                        print(f'The value you entered does not match the '
                              f'whitelist. Try tab for autocomplete.')
                        input_value = self.complete_input(w, key)

                else:

                    # parse grouped whitelist if the whitelist < 30 values
                    # TODO: description for experimental factors + factor desc
                    input_value = self.parse_group_choose_one(
                        whitelist['whitelist'], w, f'{key}:')

            # use autocomplete if the whitelist > 30 values
            elif len(whitelist['whitelist']) > 30:
                # TODO: print_desc + remove duplicate -> own function
                print(f'\n---\n{structure["desc"]}')
                input_value = self.complete_input(whitelist['whitelist'], key)

                # repeat if the input value does not match the whitelist
                while input_value not in whitelist['whitelist']:
                    print(f'The value you entered does not match the '
                          f'whitelist. Try tab for autocomplete.')
                    input_value = self.complete_input(whitelist['whitelist'], key)

            # print indexed whitelist and parse user input
            else:
                # TODO: print_desc
                print(f'\n---\n{structure["desc"]}')
                input_value = self.parse_list_choose_one(
                    whitelist['whitelist'], f'{key}:')

            # TODO: remove w_key?
            w_key = None
            if whitelist['whitelist_type'] == 'plain_group':
                for k in whitelist['whitelist_keys']:
                    if input_value.endswith(f' ({k})'):
                        input_value = input_value.replace(f' ({k})', '')
                        w_key = k

            # test if the whitelist contains the key 'headers'
            if 'headers' in whitelist:
                if whitelist['whitelist_type'] == 'group' or whitelist[
                        'whitelist_type'] == 'plain_group' and w_key is not None:
                    if w_key in whitelist['headers']:
                        headers = whitelist['headers'][w_key].split(' ')
                        vals = input_value.split(' ')

                        # create a dictionary to store the new value
                        value = {}

                        # iterate through the headers and save the header and value of the
                        # same index into a dictionary with header as key
                        for i in range(len(headers)):
                            value[headers[i]] = vals[i]

                        # overwrite the input value with the dictionary
                        input_value = value

                else:

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

        # no whitelist
        else:

            # print a description if one is stated in the metadata structure
            # TODO: print_desc
            if structure["desc"] != '':
                print(f'\n---\n{structure["desc"]}\n')

            # input type boolean
            if structure['input_type'] == 'bool':
                input_value = self.parse_list_choose_one(
                    ['True ', 'False '], f'Is the sample {key}')

            else:

                # print the key, add a newline if a description was printed
                if structure["desc"] == '':
                    input_value = input(f'\n{key}: ')
                else:
                    input_value = input(f'{key}: ')

                # no user input -> repeat
                if input_value == '':
                    print(f'Please enter something.')
                    input_value = self.parse_input_value(key, structure, allow_float=allow_float)

                # input type number
                # TODO: allow float
                if structure['input_type'] == 'number':
                    try:
                        input_value = int(input_value)
                    except ValueError:
                        if allow_float:
                            try:
                                input_value = float(input_value)
                            except ValueError:
                                print(f'Input must be of type int or float. Try again.')
                                input_value = self.parse_input_value(key, structure, allow_float=allow_float)
                        else:
                            print(f'Input must be of type int. Try again.')
                            input_value = self.parse_input_value(key, structure, allow_float=allow_float)

                # input type date (format dd.mm.yyyy)
                elif structure['input_type'] == 'date':
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
                        input_value = self.parse_input_value(key, structure, allow_float=allow_float)

                else:

                    # input type restricted_short_text
                    if structure['input_type'] == 'restricted_short_text':
                        if 'special_case' in structure and 'restriction' in structure['special_case']:
                            if 'max_length' in structure['special_case']['restriction'] and len(input_value) > structure['special_case']['restriction']['max_length']:
                                print(f'Input must not exceed {structure["special_case"]["restriction"]["max_length"]} characters. Please try again.')
                                input_value = self.parse_input_value(key, structure, allow_float=allow_float)
                            elif 'regex' in structure['special_case']['restriction']:
                                pattern = re.compile(structure['special_case']['restriction']['regex'])
                                if pattern.match(input_value):
                                    print(f'Input does not conform to defined pattern. Please try again.')
                                    input_value = self.parse_input_value(key,
                                                                         structure, allow_float=allow_float)

                    # invalid character
                    if '\"' in input_value:
                        print(f'Invalid symbol \'\"\'. Please try again.')
                        input_value = self.parse_input_value(key, structure, allow_float=allow_float)
                    elif '{' in input_value:
                        print(f'Invalid symbol \'{"{"}\'. Please try again.')
                        input_value = self.parse_input_value(key, structure, allow_float=allow_float)
                    elif '}' in input_value:
                        print(f'Invalid symbol \'{"}"}\'. Please try again.')
                        input_value = self.parse_input_value(key, structure, allow_float=allow_float)
                    elif '|' in input_value:
                        print(f'Invalid symbol \'|\'. Please try again.')
                        input_value = self.parse_input_value(key, structure, allow_float=allow_float)

        # return the user input
        return input_value

    def parse_list_choose_one(self, whitelist, header):
        """
        This function prints an indexed whitelist and prompts the user to
        choose a value by specifying the index.
        :param whitelist: a list of values for the user to choose from
        :param header: a headline or description that should be printed
        :return: value: the whitelist value chosen by the user
        """

        # print the given header and indexed whitelist and parse the user input
        try:
            print(f'{header}\n')
            self.print_option_list(whitelist, False)
            value = whitelist[int(input()) - 1]

        # redo the input prompt if the user input is not an integer
        except (IndexError, ValueError):
            print(f'Invalid entry. Please enter a number between 1 and '
                  f'{len(whitelist)}')
            value = self.parse_list_choose_one(whitelist, header)

        # TODO: direkt bool benutzen?
        if value == 'True ':
            value = True
        elif value == 'False ':
            value = False

        # return the user input
        return value

    def parse_group_choose_one(self, whitelist, w, header):
        """
        This function prints a grouped whitelist with indexes and lets the user
        choose one value.
        :param whitelist: the grouped whitelist as a dictionary
        :param w: a list containing all whitelist values
        :param header: a header that should be printed
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

            # select the whitelist value that fits the input index
            value = w[int(input()) - 1]

        # redo the input if the passed value is not an integer >1
        except (IndexError, ValueError):
            print(f'Invalid entry. Please enter a number between 1 and '
                  f'{len(whitelist)}')
            value = self.parse_list_choose_one(whitelist, header)

        # return the user input
        return value

    def get_input_list(self, node, item):
        """
        This function asks the user to enter a list of values divided by comma and
        parses the input.
        :param node: a part of the keys.yaml
        :param item: the key that should be filled
        :return: used_values: the filled in list of values
        """
        # test if a whitelist exists for the item or if the special case 'merge'
        # was defined (means that the input is treated like a single value and then
        # split into a dictionary, e.g. gene -> gene_name, ensembl_id)
        if 'whitelist' in node and node['whitelist'] or 'special_case' in node \
                and 'merge' in node['special_case']:

            # read in whitelist
            whitelist = utils.get_whitelist(item, self.result_dict)

            # test if the whitelist is not None
            if whitelist is not None:

                # test if autocompletion is needed (for whitelists longer than 30)
                if len(whitelist['whitelist']) > 30:

                    # define an empty list to store the input values
                    used_values = []

                    # set parameter redo to True to initiate an input loop
                    redo = True

                    # request user input
                    # TODO: explain autocomplete
                    print(f'\nPlease enter the values for experimental factor '
                          f'{item}.')

                    while redo:

                        # prompt user input via autocompletion
                        input_value = self.complete_input(whitelist['whitelist'],
                                                     item)

                        # test if the input matches the whitelist
                        if input_value in whitelist['whitelist']:

                            # add input to list
                            used_values.append(input_value)

                            # ask the user if he wants to input another item
                            redo = self.parse_list_choose_one(
                                ['True ', 'False '],
                                f'\nDo you want to add another {item}?')

                        else:

                            # print message for invalid value, loop is repeated
                            print(f'The value you entered does not match the '
                                  f'whitelist. Try tab for autocomplete.')

                else:

                    # test for different whitelist types
                    if whitelist['whitelist_type'] == 'plain' or \
                            whitelist['whitelist_type'] == 'plain_group':

                        # for plain whitelists print the whitelist with indices and
                        # parse the user input
                        self.print_option_list(whitelist['whitelist'], '')
                        used_values = self.parse_input_list(whitelist['whitelist'],
                                                       False)

                    elif whitelist['whitelist_type'] == 'group':

                        # rewrite the grouped whitelist of type dictionary into a
                        # plain list
                        w = [x for xs in list(whitelist['whitelist'].values())
                             for
                             x in xs]

                        # set an index i and start with 1
                        i = 1

                        # iterate over the grouped whitelist (dictionary)
                        for w_key in whitelist['whitelist']:

                            # print the key/group of the whitelist
                            print(f'\033[1m{w_key}\033[0m')

                            # iterate over the values within a group
                            for value in whitelist['whitelist'][w_key]:
                                # print the value with the current index
                                print(f'{i}: {value}')

                                # increase the index by 1
                                i += 1

                        # parse the user input (indices) and match them to the
                        # whitelist values using the plain list
                        used_values = self.parse_input_list(w, False)

                # HANDLE PLAIN GROUPED WHITELISTS:
                # a plain grouped whitelist is a grouped whitelist that contains
                # more than 30 values and is therefor to long to be displayed.
                # In order to use autocompletion on such a whitelist, it is
                # rewritten into a plain whitelist. In order to not loose the
                # groups, they are added in round braces to the end of the
                # whitelist values (e.g. value 'GFP' in group 'other' in the
                # enrichment whitelist turns into 'GFP (other)'). The following
                # code removes those groups from the values again and saves them
                # into a list so that they can still be accessed to handle headers
                # in the part below.

                # set an empty list to save keys of plain grouped whitelists
                w_keys = []

                # remove group keys from values if the whitelist is of type
                # 'plain_group'
                if whitelist['whitelist_type'] == 'plain_group':

                    # iterate over the input values
                    for i in range(len(used_values)):

                        # iterate over the keys of the plain group whitelist
                        for k in whitelist['whitelist_keys']:

                            # test if the input value contains the key in braces
                            # at the end
                            if used_values[i].endswith(f' ({k})'):
                                # remove the key from the end of the value
                                used_values[i] = used_values[i].replace(
                                    f' ({k})', '')

                                # add the key to the list of whitelist keys
                                w_keys.append(k)

                # HANDLE HEADERS:
                # Some whitelists contain headers. Those headers represent keys,
                # the input values should be split into. An example can be found in
                # the gene whitelist where the header is set to
                # 'gene_name ensemble_ID' leading to the value
                # 'TSPAN6 ENSG00000000003' being saved as {'gene_name': 'TSPAN6',
                # 'ensemble_ID': 'ENSG00000000003'}. Headers can also occur in
                # grouped whitelists where they are defined for every group
                # separately. In order to know how to split a value in a grouped
                # whitelists one needs to know which group the value belongs to.
                # For grouped whitelists that were rewritten to plain whitelists
                # (see part above) this information is saved in the list w_keys
                # that was filled above. The following splits values into a
                # dictionary according to their headers.

                # test if headers were defined in the whitelist
                if 'headers' in whitelist:

                    # test if whitelist is of type group or plain group and if
                    # w_keys were defined
                    # TODO: works for group?
                    if whitelist['whitelist_type'] == 'group' or \
                            whitelist['whitelist_type'] == 'plain_group' \
                            and len(w_keys) > 0:

                        # iterate over input values
                        for i in range(len(used_values)):

                            # look at index of value in w_keys and see if a header
                            # was defined for that w_key
                            if w_keys[i] in whitelist['headers']:

                                # TODO: own function for header?

                                # split the header at the whitespace to get a list
                                # of keys
                                headers = whitelist['headers'][
                                    w_keys[i]].split(
                                    ' ')

                                # split the value at whitespace to get the
                                # according values
                                vals = used_values[i].split(' ')

                                # initialize an empty dictionary to save the
                                # key-value-pairs to
                                used_values[i] = {}

                                # iterate over the keys in the header
                                for j in range(len(headers)):
                                    # save the key and value at the same index into
                                    # the dictionary
                                    used_values[i][headers[j]] = vals[j]

                    else:

                        # split the header of a non-group whitelist at whitespace
                        # to get a list of keys
                        headers = whitelist['headers'].split(' ')

                        # iterate over the input values
                        for i in range(len(used_values)):

                            # split the value at whitespace to get the
                            # according values
                            vals = used_values[i].split(' ')

                            # initialize an empty dictionary to save the
                            # key-value-pairs to
                            used_values[i] = {}

                            # iterate over the keys in the header
                            for j in range(len(headers)):
                                # save the key and value at the same index into
                                # the dictionary
                                used_values[i][headers[j]] = vals[j]

            else:
                # TODO: kann weg?
                print('No whitelist')
                used_values = [0]

        # no whitelist
        else:

            # get the value_type for the input from the underlying structure
            value_type = node['input_type']

            if 'text' in value_type:
                used_values = []
                redo = True
                while redo:
                    used_values.append(self.parse_input_value(item, node))
                    redo = self.parse_list_choose_one(
                        ['True ', 'False '],
                        f'\nDo you want to add another '
                        f'{item}?')
            else:
                # request user input
                print(
                    f'\nPlease enter a list of {value_type} values for key {item} '
                    f'divided by comma:\n')

                # parse user input
                used_values = self.parse_input_list(value_type, False)

        return used_values

    def print_option_list(self, options, desc):
        """
        This function prints an indexed whitelist.
        :param options: the whitelist values
        :param desc: a description to be printed
        """

        # test if a description was given
        if desc:

            # create a nested list with every sublist containing an index, option
            # and description
            data = [[f'{i + 1}:', f'{options[i]}', desc[i]] for i in
                    range(len(options))]
            # print the nested list as a table
            print(tabulate(data, tablefmt='plain',
                           maxcolwidths=[self.size * 1 / 8,
                                         self.size * 3 / 8,
                                         self.size * 4 / 8]))
        else:

            # create a nested list with every sublist containing only index and
            # option
            data = [[f'{i + 1}:', f'{options[i]}'] for i in
                    range(len(options))]

            # print the nested list as a table
            print(tabulate(data, tablefmt='plain',
                           maxcolwidths=[self.size * 1 / 8,
                                         self.size * 7 / 8]))

    def parse_input_list(self, options, terminable, allow_float=False):
        """
        This function parses the user input for a list.
        :param options: possible input options as a list or 'number' for
                        number input
        :param terminable: a bool to state if nothing can be input
        :return: input_list: a list containing the input values
        """

        # promt user input for a comma divided list
        input_list = input()

        # if terminable is set to True and the user inputs 'n', nothing is returned
        if terminable and input_list.lower() == 'n':
            return None

        else:

            # test if a list was submitted as options
            if isinstance(options, list):

                # split the input list of indices and try to match it with the
                # option list
                try:
                    input_list = [options[int(i.strip()) - 1] for i in
                                  input_list.split(',')]

                except (IndexError, ValueError):

                    # Call this function to redo the input if it does not match the
                    # option list
                    print(f'Invalid entry, try again:')
                    input_list = self.parse_input_list(options, terminable, allow_float=allow_float)

            else:

                try:
                    # split the input list at ','
                    input_list = [x.strip() for x in input_list.split(',')]

                    # convert the input list to integers if they are of type
                    # 'number'
                    if options == 'number':
                        for i in range(len(input_list)):
                            try:
                                input_list[i] = int(input_list[i])
                            except ValueError:
                                if allow_float:
                                    try:
                                        input_list[i] = float(input_list[i])
                                    except ValueError:
                                        print(
                                            f'Invalid entry. Please enter numbers divided '
                                            f'by comma.')
                                        input_list = self.parse_input_list(
                                            options, terminable, allow_float=allow_float)
                                else:
                                    print(
                                        f'Invalid entry. Please enter integers divided '
                                        f'by comma.')
                                    input_list = self.parse_input_list(options,
                                                                       terminable, allow_float=allow_float)

                except IndexError:

                    # Call this function to redo the input if the split or
                    # conversion does not work
                    print(f'Invalid entry. Please enter numbers divided '
                          f'by comma.')
                    input_list = self.parse_input_list(options, terminable, allow_float=allow_float)

        return input_list

    def complete_input(self, whitelist, key):
        """
        This function uses a completer to autofill user input and print matching
        values.
        :param whitelist: a whitelist with possible values
        :param key: the key that should be filled
        :return: input_value: the value that was input by the user
        """

        # TODO: Doku
        print(f'Press tab once for autofill if'
              f' possible or to get a list of up to'
              f' 30 possible input values.\n')
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set show-all-if-ambiguous On")
        readline.parse_and_bind("set show-all-if-unmodified On")
        completer = WhitelistCompleter(whitelist)
        readline.set_completer(completer.complete)
        readline.set_completer_delims('')
        input_value = input(f'{key}: ')
        readline.parse_and_bind('tab: self-insert')
        return input_value

    def get_value_unit(self, structure):
        """
        This function prompts the user to input a value_unit.
        :param result_dict: a dictionary containing filled information
        :return: val_un: a dictionary containing the unit and value
        """

        # create a dictionary containing 'unit' and 'value' and call the
        # 'parse_input_value' function to request those information from the user
        val_un = {'unit': self.parse_input_value('unit', structure['value']['unit']),
                  'value': self.parse_input_value('value', structure['value']['value'], allow_float=True)}

        return val_un

    def get_list_value_unit(self, ex_factor, structure):
        """
        This function prompts the user to enter a list of value_units for
        experimental factors.
        :param result_dict: a dictionary containing filled information
        :param ex_factor: the experimental factor that contains the value_unit
        :return: a dictionary containing a unit and a list of values
        """
        print('HIER')
        # print request for unit input
        print(f'\nPlease enter the unit for factor {ex_factor}:')
        # call function to input unit
        unit = self.parse_input_value('unit', structure['value']['unit'])

        # initialize empty list to store the values with units
        val_un = []

        # print request for value input
        print(f'\nPlease enter int values for factor {ex_factor} (in {unit}) '
              f'divided by comma:')

        # call function to input values
        value = self.parse_input_list('number', False, allow_float=True)

        # iterate through the input values and add a dictionary containing a value
        # and its unit to the 'val_un' list
        for val in value:
            val_un.append({'unit': unit, 'value': val})

        return val_un

    def merge_dicts(self, a, b):
        """
        This function merges two dictionaries with the same structure to create
        one.
        :param a: the first dictionary
        :param b: the second dictionary
        :return: res: the merged dictionary
        """

        # test if dictionary 'a' is a list
        if isinstance(a, list):

            # initialize a list to save combined content of dict 'a' and 'b'
            res = []

            # iterate over dict 'a'
            for i in range(len(a)):
                # call this function for every index of the list and add it to the
                # list
                res.append(self.merge_dicts(a[i], b[i]))

        # if dict 'a' is a dictionary
        elif isinstance(a, dict):

            # get a list of all keys of dict 'b'
            b_keys = list(b.keys())

            # initialize a dictionary to save the combined information to
            res = {}

            # iterate over the keys of dict 'a'
            for key in a.keys():

                # test if the key is in dict 'b'
                if key in b_keys:

                    # call this function to merge the values of the key of dict 'a'
                    # and 'b'
                    res[key] = self.merge_dicts(a[key], b[key])

                    # remove the key from the list of keys for dict 'b'
                    b_keys.remove(key)

                else:

                    # add the key and value from dict 'a' to the result
                    res[key] = a[key]

            # iterate over all keys left in the list of keys for dict 'b'
            for key in b_keys:
                # add the key and value from dict 'b' to the result
                res[key] = b[key]

        # single value
        else:

            # TODO: different lists?

            # set the value of a as the result
            res = a

        return res

    def get_combinations(self, values, key):
        """
        This function creates combinations for experimental factors that can occur
        multiple times in one condition and lets the user choose those that were
        analyzed.
        :param values: the possible values of the factor
        :param key: the name of the experimental factor
        :return: used_values: the combinations of the experimental factor that were
                              used in the conditions
        """
        if isinstance(values, dict):
            is_dict = True
        else:
            is_dict = False
        if 'ident_key' in values:
            if values['ident_key'] in values and len(
                    values[values['ident_key']]) > 1:
                multi = self.parse_list_choose_one(
                    ['True ', 'False '],
                    f'\nCan one sample contain multiple {key}s?')
            else:
                multi = False
                values.pop('ident_key')
        else:
            multi = self.parse_list_choose_one(
                ['True ', 'False '],
                f'\nCan one sample contain multiple {key}s?')

        merge_values = utils.get_combis(copy.deepcopy(values), key,
                                        self.result_dict, self.key_yaml)
        print(
                f'\nPlease select the analyzed combinations for {key} '
                f'(1-{len(merge_values)}) divided by comma:\n')
        self.print_option_list(merge_values, False)
        used_values = self.parse_input_list(merge_values, False)

        return used_values
