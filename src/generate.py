from src import utils
from src import validate_yaml
import datetime

project_id = ''
project_name = ''
pooled = False
sample_name = ''
factor = ''
fac_val = ''

def generate_file(input_id, name, mandatory_mode):
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
    elif key == factor:
        return fac_val
    elif key == 'pooled':
        return pooled
    elif key == 'sample_name':
        print(f'--------------------------------------------'
              f'Sample: {sample_name}'
              f'--------------------------------------------')
        return sample_name
    elif key == 'donor_count':
        if pooled:
            return(enter_information(node, key, return_dict, optional, mandatory_mode))
        else:
            return 1

    elif isinstance(node, dict):
        optionals = []
        for item in node:
            optional = False
            if item == 'conditions':
                return_dict[item] = get_conditions(return_dict['experimental_factors'], node[item][4])
            elif item == 'experimental_factors':
                return_dict[item] = get_experimental_factors()
            elif node[item][0] == 'mandatory':
                return_dict[item] = get_redo_value(node[item], item, optional, mandatory_mode)
            else:
                optionals.append(item)
        if len(optionals) > 0 and mandatory_mode==False:
            optional = True
            print_optionals = "\n".join([f"{i+1}: {optionals[i]}" for i in range(len(optionals))])
            print(f'Do you want to add any of the following optional keys? (1,...,{len(optionals)} or n)\n'
                  f'{print_optionals}')
            o = input()
            if o != 'n':
                options = [optionals[int(i.strip()) - 1] for i in o.split(',')]
                for option in options:
                    return_dict[option] = get_redo_value(node[option], option, optional, mandatory_mode)
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
            value.append(
                generate_part(node, item, {}, optional, mandatory_mode))
            print(f'Do you want to add another {item}? (y/n)')
            redo = True if input() == 'y' else False
    else:
        value = generate_part(node, item, {}, optional, mandatory_mode)
    return value

def get_experimental_factors():
    factor_list = utils.read_whitelist('factor')
    factors = '\n'.join([f'{i+1}: {factor_list[i]}' for i in range(len(factor_list))])
    print(f'Please select the analyzed experimental factors (1-{len(factor_list)}) divided by comma:\n'
          f'{factors}')
    used_factors = input()
    experimental_factors = []
    for i in used_factors.split(','):
        fac_val = {}
        fac_val['factor'] = factor_list[int(i.strip())-1]
        value_list = utils.read_whitelist(fac_val['factor'])
        values = '\n'.join([f'{i+1}: {value_list[i]}' for i in range(len(value_list))])
        print(
            f'Please select the values for experimental factor {fac_val["factor"]} (1-{len(value_list)}) divided by comma:\n'
            f'{values}')
        used_values = [value_list[int(i.strip())-1] for i in input().split(',')]
        fac_val['value'] = used_values
        experimental_factors.append(fac_val)
    return experimental_factors


def get_conditions(factors, node):
    combinations = get_condition_combinations(factors)
    print_combinations = '\n'.join([f'{i+1}: {combinations[i]}' for i in range(len(combinations))])
    print(f'Please select the analyzed combinations of experimental factors (1-{len(combinations)}) divided by comma:\n'
          f'{print_combinations}')
    used_combinations = [combinations[int(i.strip()) - 1] for i in input().split(',')]
    conditions = []
    for combi in used_combinations:
        replicates = get_replicates(combi, node)
        conditions.append(replicates)
    return conditions


def get_replicates(condition, node):
    replicates = {'condition_name': condition}
    print(f'Please enter the number of replicates for condition {condition}:')
    bio = int(input('biological replicates: '))
    tech = int(input('technical replicates: '))
    print(f'Are the samples pooled? (y/n)')
    input_pooled = True if input() == 'y' else False
    conditions = condition.split('-')

    if bio > 0:
        replicates['biological_replicates'] = {'count': bio}
        replicates['biological_replicates']['samples'] = []
        for i in range(1, bio+1):
            for cond in conditions:
                global sample_name
                sample_name = f'{condition}_{i}'
                key_val = cond.split(':')
                global pooled
                pooled= input_pooled
                global factor
                factor= key_val[0]
                global fac_val
                fac_val= key_val[1]
                samples = generate_part(node['biological_replicates'][4]['samples'][4], 'samples', {}, False, False)
            replicates['biological_replicates']['samples'].append(samples)
    if tech > 0:
        replicates['technical_replicates'] = {'count': tech}
        replicates['technical_replicates']['samples'] = []
        for i in range(bio+1, bio+tech+1):
            samples = {'sample_name': f'{condition}_{i}', 'pooled': pooled}
            for cond in conditions:
                key_val = cond.split(':')
                samples[key_val[0]] = key_val[1]
            replicates['technical_replicates']['samples'].append(samples)
    return replicates


def get_condition_combinations(factors):
    combinations = []
    for i in range(len(factors)):
        for value in factors[i]['value']:
            combinations.append(f'{factors[i]["factor"]}:{value}')
            for j in range(i+1,len(factors)):
                for value2 in factors[j]['value']:
                    combinations.append(f'{factors[i]["factor"]}:{value}-{factors[j]["factor"]}:{value2}')
    return combinations


def enter_information(node, key, return_dict, optional, mandatory_mode):
    if isinstance(node[4], dict):
        print(f'Please enter information about the {key}')
        return generate_part(node[4], key, return_dict, optional, mandatory_mode)
    else:
        return get_input(key, node[5], node[1], node[7])


def get_input(key, whitelist, bool_list, type):
    if bool_list:
        redo = True
        value = []
        while redo:
            value.append(user_input(key, whitelist, type))
            print(f'Do you want to add another {key}? (y/n)')
            redo = True if input() == 'y' else False
    else:
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