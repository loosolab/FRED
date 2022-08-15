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
        results = [x for x in self.whitelist if re.search(text, x, re.IGNORECASE) is not None] + [None]
        if len(results) > 30:
            results = results[:30]
        return results[state]


def generate_file(path, input_id, name, mandatory_mode):
    """
    This function is used to generate metadata by calling functions to compute
    user input. It writes the metadata into a yaml file after validating it.
    :param input_id: the ID of the experiment
    :param name: the name of the experiment
    :param mandatory_mode: if True only mandatory files are filled out
    """

    if os.path.exists(
            os.path.join(path, f'{input_id}_metadata.yaml')) or os.path.exists(
        os.path.join(path, f'{input_id}_metadata.yml')):
        sys.exit(
            f'The metadata file for ID {input_id} already exists.')

    global id
    id = input_id
    key_yaml = utils.read_in_yaml('keys.yaml')
    result_dict = {'project': {'id': input_id, 'project_name': name}}

    for item in key_yaml:
        if item in result_dict:
            result_dict[item] = {**result_dict[item],
                                 **get_redo_value(key_yaml[item], item, False,
                                                  mandatory_mode, result_dict, True)}
        else:
            result_dict[item] = get_redo_value(key_yaml[item], item, False,
                                               mandatory_mode, result_dict, True)

    print(f'{"".center(size.columns, "-")}\n'
          f'{"SUMMARY".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    print_summary(result_dict, '')
    print(f'\n\n')
    print(f'{"".center(size.columns, "-")}\n')

    print(f'{"".center(size.columns, "-")}\n'
          f'{"FILE VALIDATION".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    valid, missing_mandatory_keys, invalid_keys, \
    invalid_entries, invalid_values, pool_warn, ref_genome_warn = validate_yaml.validate_file(result_dict)
    if not valid:
        validate_yaml.print_validation_report(
            result_dict, missing_mandatory_keys, invalid_keys,
            invalid_entries, invalid_values)
    else:
        print(f'Validation complete. No errors found.\n')

        utils.save_as_yaml(result_dict,
                           os.path.join(path, f'{input_id}_metadata.yaml'))
    print_sample_names(result_dict, input_id, path)

def print_summary(result, pre):
    if isinstance(result, dict):
        print(f'{pre}')
        tabs = '\t' * pre.count('\t')
        for key in result:
            print_summary(result[key], f'\t{tabs}{key}: ')
    elif isinstance(result, list):
        print(f'{pre}')
        tabs = '\t' * pre.count('\t')
        for item in result:
            if isinstance(item, dict):
                print_summary(item, f'{tabs}')
            else:
                print_summary(item, f'{tabs}\t-')
    else:
        print(f'{pre}{result}')


def print_sample_names(result, input_id, path):
    samples = list(utils.find_list_key(result, 'technical_replicates:sample_name'))
    print(f'{"".center(size.columns, "-")}\n'
          f'{"SAMPLE NAMES".center(size.columns, " ")}\n'
          f'{"".center(size.columns, "-")}\n')
    sample_names = ''
    for elem in samples:
        for name in elem:
            sample_names += f'- {name}\n'
    print(sample_names)
    save = parse_list_choose_one([True, False], 'Do you want to save the sample names into a file?')
    if save:
        text_file = open(os.path.join(path, f'{input_id}_samples.txt'), 'w')
        text_file.write(sample_names)
        text_file.close()
        print(f'The sample names have been saved to file \'{path}/{input_id}_samples.txt\'.')


def generate_part(node, key, return_dict, optional, mandatory_mode,
                  result_dict, first_node):
    if isinstance(node, dict):
        if len(node.keys()) == 2 and 'value' in node.keys() and 'unit' in node.keys():
            value_unit = {
                'unit': parse_input_value('unit', '', True, str, result_dict),
                'value': parse_input_value('value', '', False, int,
                                           result_dict)}
            return value_unit
        else:
            optionals = []
            desc = []
            for item in node:
                optional = False
                if item == 'conditions':
                    return_dict[item] = get_conditions(
                        return_dict['experimental_factors'], node[item][4],
                        mandatory_mode, return_dict)
                elif item == 'experimental_factors':
                    return_dict[item] = get_experimental_factors(node,
                                                                 return_dict)
                elif item not in not_editable:
                    if node[item][0] == 'mandatory':
                        return_dict[item] = get_redo_value(node[item], item,
                                                           optional,
                                                           mandatory_mode,
                                                           return_dict, False)
                    else:
                        if node[item][1] or item not in factor:
                            optionals.append(item)
                            desc.append(node[item][3])
            if len(optionals) > 0 and mandatory_mode == False:
                optional = True
                print(
                    f'\nDo you want to add any of the following optional keys? '
                    f'(1,...,{len(optionals)} or n)')
                print_option_list(optionals, desc)
                options = parse_input_list(optionals, True)
                if options:
                    for option in options:
                        new_element = True
                        if node[option][2]:
                            if option in return_dict and all(isinstance(x, dict) for x in return_dict[option]):
                                new_element = False
                                key_yaml = utils.read_in_yaml('keys.yaml')
                                possible_keys = list(list(utils.find_keys(key_yaml, option))[0][4].keys())
                                elems = []
                                desc = []
                                for i in range(len(return_dict[option])):
                                    if not all(k in return_dict[option][i] for k in possible_keys):
                                        elems.append('\n'.join([f'{k}: {return_dict[option][i][k]}' for k in return_dict[option][i]]))
                                        desc.append(f'Possible information to add: {", ".join([x for x in possible_keys if x not in return_dict[option][i]])}')
                                if len(elems) > 0:
                                    elems.append(f'Add new {option}')
                                    desc.append('')
                                    print(f'\nThere are existing elements for {option}. Please select the elements for which you want to add information.\n')
                                    print_option_list(elems, desc)
                                    list_elems = parse_input_list(range(len(return_dict[option])+1), False)
                                    for indc in list_elems:
                                        if int(indc)-1 < len(return_dict[option]):
                                            caption = elems[int(indc)-1].replace("\n", ", ")
                                            print(f'\n'
                                                  f'{"".center(size.columns, "_")}\n\n'
                                                  f'{f"List element: {caption}".center(size.columns, " ")}\n'
                                                  f'{"".center(size.columns, "_")}\n')
                                            possible_input = [x for x in possible_keys if x not in list(return_dict[option][int(indc)-1].keys())]
                                            if len(possible_input) > 1:
                                                part_node = copy.deepcopy(node[option])
                                                remove_keys = []
                                                for k in part_node[4]:
                                                    if k not in possible_input:
                                                        remove_keys.append(k)
                                                for k in remove_keys:
                                                    part_node[4].pop(k)
                                                val = generate_part(part_node, option, {}, optional, mandatory_mode, result_dict, False)
                                                return_dict[option][int(indc)-1] = merge_dicts(return_dict[option][int(indc)-1], val)
                                            else:
                                                part_node = list(utils.find_keys(key_yaml, possible_input[0]))[0]
                                                val = get_redo_value(part_node, possible_input[0], optional, mandatory_mode, result_dict, False)
                                                return_dict[option][int(indc)-1][possible_input[0]] = val
                                        else:
                                            print(f'\n'
                                                  f'{"".center(size.columns, "_")}\n\n'
                                                  f'{f"New {option}".center(size.columns, " ")}\n'
                                                  f'{"".center(size.columns, "_")}\n')
                                            new_element = True
                                else:
                                    new_element = True

                        if new_element:
                            if len(node[option]) > 5 and isinstance(node[option][5],dict) and list(node[option][5].keys())[0] == 'merge':
                                value = parse_input_value(option, node[option][3], True, 'str', result_dict)
                                return value
                            else:
                                print(node[option])
                                val = get_redo_value(node[option],
                                                             option,
                                                             optional,
                                                             mandatory_mode,
                                                             result_dict, False)
                                if node[option][2]:
                                    if option in return_dict:
                                        return_dict[option] += val
                                    else:
                                        return_dict[option] = val
                                else:
                                    return_dict[option] = val
    else:
        if node[0] == 'mandatory' or optional:
            value = enter_information(node, key, return_dict, optional,
                                      mandatory_mode, result_dict, first_node)
            return value
    return return_dict


def print_option_list(options, desc):
    data = [[f'{i+1}:', f'{options[i]}', desc[i] if desc else ''] for i in range(len(options))]
    print(tabulate(data, tablefmt='plain', maxcolwidths=[size.columns*1/8, size.columns*2/8, size.columns*5/8]))


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
                if options == 'int':
                    for i in range(len(input_list)):
                        input_list[i] = int(input_list[i])
                elif options == 'float':
                    for i in range(len(input_list)):
                        input_list[i] = float(input_list[i])
            except (ValueError, IndexError) as e:
                print(f'Invalid entry. Please enter {options} numbers divided '
                      f'by comma.')
                input_list = parse_input_list(options, terminable)
    return input_list


def get_redo_value(node, item, optional, mandatory_mode, result_dict, first_node):
    if node[1]:
        redo = True
        value = []
        while redo:
            value.append(
                generate_part(node, item, {}, optional, mandatory_mode,
                              result_dict, first_node))
            redo = parse_list_choose_one([True, False],
                                         f'\nDo you want to add another {item}?')
    else:
        value = generate_part(node, item, {}, optional, mandatory_mode,
                              result_dict, first_node)
    return value


def get_experimental_factors(node, result_dict):
    factor_list = utils.get_whitelist('factor', result_dict)
    print(
        f'\nPlease select the analyzed experimental factors '
        f'(1-{len(factor_list)}) divided by comma:\n')
    print_option_list(factor_list, False)
    used_factors = parse_input_list(factor_list, False)

    experimental_factors = []
    for fac in used_factors:
        factor_value = {'factor': fac}
        fac_node = list(utils.find_keys(node, fac))[0]
        if isinstance(fac_node[4], dict):
            if 'unit' in fac_node[4] and 'value' in fac_node[4]:
                used_values = []
                print(f'\nPlease enter the unit for factor {fac}:')
                unit = parse_input_value('unit', '', True, 'str', result_dict)
                print(f'\nPlease enter int values for factor {fac} (in {unit}) '
                      f'divided by comma:')
                values = parse_input_list('int', False)
                for val in values:
                    used_values.append({'unit': unit, 'value': val})
            else:
                used_values = {}
                options = []
                values = []
                for key in fac_node[4]:
                    if fac_node[4][key][0] == 'mandatory':
                        values.append(key)
                    else:
                        options.append(key)
                if len(fac_node) > 5 and isinstance(fac_node[5], dict) and list(fac_node[5].keys())[0] == 'merge':
                    whitelist = utils.get_whitelist(fac, result_dict)
                    u_values = []
                    value_list = whitelist['whitelist']
                    values = []
                    if isinstance(value_list, dict):
                        w = [x for xs in list(value_list.values()) for x in xs]
                        if len(w) > 30:
                            redo = True
                            print(
                                f'\nPlease enter the values for experimental factor '
                                f'{factor_value["factor"]}.')
                            while redo:
                                input_value = complete_input(w, factor_value[
                                    "factor"])
                                if input_value in value_list:
                                    values.append(input_value)
                                    redo = parse_list_choose_one([True, False],
                                                                 f'\nDo you want to add another {factor_value["factor"]}?')
                                else:
                                    print(
                                        f'The value you entered does not match the '
                                        f'whitelist. Try tab for autocomplete.')
                        else:
                            print(
                                f'\nPlease select the values for experimental factor '
                                f'{factor_value["factor"]} (1-{len(w)}) divided by '
                                f'comma:\n')
                            i = 1
                            for w_key in value_list:
                                print(f'\033[1m{w_key}\033[0m')
                                for value in value_list[w_key]:
                                    print(f'{i}: {value}')
                                    i += 1
                            values = parse_input_list(w, False)
                    elif len(value_list) > 30:
                        redo = True
                        print(
                            f'\nPlease enter the values for experimental factor '
                            f'{factor_value["factor"]}.')
                        while redo:
                            input_value = complete_input(value_list,
                                                         factor_value[
                                                             "factor"])
                            if input_value in value_list:
                                values.append(input_value)
                                redo = parse_list_choose_one([True, False],
                                                             f'\nDo you want to add another {factor_value["factor"]}?')
                            else:
                                print(
                                    f'The value you entered does not match the '
                                    f'whitelist. Try tab for autocomplete.')
                    else:
                        print(
                            f'\nPlease select the values for experimental factor '
                            f'{factor_value["factor"]} (1-{len(value_list)}) divided by '
                            f'comma:\n')
                        print_option_list(value_list, False)
                        values = parse_input_list(value_list, False)
                    if 'headers' in whitelist:
                        headers = whitelist['headers'].split(' ')
                        for i in range(len(values)):
                            vals = values[i].split(' ')
                            values[i] = '{'
                            for j in range(len(headers)):
                                values[i] = f'{values[i]}{"|" if j > 0 else ""}{headers[j]}:\"{vals[j]}\"'
                            values[i] = f'{values[i]}{"}"}'
                            u_values.append(f'{fac}:{values[i]}')
                    used_values = u_values
                else:
                    for value in values:
                        if isinstance(fac_node[4][value][4],dict) and 'unit' in fac_node[4][value][4] and 'value' in fac_node[4][value][4]:
                            used_values[value] = []
                            print(f'\nPlease enter the unit for factor {fac}:')
                            unit = parse_input_value('unit', '', True, 'str',
                                                 result_dict)
                            print(
                                f'\nPlease enter int values for factor {fac} (in {unit}) '
                                f'divided by comma:')
                            values = parse_input_list('int', False)
                            for val in values:
                                used_values[value].append({'unit': unit, 'value': val})
                        else:
                            value_list = utils.get_whitelist(value, result_dict)
                            if isinstance(value_list, dict):
                                w = [x for xs in list(value_list.values()) for x in xs]
                                if len(w) > 30:
                                    redo = True
                                    print(
                                    f'\nPlease enter the values for '
                                    f'{value}.')
                                    while redo:
                                        input_value = complete_input(w, value)
                                        if input_value in value_list:
                                            used_values[value] = input_value
                                            redo = parse_list_choose_one([True, False],
                                                         f'\nDo you want to add another {factor_value["factor"]}?')
                                        else:
                                            print(f'The value you entered does not match the '
                                            f'whitelist. Try tab for autocomplete.')
                                else:
                                    print(
                                        f'\nPlease select the values for '
                                        f'{value} (1-{len(w)}) divided by '
                                        f'comma:\n')
                                    i = 1
                                    for w_key in value_list:
                                        print(f'\033[1m{w_key}\033[0m')
                                        for val in value_list[w_key]:
                                            print(f'{i}: {val}')
                                            i += 1
                                    used_values[value] = parse_input_list(w, False)
                            elif len(value_list) > 30:
                                redo = True
                                print(
                                    f'\nPlease enter the values for '
                                    f'{value}.')
                                while redo:
                                    input_value = complete_input(value_list, factor_value["factor"])
                                    if input_value in value_list:
                                        used_values[value] = input_value
                                        redo = parse_list_choose_one([True, False],
                                             f'\nDo you want to add another {value}?')
                                    else:
                                        print(f'The value you entered does not match the '
                                        f'whitelist. Try tab for autocomplete.')
                            else:
                                print(
                                    f'\nPlease select the values for '
                                    f'{value} (1-{len(value_list)}) divided by '
                                    f'comma:\n')
                                print_option_list(value_list, False)
                                used_values[value] = parse_input_list(value_list, False)
                        if len(fac_node) == 6:
                            used_values['ident_key'] = fac_node[5]

                    if len(options) > 0:
                        print(
                            f'\nDo you want to add any of the following optional keys '
                            f'(1,...,{len(options)} or n)?')
                        print_option_list(options, fac_node[3])
                        val = parse_input_list(options, True)
                        if val:
                            for value in val:
                                if isinstance(fac_node[4][value][4],dict) and 'unit' in fac_node[4][value][4] and 'value' in fac_node[4][value][4]:
                                    used_values[value] = []
                                    print(f'\nPlease enter the unit for factor {fac}:')
                                    unit = parse_input_value('unit', '', True, 'str',
                                                         result_dict)
                                    print(
                                        f'\nPlease enter int values for factor {fac} (in {unit}) '
                                        f'divided by comma:')
                                    values = parse_input_list('int', False)
                                    for val in values:
                                        used_values[value].append({'unit': unit, 'value': val})
                                else:
                                    value_list = utils.get_whitelist(value, result_dict)
                                    if isinstance(value_list, dict):
                                        w = [x for xs in list(value_list.values()) for x in xs]
                                        if len(w) > 30:
                                            redo = True
                                            print(
                                            f'\nPlease enter the values for '
                                            f'{value}.')
                                            while redo:
                                                input_value = complete_input(w, value)
                                                if input_value in value_list:
                                                    used_values[value] = input_value
                                                    redo = parse_list_choose_one([True, False],
                                                                 f'\nDo you want to add another {factor_value["factor"]}?')
                                                else:
                                                    print(f'The value you entered does not match the '
                                                    f'whitelist. Try tab for autocomplete.')
                                        else:
                                            print(
                                                f'\nPlease select the values for '
                                                f'{value} (1-{len(w)}) divided by '
                                                f'comma:\n')
                                            i = 1
                                            for w_key in value_list:
                                                print(f'\033[1m{w_key}\033[0m')
                                                for val in value_list[w_key]:
                                                    print(f'{i}: {val}')
                                                    i += 1
                                            used_values[value] = parse_input_list(w, False)
                                    elif len(value_list) > 30:
                                        redo = True
                                        print(
                                            f'\nPlease enter the values for '
                                            f'{value}.')
                                        while redo:
                                            input_value = complete_input(value_list, factor_value["factor"])
                                            if input_value in value_list:
                                                used_values[value] = input_value
                                                redo = parse_list_choose_one([True, False],
                                                     f'\nDo you want to add another {value}?')
                                            else:
                                                print(f'The value you entered does not match the '
                                                f'whitelist. Try tab for autocomplete.')
                                    else:
                                        print(
                                            f'\nPlease select the values for '
                                            f'{value} (1-{len(value_list)}) divided by '
                                            f'comma:\n')
                                        print_option_list(value_list, False)
                                        used_values[value] = parse_input_list(value_list, False)
                                if len(fac_node) == 6:
                                    used_values['ident_key'] = fac_node[5]
        elif fac_node[5]:
            value_list = utils.get_whitelist(fac, result_dict)
            used_values = []
            if isinstance(value_list, dict):
                w = [x for xs in list(value_list.values()) for x in xs]
                if len(w) > 30:
                    redo = True
                    print(
                        f'\nPlease enter the values for experimental factor '
                        f'{factor_value["factor"]}.')
                    while redo:
                        input_value = complete_input(w, factor_value["factor"])
                        if input_value in value_list:
                            used_values.append(input_value)
                            redo = parse_list_choose_one([True, False],
                                                         f'\nDo you want to add another {factor_value["factor"]}?')
                        else:
                            print(f'The value you entered does not match the '
                                  f'whitelist. Try tab for autocomplete.')
                else:
                    print(
                        f'\nPlease select the values for experimental factor '
                        f'{factor_value["factor"]} (1-{len(w)}) divided by '
                        f'comma:\n')
                    i = 1
                    for w_key in value_list:
                        print(f'\033[1m{w_key}\033[0m')
                        for value in value_list[w_key]:
                            print(f'{i}: {value}')
                            i += 1
                    used_values = parse_input_list(w, False)
            elif len(value_list) > 30:
                redo = True
                print(
                    f'\nPlease enter the values for experimental factor '
                    f'{factor_value["factor"]}.')
                while redo:
                    input_value = complete_input(value_list, factor_value["factor"])
                    if input_value in value_list:
                        used_values.append(input_value)
                        redo = parse_list_choose_one([True, False],
                                         f'\nDo you want to add another {factor_value["factor"]}?')
                    else:
                        print(f'The value you entered does not match the '
                              f'whitelist. Try tab for autocomplete.')
            else:
                print(
                    f'\nPlease select the values for experimental factor '
                    f'{factor_value["factor"]} (1-{len(value_list)}) divided by '
                    f'comma:\n')
                print_option_list(value_list, False)
                used_values = parse_input_list(value_list, False)
        else:
            value_type = fac_node[7]
            print(
                f'\nPlease enter a list of {value_type} values for experimental'
                f' factor {factor_value["factor"]} divided by comma:\n')
            used_values = parse_input_list(value_type, False)

        if isinstance(used_values, dict):
            used_values = get_combinations(used_values, fac, fac_node[2])

        factor_value['values'] = used_values
        experimental_factors.append(factor_value)

    global factor
    factor = used_factors
    return experimental_factors


def get_combinations(values, key, key_name):
    if 'ident_key' in values:
        if values['ident_key'] in values and len(values[values['ident_key']])>1:
            multi = parse_list_choose_one([True, False], f'\nCan one sample contain multiple {key_name}s?')
        else:
            multi = False
            values.pop('ident_key')
    else:
        multi = False
    merge_values = get_combis(values, key, multi)
    print(
        f'\nPlease select the analyzed combinations for {key} '
        f'(1-{len(merge_values)}) divided by comma:\n')
    print_option_list(merge_values, False)
    used_values = parse_input_list(merge_values, False)
    return used_values


def get_combis(values, key, multi):
    if 'multi' in values:
        values.pop('multi')
    if 'ident_key' in values and values['ident_key'] is None:
        values.pop('ident_key')
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
                        if isinstance(v,
                                  dict) and 'value' in v and 'unit' in v:
                            v = f'{v["value"]}{v["unit"]}'
                        value2.append(f'{val}|{list(values.keys())[i]}:"{v}"')
                value = value2
            possible_values[elem] = value
            for z in possible_values:
                if z != elem:
                    for x in possible_values[elem]:
                        for y in possible_values[z]:
                            disease_values.append(f'{key}:{"{"}{x}{"}"}-{key}:{"{"}{y}{"}"}')

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
                            if isinstance(x,
                                          dict) and 'value' in x and 'unit' in x:
                                v2.append(f'{i}|{k}:\"{x["value"]}{x["unit"]}\"')
                            else:
                                v2.append(f'{i}|{k}:\"{x}\"')
                    v = v2
            possible_values = v
            for z in possible_values:
                disease_values.append(f'{key}:{"{"}{z}{"}"}')
    return disease_values


def get_conditions(factors, node, mandatory_mode, result_dict):
    combi = True
    combinations = get_condition_combinations(factors)
    if len(factors) == 1 and combinations == factors[0]['values']:
        combi = False
        used_combinations = combinations
    for fac in factors:
        if fac['factor'] in ['disease', 'treatment', 'gene']:
            vals = []
            for cond in fac['values']:
                val = ([x[1] for x in split_cond(cond)])
                for y in val:
                    vals.append(y)
            vals = [dict(t) for t in {tuple(d.items()) for d in vals}]
            for elem in vals:
                for key in elem:
                    if key == 'treatment_duration':
                        unit = elem[key].lstrip('0123456789')
                        value = elem[key][:len(elem[key]) - len(unit)]
                        elem[key] = {'unit': unit, 'value': int(value)}
            for i in range(len(result_dict['experimental_factors'])):
                if result_dict['experimental_factors'][i]['factor'] == fac['factor']:
                    result_dict['experimental_factors'][i]['values'] = vals

    if combi:
        print(
            f'\nPlease select the analyzed combinations of experimental factors '
            f'(1-{len(combinations)}) divided by comma:\n')
        print_option_list(combinations, False)
        used_combinations = parse_input_list(combinations, False)

    conditions = get_replicate_count(used_combinations, node, mandatory_mode,
                                     result_dict)
    return conditions


def get_replicate_count(conditions, node, mandatory_mode, result_dict):
    condition_infos = []
    input_pooled = None
    for condition in conditions:
        print(f'{"".center(size.columns, "_")}\n\n'
              f'{f"Condition: {condition}".center(size.columns, " ")}\n'
              f'{"".center(size.columns, "_")}\n\n'
              f'Please enter the number of biological replicates:')
        bio = parse_input_value('count', '', False, 'int',
                                result_dict)
        if bio > 0:
            input_pooled = parse_list_choose_one([True, False],
                                                 f'\nAre the samples pooled?')
        condition_infos.append(
            get_replicates(condition, bio, input_pooled, node,
                           mandatory_mode, result_dict))
    return condition_infos


def get_replicates(condition, bio, input_pooled, node, mandatory_mode,
                   result_dict):
    replicates = {'condition_name': condition}

    if bio > 0:
        print(f'{"".center(size.columns, "_")}\n\n'
              f'\033[1m{"Biological Replicates".center(size.columns, " ")}\033[0m\n')
        replicates['biological_replicates'] = fill_replicates(
            'biological_replicates', condition, 1, bio + 1, input_pooled, node,
            mandatory_mode, result_dict)
    return replicates


def fill_replicates(type, condition, start, end, input_pooled, node,
                    mandatory_mode, result_dict):
    conditions = split_cond(condition)
    organism = utils.get_whitelist(os.path.join('abbrev', 'organism_name'), result_dict)
    if result_dict['organism'] in organism:
        organism = organism[result_dict['organism']]
    replicates = {'count': end - start, 'samples': []}
    for i in range(start, end):
        samples = {}
        sample_name = f'{condition}_b{"{:02d}".format(i)}'
        short_name = f'{get_short_name(condition, result_dict)}_b{"{:02d}".format(i)}'
        samples['sample_name'] = short_name
        print(f'{f"Sample: {sample_name}".center(size.columns, "-")}\n')
        samples['pooled'] = input_pooled
        if input_pooled:
            donor_count = parse_input_value('donor_count', '', False, 'int',
                                            result_dict)
        else:
            donor_count = 1
        samples['donor_count'] = donor_count
        for cond in conditions:
            if cond[0] in ['age', 'time_point', 'duration']:
                unit = cond[1].lstrip('0123456789')
                value = cond[1][:len(cond[1]) - len(unit)]
                samples[cond[0]] = {'unit': unit, 'value': int(value)}
            else:
                # TODO : if is list
                if cond[0] in ['disease', 'treatment']:
                    for key in cond[1]:
                        if key == 'treatment_duration':
                            unit = cond[1][key].lstrip('0123456789')
                            value = cond[1][key][:len(cond[1][key]) - len(unit)]
                            cond[1][key] = {'unit': unit,
                                                'value': int(value)}
                    if cond[0] not in samples:
                        samples[cond[0]] = [cond[1]]
                    else:
                        samples[cond[0]].append(cond[1])
                else:
                    samples[cond[0]] = cond[1]

        samples = merge_dicts(samples, generate_part(node[type][4]['samples'][4],
                                            'samples', samples,
                                            False, mandatory_mode,
                                            result_dict, False))
        if not 'number_of_measurements' in samples:
            samples['number_of_measurements'] = 1
        samples['technical_replicates'] = get_technical_replicates(short_name, organism, samples['number_of_measurements'])
        replicates['samples'].append(samples)
    return replicates


def get_short_name(condition, result_dict):
    conds = split_cond(condition)
    whitelist = utils.get_whitelist(os.path.join('abbrev', 'factor'), result_dict)
    short_cond = []
    for c in conds:
        if whitelist and c[0] in whitelist:
            k = whitelist[c[0]]
        else:
            k = c[0]
        if isinstance(c[1], dict):
            cond_whitelist = utils.get_whitelist(os.path.join('abbrev', c[0]), result_dict)
            new_vals = {}
            for v in c[1]:
                if cond_whitelist and v in cond_whitelist:
                    val_whitelist = utils.get_whitelist(os.path.join('abbrev', v), result_dict)
                    if val_whitelist and c[1][v].lower() in val_whitelist:
                        new_vals[cond_whitelist[v]] = val_whitelist[c[1][v].lower()]
                    else:
                        new_vals[cond_whitelist[v]] = c[1][v]
            val = '+'.join([f'{x}.{new_vals[x].replace(" ", "")}' for x in list(new_vals.keys())])
            short_cond.append(f'{k}#{val}')
        else:
            val_whitelist = utils.get_whitelist(os.path.join('abbrev', c[0]), result_dict)
            if val_whitelist and c[1].lower() in val_whitelist:
                short_cond.append(f'{k}.{val_whitelist[c[1].lower()]}')
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
            start = i+1
        elif condition[i] == '|':
            sub_cond[sub_key] = value
            start = i+1
        elif condition[i] == '}':
            sub_cond[sub_key] = value
            conditions.append((key,sub_cond))
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
                start = i+1
        elif condition[i] == '-' and count % 2 == 0:
            if sub:
                sub = False
            else:
                conditions.append((key, value))
            start = i+1
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


def get_technical_replicates(sample_name, organism, nom):
    print(f'\nPlease enter the number of technical replicates:')
    count = parse_input_value('count', '', False, 'int', [])
    while count < 1:
        print(f'The number of technical replicates has to be at least 1.')
        count = parse_input_value('count', '', False, 'int', [])
    samples = []
    for i in range(count):
        for j in range(nom):
            samples.append(f'{id}_{organism}_{sample_name}_t{"{:02d}".format(i+1)}_m{"{:02d}".format(j+1)}')
    return {'count': count, 'sample_name': samples}


def get_condition_combinations(factors):
    """
    This function returns all possible combinations for experimental factors
    :param factors: multiple dictionaries containing the keys 'factor' and
                    'value' with their respective values grouped in a list
    :return: a list containing all combinations of conditions
    """
    combinations = []
    for i in range(len(factors)):
        for value in factors[i]['values']:
            if isinstance(value,
                          dict) and 'value' in value and 'unit' in value:
                value = f'{value["value"]}{value["unit"]}'
            if factors[i]['factor'] in ['disease', 'treatment', 'gene']:
                combinations.append(f'{value}')
            else:
                combinations.append(f'{factors[i]["factor"]}:"{value}"')
            for j in range(i + 1, len(factors)):
                comb = get_condition_combinations(factors[j:])
                for c in comb:
                    if factors[i]['factor'] in ['disease', 'treatment', 'gene']:
                        combinations.append(f'{value}-{c}')
                    else:
                        combinations.append(f'{factors[i]["factor"]}:"{value}"-{c}')
    return combinations


def enter_information(node, key, return_dict, optional, mandatory_mode,
                      result_dict, first_node):
    if isinstance(node[4], dict):
        if first_node:
            print(f'{"".center(size.columns, "_")}\n\n'
                  f'{f"{node[2]}".center(size.columns, " ")}\n'
                  f'{"".center(size.columns, "_")}\n')
        else:
            print(f'\n'
                  f'{"".center(size.columns, "-")}\n'
                  f'{f"{node[2]}".center(size.columns, " ")}\n'
                  f'{"".center(size.columns, "-")}\n')
        if node[3] != '':
            print(f'{node[3]}\n')
        return generate_part(node[4], key, return_dict, optional,
                             mandatory_mode, result_dict, False)
    else:
        return parse_input_value(key, node[3], node[5], node[7], result_dict)


def parse_list_choose_one(whitelist, header):
    try:
        print(f'{header}')
        print_option_list(whitelist, False)
        value = whitelist[int(input()) - 1]
    except (IndexError, ValueError) as e:
        print(f'Invalid entry. Please enter a number between 1 and '
              f'{len(whitelist)}')
        value = parse_list_choose_one(whitelist, header)
    return value


def parse_input_value(key, desc, whitelist, value_type, result_dict):
    whites = None
    whites2 = None
    if whitelist:
        whites = utils.get_whitelist(key, result_dict)
        whites2 = whites
        if isinstance(whites, dict) and 'whitelist' in whites:
            whites2 = whites['whitelist']
    if whites2:
        if isinstance(whites, dict):
            w = [x for xs in list(whites.values()) for x in xs]
            if len(w) > 30:
                input_value = complete_input(w, key)
                if input_value not in w:
                    print(f'The value you entered does not match the '
                          f'whitelist. Try tab for autocomplete.')
                    input_value = parse_input_value(key, desc, whitelist, value_type, result_dict)
            else:
                input_value = parse_group_choose_one(whites, w, f'{key}:')
        elif len(whites) > 30:
            input_value = complete_input(whites, key)
            if input_value not in whites:
                print(f'The value you entered does not match the '
                      f'whitelist. Try tab for autocomplete.')
                input_value = parse_input_value(key, desc, whitelist, value_type,
                                  result_dict)
        elif len(whites) > 0:
            input_value = parse_list_choose_one(whites, f'{key}:')
        if 'headers' in whites:
            headers = whites['headers'].split(' ')
            vals = input_value.split(' ')
            value = {}
            for i in range(len(headers)):
                value[headers[i]] = vals[i]
            input_value = {key: value}
    else:
        if desc != '':
            print(f'\n{desc}')
        if value_type == 'bool':
            input_value = parse_list_choose_one([True, False],
                                                f'Is the sample {key}')
        else:
            if desc == '':
                input_value = input(f'\n{key}: ')
            else:
                input_value = input(f'{key}: ')
            if input_value == '':
                print(f'Please enter something.')
                input_value = parse_input_value(key, desc, whitelist,
                                                value_type, result_dict)
            elif '\"' in input_value:
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
        if value_type == 'int':
            try:
                input_value = int(input_value)
            except ValueError:
                print(f'Input must be of type int. Try again.')
                input_value = parse_input_value(key, desc, whitelist,
                                                value_type,
                                                result_dict)
        elif value_type == 'float':
            try:
                input_value = float(input_value)
            except ValueError:
                print(f'Input must be of type float. Try again.')
                input_value = parse_input_value(key, desc, whitelist,
                                                value_type,
                                                result_dict)
        elif value_type == 'date':
            try:
                input_date = input_value.split('.')
                if len(input_date) != 3 or len(input_date[0]) != 2 or len(
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
    return input_value


def parse_group_choose_one(whitelist, w, header):
    try:
        print(f'{header}\n')
        i = 1
        for key in whitelist:
            print(f'\033[1m{key}\033[0m')
            for value in whitelist[key]:
                print(f'{i}: {value}')
                i += 1
        value = w[int(input()) - 1]
    except (IndexError, ValueError) as e:
        print(f'Invalid entry. Please enter a number between 1 and '
              f'{len(whitelist)}')
        value = parse_list_choose_one(whitelist, header)
    return value


def complete_input(whitelist, key):
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
