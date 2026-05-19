from fred.src.input_functions import Input
from fred.src.autogenerate import Autogenerate
from fred.src.exceptions import GoBackSignal
from fred.src import validate_yaml
from fred.src import utils
from fred.src.heatmap import create_heatmap
import copy
import os
from jinja2 import Template

template = Template(
    """
        <h3>{{ header }}</h3>
                        
            {% for elem in plots %}

                {% if loop.index0 != 0 %}
                    <hr style="border-style: dotted;" />
                {% endif %}
                                
                <div style="woverflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:5">
                    {{ elem.plot }}

                    {% if elem.missing_samples %}
                        <i>Conditions without samples:</i>
                        {{ elem.missing_samples }}
                    {% endif %}
                </div>
                                
            {% endfor %} 
                
        """
)


class Generate(Input):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tmp_dir = os.path.join(os.path.expanduser("~"), ".fred", "tmp")
        self.tmp_path = os.path.join(tmp_dir, f"{self.project_id}_autosave.yaml")

    def _autosave(self):
        os.makedirs(os.path.dirname(self.tmp_path), exist_ok=True)
        utils.save_as_yaml(self.result_dict, self.tmp_path)

    def _delete_autosave(self):
        if os.path.exists(self.tmp_path):
            os.remove(self.tmp_path)

    def _resolve_go_back(self, position, mandatory_keys):
        """
        Handle GoBackSignal at one level: find the previous history entry that
        belongs to this level, re-prompt it, and return the new idx for the
        mandatory loop.  Returns None if history is empty (no change needed).
        Raises GoBackSignal if the entry belongs to a parent level.
        """
        while True:
            if not self.field_history:
                print("[No previous field to go back to]")
                return None
            hist_position, hist_key, hist_structure = self.field_history[-1]
            target_idx = None
            for i, k in enumerate(mandatory_keys):
                expected = position + [k]
                if (len(hist_position) >= len(expected)
                        and hist_position[:len(expected)] == expected):
                    target_idx = i
                    break
            if target_idx is None:
                raise  # re-raise GoBackSignal so the parent level handles it
            self.field_history.pop()
            display_pos = " > ".join(str(p) for p in hist_position)
            print(f"\n[Going back to: {display_pos}]")
            try:
                new_value = self.parse_input_value(hist_key, hist_structure)
                self.fill_key(hist_position, new_value, self.result_dict)
                # Truncate any lists that have stale elements beyond the re-prompted index
                for path_i, step in enumerate(hist_position):
                    if isinstance(step, int):
                        try:
                            parent_node = self.result_dict
                            for s in hist_position[:path_i]:
                                parent_node = parent_node[s]
                            if isinstance(parent_node, list) and len(parent_node) > step + 1:
                                for stale_idx in range(step + 1, len(parent_node)):
                                    stale_prefix = hist_position[:path_i] + [stale_idx]
                                    self.field_history = [
                                        e for e in self.field_history
                                        if not (len(e[0]) >= len(stale_prefix)
                                                and e[0][:len(stale_prefix)] == stale_prefix)
                                    ]
                                del parent_node[step + 1:]
                        except (KeyError, IndexError, TypeError):
                            pass
                self.field_history.append((hist_position, hist_key, hist_structure))
                return target_idx + 1
            except GoBackSignal:
                continue  # user typed !back again → go further back

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

            else:

                if (
                    'special_case' in item_structure
                    and 'generated' in item_structure['special_case']
                    and item_structure['special_case']['generated'] == 'now'
                ):
                    struct_copy = copy.deepcopy(item_structure)
                    struct_copy['list'] = False
                    not_removable_keys = [
                        k for k, v in item_structure['value'].items()
                        if v.get('list')
                        and 'special_case' in v
                        and v['special_case'].get('edit') == 'not removable'
                    ]
                    for i in range(len(self.setting_ids)):
                        preserved = {}
                        if isinstance(values[i], dict):
                            for k in not_removable_keys:
                                if k in values[i]:
                                    preserved[k] = list(values[i][k])
                        self.parse_lists(struct_copy, position + [i], indent + 1, self.result_dict)
                        for k, existing_vals in preserved.items():
                            try:
                                new_vals = utils.find_position(self.result_dict, position + [i, k])
                                combined = existing_vals + [v for v in new_vals if v not in existing_vals]
                                self.fill_key(position + [i, k], combined, self.result_dict)
                            except (KeyError, IndexError, TypeError):
                                pass
                    return

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

                all_options.append("add element to list")

                print(
                    f"Please choose how you want to edit the list choosing "
                    f"from the following options (1-{len(all_options)}) divided by "
                    f"comma."
                )

                self.print_option_list(all_options, False)
                chosen_options = self.parse_input_list(all_options, False)

                if "remove element from list" in all_options:
                    all_options.remove("remove element from list")
                if "add element to list" in all_options:
                    all_options.remove("add element to list")

                remove_options = []

                if "remove element from list" in chosen_options:

                    print(
                        f"Please choose the list elements you want to remove"
                        f" (1-{len(all_options)}) divided by comma."
                    )

                    self.print_option_list(all_options, False)
                    remove_options = self.parse_input_list(all_options, False)

                edit_options = {}

                for i in range(len(all_options)):

                    if all_options[i] in remove_options:
                        action = "remove"
                    elif all_options[i] in chosen_options:
                        action = "edit"
                    else:
                        action = None

                    edit_options[all_options[i]] = {"element": values[i], "action": action, "index": i}

                for key in edit_options:

                    if edit_options[key]["action"] == "edit":

                        display_name = key.replace("\n", " | ")
                        print(
                            f"\n"
                            f'{"".center(self.size, "-")}\n'
                            f'{f"{display_name}".center(self.size, " ")}\n'
                            f'{"".center(self.size, "-")}\n'
                        )

                        self.edit_item(copy.deepcopy(edit_options[key]['element']), position + [edit_options[key]['index']], indent+1)

                    if edit_options[key]["action"] == "remove":

                        result_pos = utils.find_position(self.result_dict, position)
                        result_pos.pop(result_pos.index(edit_options[key]['element']))

                if "add element to list" in chosen_options:

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
                        self.parse_lists(item_structure, position, indent, self.result_dict)

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
                print(
                    f"Please choose the keys (1-{len(edit_index)}) you want to edit"
                    f" divided by comma."
                )

                self.print_option_list(edit_index, False)
                edit_index = self.parse_input_list(edit_index, False)

            if "all" in edit_index:

                self.parse_lists(item_structure, position, indent, self.result_dict)

            else:

                for key in edit_index:

                    if key in values:

                        self.edit_item(values[key], position + [key], indent+1)

                    else:

                        self.parse_lists(item_structure['value'][key], position + [key], indent+1, self.result_dict)

        else:
            self.fill_key(
                position,
                (
                    self.parse_input_value(position[-1], item_structure)
                ),
                self.result_dict
            )

    def generate(self):
        if os.path.exists(self.tmp_path):
            resume = self.parse_list_choose_one(
                ["yes", "no"],
                f"Found autosave for ID '{self.project_id}'. Resume where you left off?"
            )
            if resume == "yes":
                self.result_dict = utils.read_in_yaml(self.tmp_path)
                print("Resuming...")
            else:
                self._delete_autosave()

        indent = 1
        for part in self.key_yaml:
            if part in self.result_dict:
                print(f"\n[Resumed] Section '{part}' already completed, skipping.")
                continue
            while True:
                try:
                    self.parse_lists(self.key_yaml[part], [part], indent, self.result_dict)
                    break
                except GoBackSignal:
                    print("[No previous field to go back to]")
                    if part in self.result_dict:
                        del self.result_dict[part]
                    self.field_history = [
                        e for e in self.field_history if not (e[0] and e[0][0] == part)
                    ]
                    self.conditions = {}
            self._autosave()
            while True:
                if part == "experimental_setting":
                    plot = create_heatmap.get_heatmap(
                        {part: self.result_dict[part]}, self.key_yaml
                    )
                    for elem in plot:
                        if elem[1] is not None:
                            elem[1].show()
                else:
                    print(self.get_summary(self.result_dict[part]))
                answer = self.parse_list_choose_one(
                    ["yes", "no"],
                    f"Is the '{part}' section correct?"
                )
                if answer == "yes":
                    break
                self.edit_item(self.result_dict[part], [part], indent)
                self._autosave()
        for elem in self.generate_end:
            func = getattr(Autogenerate, f"get_{elem[-1]}")
            fill_val = func(Autogenerate(self, elem))
            if fill_val is not None:
                self.fill_key(elem, fill_val, self.result_dict)

        # print validation report
        # print(self.get_validation(self.result_dict))
        print(self.get_summary(self.result_dict))
        # save information to a yaml file and print the filename
        print(
            f"File is saved to "
            f'{os.path.join(self.path, f"{self.project_id}{self.filename}.yaml")}'
            f""
        )
        utils.save_as_yaml(
            self.result_dict,
            os.path.join(self.path, f"{self.project_id}{self.filename}.yaml"),
        )
        self._delete_autosave()

    def print_sample_names(self):
        """
        This function creates a string out of all generated filenames that can
        be printed.
        """
        samples = list(
            utils.find_list_key(self.result_dict, "technical_replicates:sample_name")
        )
        print(
            f'{"".center(self.size, "-")}\n'
            f'{"SAMPLE NAMES".center(self.size, " ")}\n'
            f'{"".center(self.size, "-")}\n'
        )
        sample_names = ""
        for elem in samples:
            for name in elem:
                sample_names += f"- {name}\n"
        print(sample_names)
        save = self.parse_list_choose_one(
            ["True ", "False "], "Do you want to save the sample names into a file?"
        )
        if save:
            text_file = open(
                os.path.join(self.path, f"{self.project_id}_samples.txt"), "w"
            )
            text_file.write(sample_names)
            text_file.close()
            print(
                f"The sample names have been saved to file "
                f"'{self.path}/{self.project_id}_samples.txt'."
            )

    def get_summary(self, result):
        summary = ""
        summary += (
            f'{"".center(self.size, "=")}\n'
            f'{"SUMMARY".center(self.size, " ")}\n'
            f'{"".center(self.size, "=")}\n'
        )
        summary += self.print_summary(result, 1, False)
        summary += f"\n\n"
        summary += f'{"".center(self.size, "=")}\n'
        return summary

    def get_validation(self, result):
        validation_reports = {
            "all_files": 1,
            "corrupt_files": {"count": 0, "report": []},
            "error_count": 0,
            "warning_count": 0,
        }
        file_reports = {"file": result, "error": None, "warning": None}
        report = ""
        report += (
            f'{"FILE VALIDATION".center(self.size, " ")}\n'
            f'{"".center(self.size, "-")}\n'
        )
        (
            valid,
            missing_mandatory_keys,
            invalid_keys,
            invalid_entries,
            invalid_values,
            logical_warn,
        ) = validate_yaml.validate_file(result, self.key_yaml, self.filename)
        if not valid:
            validation_reports["corrupt_files"]["count"] = 1
            validation_reports["error_count"] += (
                len(missing_mandatory_keys)
                + len(invalid_keys)
                + len(invalid_entries)
                + len(invalid_values)
            )
            file_reports["error"] = (
                missing_mandatory_keys,
                invalid_keys,
                invalid_entries,
                invalid_values,
            )
        if len(logical_warn) > 0:
            validation_reports["corrupt_files"]["count"] = 1
            validation_reports["warning_count"] += len(logical_warn)
            file_reports["warning"] = logical_warn
        validation_reports["corrupt_files"]["report"].append(file_reports)

        report += (
            f'Found {validation_reports["error_count"]} errors and '
            f'{validation_reports["warning_count"]} warnings.\n'
        )

        if validation_reports["corrupt_files"]["count"] > 0:
            rep = ""
            for _report in validation_reports["corrupt_files"]["report"]:
                rep += f'{"".center(self.size, "_")}\n\n'
                rep += validate_yaml.print_full_report(
                    _report["file"], _report["error"], _report["warning"], self.size
                )
            rep += f'{"".center(self.size, "_")}\n\n'
            report += rep
        return report

    def print_summary(self, result, depth, is_list):
        """
        This function parses the dictionary into a string with the same
        structure as it will be saved to the yaml file
        :param result: the filled dictionary
        :param depth: an integer that specifies the depth of indentation
        :param is_list: a bool that states if a key contains a list
        :return: summary: a string that contains all entered information
        """
        summary = ""
        if isinstance(result, dict):
            for key in result:
                printed_summary = self.print_summary(result[key], depth + 1, is_list)
                if key == list(result.keys())[0] and is_list:
                    summary = (
                        f'{summary}\n{"    " * (depth - 1)}{"  - "}'
                        f"{key}: {printed_summary}"
                    )
                else:
                    summary = f'{summary}\n{"    " * depth}{key}: ' f"{printed_summary}"
        elif isinstance(result, list):
            for elem in result:
                if not isinstance(elem, list) and not isinstance(elem, dict):
                    summary = f'{summary}\n{"    " * (depth - 1)}{"  - "}' f"{elem}"
                else:
                    summary = f"{summary}" f"{self.print_summary(elem, depth, True)}"
        else:
            summary = f"{summary}{result}"
        return summary

    def parse_lists(self, structure, position, indent, return_dict, is_factor=False):
        if isinstance(structure["value"], dict):
            try:
                elem_index = len(utils.find_position(self.result_dict, position))
            except KeyError:
                elem_index = 0
            redo = True

            while redo:
                self.print_header(structure["display_name"], indent)
                print(utils.print_desc(structure["desc"], size=self.size), "\n")
                is_list = False
                if "special_case" in structure and "merge" in structure["special_case"]:
                    self.fill_key(
                        (
                            position + [elem_index]
                            if structure["list"] or is_factor
                            else position
                        ),
                        self.parse_input_value(
                            position[-1],
                            structure["value"][structure["special_case"]["merge"]],
                        ),
                        return_dict,
                    )
                    if is_factor:
                        is_list = True
                elif (
                    "special_case" in structure
                    and "value_unit" in structure["special_case"]
                ):
                    if structure["list"] or is_factor:
                        self.fill_key(
                            position,
                            self.get_list_value_unit(position[-1], structure),
                            return_dict,
                        )
                    else:
                        self.fill_key(
                            position, self.get_value_unit(structure), return_dict
                        )
                else:
                    self.input_keys(
                        structure["value"],
                        (
                            position + [elem_index]
                            if structure["list"] or is_factor
                            else position
                        ),
                        indent,
                        return_dict,
                        is_factor=is_factor,
                    )
                self.print_headline(indent)
                if (structure["list"] and not is_factor) or (is_list and is_factor):
                    try:
                        redo = self.parse_list_choose_one(
                            ["True ", "False "],
                            f"\nDo you want to add another "
                            f'{structure["display_name"]}?',
                        )
                    except GoBackSignal:
                        raise
                    elem_index += 1
                else:
                    redo = False

        else:
            if structure["list"] or is_factor:
                value = self.get_input_list(structure, position[-1])
                self.fill_key(position, value, return_dict)
            else:
                value = self.parse_input_value(position[-1], structure)
                self.field_history.append((list(position), position[-1], structure))
                self.fill_key(position, value, return_dict)

    def print_headline(self, indent):
        if indent > 1:
            delim = "-"
        else:
            delim = "_"
        print(f'\n{"".center(self.size, delim)}\n')

    def print_header(self, key, indent):
        if indent > 1:
            delim = "-"
            new_line = ""
        else:
            delim = "_"
            new_line = "\n"
        print(
            f"\n"
            f'{"".center(self.size, delim)}{new_line}\n'
            f'{f"{key}".center(self.size, " ")}\n'
            f'{"".center(self.size, delim)}\n'
        )

    def input_keys(self, structure, position, indent, return_dict, is_factor=False):
        optionals = []
        desc = []
        mandatory_keys = []

        # Categorize keys into mandatory and optional
        for key in structure:
            if structure[key]["mandatory"] or (
                "special_case" in structure[key]
                and (
                    "generated" in structure[key]["special_case"]
                    or "factor" in structure[key]["special_case"]
                )
            ):
                mandatory_keys.append(key)
            else:
                if (
                    not (
                        "special_case" in structure[key]
                        and "factor" in structure[key]["special_case"]
                        and structure[key]["special_case"]["factor"]
                    )
                    or structure[key]["list"]
                ):
                    optionals.append(key)
                    desc.append(structure[key]["desc"])

        idx = 0
        while True:  # outer: restarts mandatory+optional when go-back hits optional phase
            # --- Mandatory phase ---
            while idx < len(mandatory_keys):
                key = mandatory_keys[idx]
                try:
                    if "special_case" in structure[key]:
                        if (
                            "factor" in structure[key]["special_case"]
                            and structure[key]["special_case"]["factor"]
                        ):
                            if "list" in structure[key] and structure[key]["list"]:
                                self.fill_key(
                                    position + [key], [structure[key]["value"]], return_dict
                                )
                            else:
                                self.fill_key(
                                    position + [key], structure[key]["value"], return_dict
                                )
                        elif "generated" in structure[key]["special_case"]:
                            if structure[key]["special_case"]["generated"] == "now":
                                func = getattr(Autogenerate, f"get_{key}")
                                fill_val = func(Autogenerate(self, position + [key]))
                                if fill_val is not None:
                                    self.fill_key(position + [key], fill_val, return_dict)
                                    if not isinstance(structure[key]["value"], dict):
                                        print(f'\n---\n{structure[key]["desc"]}\n')
                                        print(
                                            f"{key}: {utils.find_position(self.result_dict, position + [key])}"
                                        )
                            elif structure[key]["special_case"]["generated"] == "end":
                                self.generate_end.append(position + [key])
                            elif structure[key]["special_case"]["generated"] == "fill":
                                self.fill_key(
                                    position + [key], structure[key]["value"], return_dict
                                )
                                optionals.append(key)
                                desc.append(structure[key]["desc"])
                        elif "value_unit" in structure[key]["special_case"]:
                            if "list" in structure[key]:
                                self.fill_key(
                                    position + [key],
                                    self.get_list_value_unit(key, structure),
                                    return_dict,
                                )
                            else:
                                self.fill_key(
                                    position + [key],
                                    self.get_value_unit(structure),
                                    return_dict,
                                )
                        elif "merge" in structure[key]["special_case"]:
                            merge_structure = structure[key]["value"][
                                structure[key]["special_case"]["merge"]
                            ]
                            value = self.parse_input_value(key, merge_structure)
                            self.fill_key(position + [key], value, return_dict)
                            if not is_factor:
                                self.field_history.append(
                                    (list(position + [key]), key, merge_structure)
                                )
                        else:
                            self.parse_lists(
                                structure[key],
                                position + [key],
                                indent + 1,
                                return_dict,
                                is_factor=is_factor,
                            )
                    else:
                        self.parse_lists(
                            structure[key],
                            position + [key],
                            indent + 1,
                            return_dict,
                            is_factor=is_factor,
                        )
                    idx += 1
                except GoBackSignal:
                    new_idx = self._resolve_go_back(position, mandatory_keys)
                    if new_idx is not None:
                        try:
                            node = self.result_dict
                            for step in position:
                                node = node[step]
                            if isinstance(node, dict):
                                for k in mandatory_keys[new_idx:]:
                                    node.pop(k, None)
                                setting_id = node.get("setting_id")
                                if setting_id and setting_id in self.conditions:
                                    del self.conditions[setting_id]
                        except (KeyError, IndexError, TypeError):
                            pass
                        idx = new_idx
                    # If None: no history, idx unchanged → re-prompt current key
                    # If GoBackSignal raised by _resolve_go_back: propagates to parent

            # --- Optional phase ---
            if len(optionals) == 0 or self.mandatory_only:
                break

            print(
                f"\nDo you want to add any of the following optional keys?"
                f" (1,...,{len(optionals)} or n)\n"
            )
            self.print_option_list(optionals, desc)
            options = self.parse_input_list(optionals, True)

            if not options:
                break

            optional_interrupted = False
            for option in options:
                try:
                    if (
                        "special_case" in structure[option]
                        and "generated" in structure[option]["special_case"]
                        and structure[option]["special_case"]["generated"] != "fill"
                    ):
                        if structure[option]["special_case"]["generated"] == "now":
                            func = getattr(Autogenerate, f"get_{option}")
                            fill_val = func(Autogenerate(self, position + [option]))
                            if fill_val is not None:
                                self.fill_key(
                                    position + [option], fill_val, return_dict
                                )
                        elif structure[option]["special_case"]["generated"] == "end":
                            self.generate_end.append(position + [option])
                    else:
                        self.parse_lists(
                            structure[option],
                            position + [option],
                            indent + 1,
                            return_dict,
                            is_factor=is_factor,
                        )
                except GoBackSignal:
                    new_idx = self._resolve_go_back(position, mandatory_keys)
                    if new_idx is not None:
                        try:
                            node = self.result_dict
                            for step in position:
                                node = node[step]
                            if isinstance(node, dict):
                                for k in mandatory_keys[new_idx:]:
                                    node.pop(k, None)
                                for opt in optionals:
                                    node.pop(opt, None)
                                setting_id = node.get("setting_id")
                                if setting_id and setting_id in self.conditions:
                                    del self.conditions[setting_id]
                        except (KeyError, IndexError, TypeError):
                            pass
                        idx = new_idx
                        optional_interrupted = True
                        break  # exit for loop; outer while will restart from idx
                    # If None: no history, skip this optional and continue
                    # If GoBackSignal raised by _resolve_go_back: propagates to parent

            if optional_interrupted:
                continue  # restart outer while True → redo mandatory from idx, then optional

            break

    def fill_key(self, position, value, fill_dict):
        if len(position) > 0:
            if len(position) == 1:
                fill_dict[position[0]] = value
            else:
                if type(position[1]) == str:
                    if type(position[0]) == str and position[0] not in fill_dict:
                        fill_dict[position[0]] = {}
                else:
                    if position[0] not in fill_dict:
                        fill_dict[position[0]] = []
                    if len(fill_dict[position[0]]) < position[1] + 1:
                        for i in range(len(fill_dict[position[0]]), position[1] + 1):
                            fill_dict[position[0]].append({})
                self.fill_key(position[1:], value, fill_dict[position[0]])
        else:
            print("NO POSITION")
