import src.utils as utils
from src import validate_yaml
import datetime

project_id = ''
project_name = ''
pooled = False
factor = []
not_editable = ['sample_name', 'pooled', 'donor_count']


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
    global project_id
    project_id = input_id
    global project_name
    project_name = name
    key_yaml = utils.read_in_yaml('keys.yaml')
    result_dict = {}

    for item in key_yaml:
        result_dict[item] = generate_part(key_yaml[item], item, {}, False, mandatory_mode)
    print(result_dict)


def generate_part(node, key, return_dict, optional, mandatory_mode):

    if key == 'id':
        return project_id
    elif key == 'project_name':
        return project_name
    #elif key == 'donor_count':
    #    if pooled:
    #        return(enter_information(node, key, return_dict, optional, mandatory_mode))
    #    else:
    #        return 1

    elif isinstance(node, dict):
        optionals = []
        for item in node:
            optional = False
            if item == 'conditions':
                return_dict[item] = get_conditions(return_dict['experimental_factors'], node[item][4], mandatory_mode)
            elif item == 'experimental_factors':
                return_dict[item] = get_experimental_factors()
            elif node[item][0] == 'mandatory' and item not in not_editable:
                return_dict[item] = get_redo_value(node[item], item, optional, mandatory_mode)
            else:
                if item not in factor and item not in not_editable:
                    optionals.append(item)
        if len(optionals) > 0 and mandatory_mode == False:
            optional = True
            print_optionals = "\n".join([f"{i+1}: {optionals[i]}" for i in range(len(optionals))])
            print(f'Do you want to add any of the following optional keys? (1,...,{len(optionals)} or n)\n'
                  f'{print_optionals}')
            o = input()
            if o != 'n':
                options = [optionals[int(i.strip()) - 1] for i in o.split(',')]
                for option in options:
                    return_dict[option] = get_redo_value(node[option], option, optional, mandatory_mode)
            print("I'm done!")
    else:
        if node[0] == 'mandatory' or optional:
            value = enter_information(node, key, return_dict, optional, mandatory_mode)
            return value
    return return_dict


def get_redo_value(node, item, optional, mandatory_mode):
    if node[1]:
        redo = True
        value = []
        while redo:
            print('I\'m on!')
            value.append(
                generate_part(node, item, {}, optional, mandatory_mode))
            print(f'Do you want to add another {item}? (y/n)')
            redo = True if input() == 'y' else False
    else:
        value = generate_part(node, item, {}, optional, mandatory_mode)
    return value

# TODO: test for input
def get_experimental_factors():
    factor_list = utils.read_whitelist('factor')
    factors = '\n'.join([f'{i+1}: {factor_list[i]}' for i in range(len(factor_list))])
    print(f'Please select the analyzed experimental factors (1-{len(factor_list)}) divided by comma:\n'
          f'{factors}')
    used_factors = input()
    experimental_factors = []
    for i in used_factors.split(','):
        factor_value = {'factor': factor_list[int(i.strip()) - 1]}
        value_list = utils.read_whitelist(factor_value['factor'])
        values = '\n'.join([f'{i+1}: {value_list[i]}' for i in range(len(value_list))])
        print(
            f'Please select the values for experimental factor {factor_value["factor"]} (1-{len(value_list)}) divided by comma:\n'
            f'{values}')
        used_values = [value_list[int(i.strip())-1] for i in input().split(',')]
        factor_value['value'] = used_values
        experimental_factors.append(factor_value)
    global factor
    factor = [x['factor'] for x in experimental_factors]
    return experimental_factors


def get_conditions(factors, node, mandatory_mode):
    combinations = get_condition_combinations(factors)
    print_combinations = '\n'.join([f'{i+1}: {combinations[i]}' for i in range(len(combinations))])
    print(f'Please select the analyzed combinations of experimental factors (1-{len(combinations)}) divided by comma:\n'
          f'{print_combinations}')
    used_combinations = [combinations[int(i.strip()) - 1] for i in input().split(',')]
    conditions = get_replicate_count(used_combinations, node, mandatory_mode)
    return conditions


def get_replicate_count(conditions, node, mandatory_mode):
    condition_infos = []
    input_pooled = None
    for condition in conditions:
        print(f'{"".center(80, "_")}\n\n'
              f'{f"Condition: {condition}".center(80, " ")}\n'
              f'{"".center(80, "_")}\n'
              f'Please enter the number of replicates:')
        bio = int(input('biological replicates: '))
        tech = int(input('technical replicates: '))
        if bio > 0 or tech > 0:
            print(f'Are the samples pooled? (y/n)')
            input_pooled = True if input() == 'y' else False
        condition_infos.append(get_replicates(condition, bio, tech, input_pooled, node, mandatory_mode))
    return condition_infos

# TODO: technical replicates
# TODO: test for input
# TODO: Node rau + extra Funktion für replicates
def get_replicates(condition, bio, tech, input_pooled, node, mandatory_mode):
    replicates = {'condition_name': condition}

    if bio > 0:
        print(f'{"".center(80,"_")}\n\n'
              f'\033[1m{"Biological Replicates".center(80," ")}\033[0m\n')
        replicates['biological_replicates'] = fill_replicates('biological_replicates', condition, 1, bio+1, input_pooled, node, mandatory_mode)

    if tech > 0:
        print(f'{"".center(80, "_")}\n\n'
              f'\033[1m{"Technical Replicates".center(80, " ")}\033[0m\n')
        replicates['technical_replicates'] = fill_replicates('technical_replicates', condition, bio+1, bio+tech+1, input_pooled, node, mandatory_mode)
    return replicates

def fill_replicates(type, condition, start, end, input_pooled, node, mandatory_mode):
    conditions = condition.split('-')
    replicates = {'count': end-start, 'samples': []}
    for i in range(start, end):
        samples = {}
        sample_name = f'{condition}_{i}'
        samples['sample_name'] = sample_name
        print(f'{f"Sample: {sample_name}".center(80, "-")}\n')
        samples['pooled'] = input_pooled
        if input_pooled:
            donor_count = input('donor_count:')
        else:
            donor_count = 1
        samples['donor_count'] = donor_count
        for cond in conditions:
            key_val = cond.split(':')
            samples[key_val[0]] = key_val[1]
        samples = {**samples, **generate_part(node[type][4]['samples'][4], 'samples', {}, False, mandatory_mode)}
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
            for j in range(i+1,len(factors)):
                comb = get_condition_combinations(factors[j:])
                for c in comb:
                    combinations.append(f'{factors[i]["factor"]}:{value}-{c}')
    return combinations


def enter_information(node, key, return_dict, optional, mandatory_mode):
    if isinstance(node[4], dict):
        print(f'Please enter information about the {key}')
        return generate_part(node[4], key, return_dict, optional, mandatory_mode)
    else:
        return get_input(key, node[5], node[1], node[7])


def get_input(key, whitelist, bool_list, type):
    value = user_input(key, whitelist, type)
    return value


def user_input(key, whitelist, type):
    whites = None
    if whitelist:
        whites = utils.read_whitelist(key)
    if whites:
        w_list = '\n'.join([f'{i+1}: {whites[i]}' for i in range(len(whites))])
        print(f'{key}:\n'
              f'{w_list}')
        value = whites[int(input())-1]
    else:
        value = input(f'{key}: ')
    value, invalid = test_for_value(value, type)
    if invalid:
        print(f'Invalid entry')
        value = user_input(key, whitelist, type)
    return value


def test_for_value(value, type):
    invalid = None
    if type == 'int':
        value = int(value)
    elif type == 'float':
        value = float(value)
    elif type == 'date':
        try:
            input_date = value.split('.')
            if len(input_date)!=3:
                raise SyntaxError
            value = datetime.date(int(input_date[2]),int(input_date[1]), int(input_date[0]))
            value = value.strftime("%d.%m.%Y")
        except IndexError and ValueError and SyntaxError:
            invalid = 'Invalid entry for date'
    return value, invalid