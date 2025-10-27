from src.input_functions import Input
from src.autogenerate import Autogenerate
from src import validate_yaml
from src import utils
from src.heatmap import create_heatmap
import os
from jinja2 import Template

template = Template(
        '''
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
                
        '''
        )

class Generate(Input):

    def generate(self):
        indent = 1
        for part in self.key_yaml:
            self.parse_lists(self.key_yaml[part], [part], indent,
                             self.result_dict)
            if part == 'experimental_setting':
                plot = create_heatmap.get_heatmap({part: self.result_dict[part]}, self.key_yaml)
                for elem in plot:
                    if elem[1] is not None:
                        elem[1].show()
            else:
                print(self.get_summary(self.result_dict[part]))
        for elem in self.generate_end:
            func = getattr(Autogenerate, f'get_{elem[-1]}')
            fill_val = func(
                Autogenerate(self, elem))
            if fill_val is not None:
                self.fill_key(elem, fill_val, self.result_dict)

        # print validation report
        #print(self.get_validation(self.result_dict))
        print(self.get_summary(self.result_dict))
        # save information to a yaml file and print the filename
        print(
            f'File is saved to '
            f'{os.path.join(self.path, f"{self.project_id}{self.filename}.yaml")}'
            f'')
        utils.save_as_yaml(self.result_dict, os.path.join(
            self.path, f'{self.project_id}{self.filename}.yaml'))

    def print_sample_names(self):
        """
        This function creates a string out of all generated filenames that can
        be printed.
        """
        samples = list(
            utils.find_list_key(self.result_dict,
                                'technical_replicates:sample_name'))
        print(f'{"".center(self.size, "-")}\n'
              f'{"SAMPLE NAMES".center(self.size, " ")}\n'
              f'{"".center(self.size, "-")}\n')
        sample_names = ''
        for elem in samples:
            for name in elem:
                sample_names += f'- {name}\n'
        print(sample_names)
        save = self.parse_list_choose_one(
            ['True ', 'False '],
            'Do you want to save the sample names into a file?')
        if save:
            text_file = open(os.path.join(
                self.path, f'{self.project_id}_samples.txt'), 'w')
            text_file.write(sample_names)
            text_file.close()
            print(
                f'The sample names have been saved to file '
                f'\'{self.path}/{self.project_id}_samples.txt\'.')

    def get_summary(self, result):
        summary = ''
        summary += f'{"".center(self.size, "=")}\n' \
                   f'{"SUMMARY".center(self.size, " ")}\n' \
                   f'{"".center(self.size, "=")}\n'
        summary += self.print_summary(result, 1, False)
        summary += f'\n\n'
        summary += f'{"".center(self.size, "=")}\n'
        return summary

    def get_validation(self, result):
        validation_reports = {'all_files': 1,
                              'corrupt_files': {'count': 0, 'report': []},
                              'error_count': 0, 'warning_count': 0}
        file_reports = {'file': result, 'error': None, 'warning': None}
        report = ''
        report += f'{"FILE VALIDATION".center(self.size, " ")}\n' \
                  f'{"".center(self.size, "-")}\n'
        valid, missing_mandatory_keys, invalid_keys, \
            invalid_entries, invalid_values, logical_warn = \
            validate_yaml.validate_file(result, self.key_yaml, self.filename)
        if not valid:
            validation_reports['corrupt_files']['count'] = 1
            validation_reports['error_count'] += (
                    len(missing_mandatory_keys) + len(invalid_keys) + len(
                        invalid_entries) + len(invalid_values))
            file_reports['error'] = (
                missing_mandatory_keys, invalid_keys, invalid_entries,
                invalid_values)
        if len(logical_warn) > 0:
            validation_reports['corrupt_files']['count'] = 1
            validation_reports['warning_count'] += len(logical_warn)
            file_reports['warning'] = logical_warn
        validation_reports['corrupt_files']['report'].append(file_reports)

        report += f'Found {validation_reports["error_count"]} errors and ' \
                  f'{validation_reports["warning_count"]} warnings.\n'

        if validation_reports['corrupt_files']['count'] > 0:
            rep = ''
            for _report in validation_reports['corrupt_files']['report']:
                rep += f'{"".center(self.size, "_")}\n\n'
                rep += validate_yaml.print_full_report(_report['file'],
                                                       _report['error'],
                                                       _report['warning'],
                                                       self.size)
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
        summary = ''
        if isinstance(result, dict):
            for key in result:
                printed_summary = self.print_summary(result[key],
                                                     depth + 1, is_list)
                if key == list(result.keys())[0] and is_list:
                    summary = f'{summary}\n{"    " * (depth - 1)}{"  - "}' \
                              f'{key}: {printed_summary}'
                else:
                    summary = f'{summary}\n{"    " * depth}{key}: ' \
                              f'{printed_summary}'
        elif isinstance(result, list):
            for elem in result:
                if not isinstance(elem, list) and not isinstance(elem, dict):
                    summary = f'{summary}\n{"    " * (depth - 1)}{"  - "}' \
                              f'{elem}'
                else:
                    summary = f'{summary}' \
                              f'{self.print_summary(elem, depth, True)}'
        else:
            summary = f'{summary}{result}'
        return summary

    def parse_lists(self, structure, position, indent, return_dict,
                    is_factor=False):

        if isinstance(structure['value'], dict):
            elem_index = 0
            redo = True

            while redo:
                self.print_header(structure['display_name'], indent)
                print(utils.print_desc(structure['desc'], size=self.size),
                      '\n')
                is_list = False
                if 'special_case' in structure and 'merge' in structure['special_case']:
                    self.fill_key(position + [elem_index] if structure['list'] or is_factor else position, self.parse_input_value(
                            position[-1], structure['value'][structure[
                                'special_case']['merge']]), return_dict)
                    if is_factor:
                        is_list = True
                elif 'special_case' in structure and 'value_unit' in structure['special_case']:
                    if structure['list'] or is_factor:
                        self.fill_key(
                                position,
                                self.get_list_value_unit(position[-1], structure),
                                return_dict)
                    else:
                        self.fill_key(
                                position,
                                self.get_value_unit(structure), return_dict)
                else:
                    self.input_keys(
                        structure['value'],
                        position + [elem_index] if structure['list'] or is_factor else position,
                        indent, return_dict, is_factor=is_factor)
                self.print_headline(indent)
                if (structure['list'] and not is_factor) or (is_list and is_factor):
                    redo = self.parse_list_choose_one(
                            ['True ', 'False '],
                            f'\nDo you want to add another '
                            f'{structure["display_name"]}?')
                    elem_index += 1
                else:
                    redo = False

        else:
            self.fill_key(
                position, self.get_input_list(structure, position[-1]) if
                structure['list'] or is_factor else self.parse_input_value(
                    position[-1], structure),
                return_dict)

    def print_headline(self, indent):
        if indent > 1:
            delim = '-'
        else:
            delim = '_'
        print(f'\n{"".center(self.size, delim)}\n')

    def print_header(self, key, indent):
        if indent > 1:
            delim = '-'
            new_line = ''
        else:
            delim = '_'
            new_line = '\n'
        print(f'\n'
              f'{"".center(self.size, delim)}{new_line}\n'
              f'{f"{key}".center(self.size, " ")}\n'
              f'{"".center(self.size, delim)}\n')

    def input_keys(self, structure, position, indent, return_dict,
                   is_factor=False):
        optionals = []
        desc = []
        for key in structure:
            if structure[key]['mandatory'] or \
                    ('special_case' in structure[key] and ('generated' in
                     structure[key]['special_case'] or 'factor' in structure[key]['special_case'])):
                if 'special_case' in structure[key]:
                    if 'factor' in structure[key]['special_case'] and \
                            structure[key]['special_case']['factor']:
                        self.fill_key(position + [key],
                                      structure[key]['value'], return_dict)
                    elif 'generated' in structure[key]['special_case']:
                        if structure[key]['special_case']['generated'] == \
                                'now':
                            func = getattr(Autogenerate, f'get_{key}')
                            fill_val = func(Autogenerate(self, position + [key]))
                            if fill_val is not None:
                                self.fill_key(position + [key], fill_val,
                                              return_dict)
                                if not isinstance(structure[key]['value'], dict):
                                    print(f'\n---\n{structure[key]["desc"]}\n')
                                    print(f'{key}: {utils.find_position(self.result_dict, position + [key])}')
                        elif structure[key]['special_case']['generated'] == \
                                'end':
                            self.generate_end.append(position + [key])
                        elif structure[key]['special_case']['generated'] == \
                                'fill':
                            self.fill_key(position + [key],
                                          structure[key]['value'], return_dict)
                            optionals.append(key)
                            desc.append(structure[key]['desc'])
                    elif 'value_unit' in structure[key]['special_case']:
                        if 'list' in structure[key]:
                            self.fill_key(
                                position + [key],
                                self.get_list_value_unit(key, structure),
                                return_dict)
                        else:
                            self.fill_key(
                                position + [key],
                                self.get_value_unit(structure), return_dict)
                    elif 'merge' in structure[key]['special_case']:
                        self.fill_key(
                            position + [key], self.parse_input_value(
                                key,
                                structure[key]['value'][structure[key][
                                    'special_case']['merge']]),
                            return_dict)
                    else:
                        self.parse_lists(structure[key], position + [key],
                                         indent + 1, return_dict,
                                         is_factor=is_factor)
                else:
                    self.parse_lists(structure[key], position + [key],
                                     indent+1, return_dict,
                                     is_factor=is_factor)
            else:
                if not ('special_case' in structure[key] and 'factor' in
                        structure[key]['special_case'] and
                        structure[key]['special_case']['factor']) or \
                        structure[key]['list']:
                    optionals.append(key)
                    desc.append(structure[key]['desc'])
        if len(optionals) > 0 and not self.mandatory_only:
            print(
                f'\nDo you want to add any of the following optional keys?'
                f' (1,...,{len(optionals)} or n)\n')
            self.print_option_list(optionals, desc)
            options = self.parse_input_list(optionals, True)
            if options:
                for option in options:
                    if 'special_case' in structure[option] and 'generated' in \
                            structure[option]['special_case'] and \
                            structure[option]['special_case']['generated'] != \
                            'fill':
                        if structure[option]['special_case']['generated'] == \
                                'now':
                            func = getattr(Autogenerate, f'get_{option}')
                            fill_val = func(
                                Autogenerate(self, position + [option]))
                            if fill_val is not None:
                                self.fill_key(position + [option], fill_val,
                                              return_dict)
                        elif structure[option]['special_case']['generated'] \
                                == 'end':
                            self.generate_end.append(position + [option])
                    else:
                        self.parse_lists(structure[option],
                                         position + [option], indent+1,
                                         return_dict, is_factor=is_factor)

    def fill_key(self, position, value, fill_dict):
        if len(position) > 0:
            if len(position) == 1:
                fill_dict[position[0]] = value
            else:
                if type(position[1]) == str:
                    if type(position[0]) == str and position[0] not in \
                            fill_dict:
                        fill_dict[position[0]] = {}
                else:
                    if position[0] not in fill_dict:
                        fill_dict[position[0]] = []
                    if len(fill_dict[position[0]]) < position[1]+1:
                        for i in range(len(fill_dict[position[0]]),
                                       position[1]+1):
                            fill_dict[position[0]].append({})
                self.fill_key(position[1:], value, fill_dict[position[0]])
        else:
            print('NO POSITION')
