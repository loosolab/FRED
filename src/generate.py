import src.utils as utils
import src.validate_yaml as validate_yaml
import datetime

factor = []
not_editable = ['id', 'project_name', 'sample_name', 'pooled', 'donor_count']


# TODO test if file exists for ID
# TODO validation
# TODO save yaml file as id_metadata.yaml
def generate_file(input_id, name, mandatory_mode):
    """
    This function is used to generate metadata by calling functions to compute
    user input. It writes the metadata into a yaml file after validating it.
    :param input_id: the ID of the experiment
    :param name: the name of the experiment
    :param mandatory_mode: if True only mandatory files are filled out
    """

    key_yaml = utils.read_in_yaml('keys.yaml')
    result_dict = {'project': {'id': input_id, 'project_name': name}}

    for item in key_yaml:
        if item in result_dict:
            result_dict[item] = {**result_dict[item],
                                 **get_redo_value(key_yaml[item], item, False,
                                                  mandatory_mode)}
        else:
            result_dict[item] = get_redo_value(key_yaml[item], item, False,
                                               mandatory_mode)
    #valid, missing_mandatory_keys, invalid_keys, \
    #invalid_entries = validate_yaml.validate_file(result_dict)
    #if not valid:
    #    validate_yaml.print_validation_report(
    #        result_dict, missing_mandatory_keys, invalid_keys,
    #        invalid_entries)
    utils.save_as_yaml(result_dict, f'{input_id}_metadata.yaml')


def generate_part(node, key, return_dict, optional, mandatory_mode):
    if isinstance(node, dict):
        optionals = []
        for item in node:
            optional = False
            if item == 'conditions':
                return_dict[item] = get_conditions(
                    return_dict['experimental_factors'], node[item][4],
                    mandatory_mode)
            elif item == 'experimental_factors':
                return_dict[item] = get_experimental_factors(node)
            elif item not in not_editable:
                if node[item][0] == 'mandatory':
                    return_dict[item] = get_redo_value(node[item], item,
                                                       optional,
                                                       mandatory_mode)
                else:
                    if item not in factor:
                        optionals.append(item)
        if len(optionals) > 0 and mandatory_mode == False:
            optional = True
            print(
                f'Do you want to add any of the following optional keys? '
                f'(1,...,{len(optionals)} or n)\n')
            print_option_list(optionals)
            options = parse_input_list(optionals, True)
            if options:
                for option in options:
                    return_dict[option] = get_redo_value(node[option], option,
                                                         optional,
                                                         mandatory_mode)
    else:
        if node[0] == 'mandatory' or optional:
            value = enter_information(node, key, return_dict, optional,
                                      mandatory_mode)
            return value
    return return_dict


def print_option_list(options):
    print_options = "\n".join(
                [f"{i + 1}: {options[i]}" for i in range(len(options))])
    print(f'{print_options}')


def parse_input_list(options, terminable):
    input_list = input()
    if terminable and input_list.lower() == 'n':
        return None
    else:
        if isinstance(options, list):
            try:
                input_list = [options[int(i.strip())-1] for i in
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


def get_redo_value(node, item, optional, mandatory_mode):
    if node[1]:
        redo = True
        value = []
        while redo:
            value.append(
                generate_part(node, item, {}, optional, mandatory_mode))
            print(f'Do you want to add another {item}?')
            print_option_list(['Yes', 'No'])
            redo = parse_list_choose_one([True, False])
    else:
        value = generate_part(node, item, {}, optional, mandatory_mode)
    return value


def get_experimental_factors(node):
    factor_list = utils.read_whitelist('factor')
    print(
        f'Please select the analyzed experimental factors '
        f'(1-{len(factor_list)}) divided by comma:\n')
    print_option_list(factor_list)
    used_factors = parse_input_list(factor_list, False)

    experimental_factors = []
    for fac in used_factors:
        factor_value = {'factor': fac}
        fac_node = list(utils.find_keys(node, fac))[0]
        if fac_node[5]:
            value_list = utils.read_whitelist(fac)
            print(
                f'Please select the values for experimental factor '
                f'{factor_value["factor"]} (1-{len(value_list)}) divided by '
                f'comma:\n')
            print_option_list(value_list)
            used_values = parse_input_list(value_list, False)
        else:
            value_type = fac_node[7]
            print(f'Please enter a list of {value_type} values divided by '
                  f'comma:\n')
            used_values = parse_input_list(value_type, False)
        factor_value['value'] = used_values
        experimental_factors.append(factor_value)

    global factor
    factor = used_factors
    return experimental_factors


def get_conditions(factors, node, mandatory_mode):
    combinations = get_condition_combinations(factors)
    print(
        f'Please select the analyzed combinations of experimental factors '
        f'(1-{len(combinations)}) divided by comma:\n')
    print_option_list(combinations)
    used_combinations = parse_input_list(combinations, False)
    conditions = get_replicate_count(used_combinations, node, mandatory_mode)
    return conditions


def get_replicate_count(conditions, node, mandatory_mode):
    condition_infos = []
    input_pooled = None
    for condition in conditions:
        print(f'{"".center(80, "_")}\n\n'
              f'{f"Condition: {condition}".center(80, " ")}\n'
              f'{"".center(80, "_")}\n\n'
              f'Please enter the number of replicates:')
        bio = parse_input_value('biological replicates', False, 'int')
        tech = parse_input_value('technical replicates', False, 'int')
        if bio > 0 or tech > 0:
            print(f'Are the samples pooled?')
            print_option_list(['Yes', 'No'])
            input_pooled = parse_list_choose_one([True, False])
        condition_infos.append(
            get_replicates(condition, bio, tech, input_pooled, node,
                           mandatory_mode))
    return condition_infos


def get_replicates(condition, bio, tech, input_pooled, node, mandatory_mode):
    replicates = {'condition_name': condition}

    if bio > 0:
        print(f'{"".center(80, "_")}\n\n'
              f'\033[1m{"Biological Replicates".center(80, " ")}\033[0m\n')
        replicates['biological_replicates'] = fill_replicates(
            'biological_replicates', condition, 1, bio + 1, input_pooled, node,
            mandatory_mode)

    if tech > 0:
        print(f'{"".center(80, "_")}\n\n'
              f'\033[1m{"Technical Replicates".center(80, " ")}\033[0m\n')
        replicates['technical_replicates'] = fill_replicates(
            'technical_replicates', condition, bio + 1, bio + tech + 1,
            input_pooled, node, mandatory_mode)
    return replicates


def fill_replicates(type, condition, start, end, input_pooled, node,
                    mandatory_mode):
    conditions = condition.split('-')
    replicates = {'count': end - start, 'samples': []}
    for i in range(start, end):
        samples = {}
        sample_name = f'{condition}_{i}'
        samples['sample_name'] = sample_name
        print(f'{f"Sample: {sample_name}".center(80, "-")}\n')
        samples['pooled'] = input_pooled
        if input_pooled:
            donor_count = parse_input_value('donor_count', False, 'int')
        else:
            donor_count = 1
        samples['donor_count'] = donor_count
        for cond in conditions:
            key_val = cond.split(':')
            samples[key_val[0]] = key_val[1]
        samples = {**samples,
                   **generate_part(node[type][4]['samples'][4], 'samples', {},
                                   False, mandatory_mode)}
        replicates['samples'].append(samples)
    return replicates


def get_condition_combinations(factors):
    """
    This function returns all possible combinations for experimental factors
    :param factors: multiple dictionaries containing the keys 'factor' and
                    'value' with their respective values grouped in a list
    :return: a list containing all combinations of conditions
    """
    combinations = []
    for i in range(len(factors)):
        for value in factors[i]['value']:
            combinations.append(f'{factors[i]["factor"]}:{value}')
            for j in range(i + 1, len(factors)):
                comb = get_condition_combinations(factors[j:])
                for c in comb:
                    combinations.append(f'{factors[i]["factor"]}:{value}-{c}')
    return combinations


def enter_information(node, key, return_dict, optional, mandatory_mode):
    if isinstance(node[4], dict):
        print(f'Please enter information about the {key}')
        return generate_part(node[4], key, return_dict, optional,
                             mandatory_mode)
    else:
        return parse_input_value(key, node[5], node[7])


def parse_list_choose_one(whitelist):
    try:
        value = whitelist[int(input())-1]
    except (IndexError, ValueError) as e:
        print(f'Invalid entry. Please enter a number between 1 and '
              f'{len(whitelist)}')
        value = parse_list_choose_one(whitelist)
    return value


def parse_input_value(key, whitelist, value_type):
    whites = None
    if whitelist:
        whites = utils.read_whitelist(key)
    if whites:
        print_option_list(whites)
        input_value = parse_list_choose_one(whites)
    else:
        input_value = input(f'{key}: ')
        if input_value == '':
            print(f'Please enter something.')
            input_value = parse_input_value(key, whitelist, value_type)
        if value_type == 'int':
            try:
                input_value = int(input_value)
            except ValueError:
                print(f'Input must be of type int. Try again.')
                input_value = parse_input_value(key, whitelist, value_type)
        elif value_type == 'float':
            try:
                input_value = float(input_value)
            except ValueError:
                print(f'Input must be of type float. Try again.')
                input_value = parse_input_value(key, whitelist, value_type)
        elif value_type == 'date':
            try:
                input_date = input_value.split('.')
                if len(input_date) != 3:
                    raise SyntaxError
                input_value = datetime.date(int(input_date[2]),
                                            int(input_date[1]),
                                            int(input_date[0]))
                input_value = input_value.strftime("%d.%m.%Y")
            except (IndexError, ValueError, SyntaxError) as e:
                print(f'Input must be of type \'DD.MM.YYYY\'.')
                input_value = parse_input_value(key, whitelist, value_type)
    return input_value