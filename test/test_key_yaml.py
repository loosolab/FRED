import os
import sys
import yaml.parser
import yaml.scanner

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import src.utils as utils

#TODO: test special_case

def test_key_yaml(all_keys, inner_keys):
    try:
        key_yaml = utils.read_in_yaml('keys.yaml')
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        print(f'The yaml file could not be parsed:\n{e}')
        sys.exit(1)

    for key in key_yaml:
        test_properties(key_yaml[key], key, all_keys, inner_keys)


def test_properties(part, key, all_keys, inner_keys):
    for prop in all_keys:
        if prop not in part:
            print(f'Property \'{prop}\' is missing for key \'{key}\'')
            sys.exit(1)
        else:
            error, prop_type = test_property_input(part[prop], prop, all_keys)
            if error:
                print(f'Wrong input \'{part[prop]}\' for property \'{prop}\' for key \'{key}\'. Input should be {prop_type}')
                sys.exit(1)

    if isinstance(part['value'], dict):
        for sub_key in part['value']:
            test_properties(part['value'][sub_key], f'{key}:{sub_key}', all_keys, inner_keys)
    else:
        test_for_inner_keys(part, key, inner_keys)


def test_for_inner_keys(part, key, inner_keys):
    for prop in inner_keys:
        if prop not in part:
            print(f'Property \'{prop}\' is missing for key \'{key}\'')
            sys.exit(1)
        else:
            error, prop_type = test_property_input(part[prop], prop, inner_keys)
            if error:
                print(
                    f'Wrong input \'{part[prop]}\' for property \'{prop}\' for key \'{key}\'. Input should be {prop_type}')
                sys.exit(1)


def test_property_input(prop_input, prop, keys):
    if keys[prop] == 'bool':
        if type(prop_input) != bool:
            return True, 'of type \'bool\''
    elif keys[prop] == 'str':
        if type(prop_input) != str:
            return True, 'of type \'str\''
    elif keys[prop] == 'int':
        if type(prop_input) != int:
            return True, 'of type \'int\''
    elif keys[prop] == 'value':
        if prop_input is not None and not isinstance(prop_input, dict) and type(prop_input) not in [str, bool, int]:
            return True, 'either a dictionary or a default value that can be \'None\' or of type \'str\', \'bool\' or \'int\''
    elif isinstance(keys[prop], list):
        if prop_input not in keys[prop]:
            return True, ', '.join(f'\'{x}\'' for x in keys[prop])
    return False, 'None'


if __name__ == "__main__":

    all_keys = {'mandatory': 'bool',
                'list': 'bool',
                'display_name': 'str',
                'desc': 'str',
                'value': 'value'}

    inner_keys = {'whitelist': 'bool',
                  'input_type': ['short_text', 'long_text', 'select', 'number', 'bool', 'date']}

    test_key_yaml(all_keys, inner_keys)

    sys.exit(0)