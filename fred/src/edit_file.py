from fred.src.generate import Generate
import fred.src.utils as utils
from fred.src.autogenerate import Autogenerate
import copy
import os


class Edit(Generate):

    def create_result_dict(self):
        self.result_dict = utils.read_in_yaml(self.path)
        self.id = self.result_dict['project']['id']
    
    def edit(self):
        options = [key for key in self.key_yaml]
        print(
        f"Choose the parts you want to edit (1,...,{len(options)}) divided "
        f"by comma.\n"
        )
        self.print_option_list(options, False)
        edit_keys = self.parse_input_list(options, True)

        for key in edit_keys:

            if key in self.result_dict:
                self.edit_item(self.result_dict[key], [key], 1)
            else:
                self.parse_lists(self.key_yaml[key], [key], 1, self.result_dict)
        
        for elem in self.generate_end:
            func = getattr(Autogenerate, f"get_{elem[-1]}")
            fill_val = func(Autogenerate(self, elem))
            if fill_val is not None:
                self.fill_key(elem, fill_val, self.result_dict)

        utils.save_as_yaml(self.result_dict, self.path)

    def edit_item(self, values, position, indent):

        if isinstance(position[-1], int):
            structure_pos = [pos for pos in position if isinstance(pos, str)]
            item_structure = list(utils.find_keys(copy.deepcopy(self.key_yaml), structure_pos[-1]))[0]
            item_structure['list'] = False
        else:
            structure_pos = position
            item_structure = list(utils.find_keys(self.key_yaml, position[-1]))[0]
        
        if item_structure['list']:
            
            if not isinstance(item_structure['value'], dict):

                if 'special_case' in item_structure and 'edit' in item_structure['special_case'] and item_structure['special_case']['edit'] == 'not removable':
                    self.fill_key(position, values + self.get_input_list(item_structure, structure_pos[-1]), self.result_dict)
                else:
                    self.fill_key(position, self.get_input_list(item_structure, structure_pos[-1]), self.result_dict)
                #self.parse_lists(item_structure, position, indent, self.result_dict, is_factor=False)
            
            else:

                if 'special_case' in item_structure and 'edit' in item_structure['special_case'] and item_structure['special_case']['edit'] == 'not removable':
                    all_options = []
                else:
                    all_options = ["remove element from list"]

                if 'special_case' in item_structure and 'edit' in item_structure['special_case'] and item_structure['special_case']['edit'] == 'not editable':
                    pass
                elif 'special_case' in item_structure and 'generated' in item_structure['special_case'] and item_structure['special_case']['generated'] == 'end':
                    self.generate_end.append(position)
                else:
                    for i in range(len(values)):

                        if isinstance(values[i], dict):
                            display_keys = [x for x in list(values[i].keys()) if 'id' in x or 'name' in x]
                            if len(display_keys) == 0:
                                display_keys = list(values[i].keys())[:3]
                            str_dict = "\n".join(f"{x}: {values[i][x]}" for x in display_keys)
                            all_options.append(f"edit: {str_dict}")
                        else:
                            all_options.append(f"edit: {values[i]}")

                # add the option to add a new element to the list
                all_options.append("add element to list")

                # request user input
                print(
                    f"Please choose how you want to edit the list choosing "
                    f"from the following options (1-{len(all_options)}) divided by "
                    f"comma."
                )

                # print the list elements as options and parse the user input
                self.print_option_list(all_options, False)
                chosen_options = self.parse_input_list(all_options, False)

                # remove the options that do not represent a distinct list element
                if "remove element from list" in all_options:
                    all_options.remove("remove element from list")
                if "add element to list" in all_options:
                    all_options.remove("add element to list")

                # initialize a list to store list elements that should be removed
                remove_options = []

                # test if user chose to remove elements
                if "remove element from list" in chosen_options:

                    # request user to state elements to delete
                    print(
                        f"Please choose the list elements you want to remove"
                        f" (1-{len(all_options)}) divided by comma."
                    )

                    # print a list of removable elements and parse user input
                    self.print_option_list(all_options, False)
                    remove_options = self.parse_input_list(all_options, False)

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
                        action = "remove"
                    elif all_options[i] in chosen_options:
                        action = "edit"
                    else:
                        action = None

                    # add the list element and its according action to the dict
                    edit_options[all_options[i]] = {"element": values[i], "action": action, "index": i}

                # initialize a new list to save all elements to which do not get
                # removed (edited as well as not edited)

                # iterate over all list elements
                for key in edit_options:

                    # test if the element should be edited
                    if edit_options[key]["action"] == "edit":

                        # TODO: enhance line breaks (if display name > size)

                        # print header for current element
                        display_name = key.replace("\n", " | ")
                        print(
                            f"\n"
                            f'{"".center(self.size, "-")}\n'
                            f'{f"{display_name}".center(self.size, " ")}\n'
                            f'{"".center(self.size, "-")}\n'
                        )

                        # call this function to overwrite the list element with its
                        # edited version
                        self.edit_item(copy.deepcopy(edit_options[key]['element']), position + [edit_options[key]['index']], indent+1)

                    # test if the list element should NOT be removed
                    if edit_options[key]["action"] == "remove":
                        
                        result_pos = utils.find_position(self.result_dict, position)
                        result_pos.pop(result_pos.index(edit_options[key]['element']))
                        
                # test if the user chose to add new list elements
                if "add element to list" in chosen_options:

                    # set the display_name and print it as header for the new
                    # element
                    display_name = item_structure["display_name"]
                    print(
                        f"\n"
                        f'{"".center(self.size, "-")}\n'
                        f'{f"New {display_name}".center(self.size, " ")}\n'
                        f'{"".center(self.size, "-")}\n'
                    )

                    if 'special_case' in item_structure and 'generated' in item_structure['special_case'] and item_structure['special_case']['generated'] == 'now':
                        func = getattr(Autogenerate, f"get_{position[-1]}")
                        self.fill_key(position, func(Autogenerate(self, position)), self.result_dict)

                    else:
                        # get input for new element
                        self.parse_lists(item_structure, position, indent, self.result_dict)

        # item to edit is a dictionary
        elif isinstance(item_structure['value'], dict):
            
            edit_index = []
            edit_all = True
            for value_key in item_structure["value"]:
                if 'special_case' in item_structure["value"][value_key] and 'edit' in item_structure["value"][value_key]['special_case'] and item_structure["value"][value_key]['special_case']['edit'] == 'not editable':
                    edit_all = False
                elif 'special_case' in item_structure["value"][value_key] and 'generated' in item_structure["value"][value_key]['special_case'] and item_structure["value"][value_key]['special_case']['generated'] == 'end':
                    edit_all = False
                    self.generate_end.append(position + [value_key])
                else:
                    edit_index.append(value_key)
            
            if edit_all:
                edit_index.insert(0, "all")

            if len(edit_index) == 0:
                print('No elements to edit under this key.')

            elif len(edit_index) > 1:
                # request input from the user
                print(
                    f"Please choose the keys (1-{len(edit_index)}) you want to edit"
                    f" divided by comma."
                )
                
                # print options for the user and parse the given input
                self.print_option_list(edit_index, False)
                edit_index = self.parse_input_list(edit_index, False)

            # test if 'all' was selected
            if "all" in edit_index:

                # redo input for the whole dictionary
                self.parse_lists(item_structure, position, indent, self.result_dict)

            # keys were selected but not 'all'
            else:

                # iterate over keys
                for key in edit_index:

                        
                    # key was already filled out
                    if key in values:
                            
                        # call this function to edit the value of the key
                        self.edit_item(values[key], position + [key], indent+1)   
                                
                    # key was not filled out yet
                    else:
                            
                        self.parse_lists(item_structure['value'][key], position + [key], indent+1, self.result_dict)

        # item is a single value
        else:
            # call function to input value
            self.fill_key(
                position,
                (
                    self.parse_input_value(position[-1], item_structure)
                ),
                self.result_dict
            )
