from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import argparse
import pathlib
from src import utils
import numpy as np
import json
import src.web_interface.factors_and_conditions as fc
import re

def get_data(path, keys_yaml):
    yaml = path
    keys = keys_yaml
    settings = list(utils.find_keys(yaml, 'experimental_setting'))
    setting_dict = {}
    annotated_dict = {}
    experimental_factors = {}
    organisms = {}

    options = [x for x in list(utils.find_keys(keys, 'samples'))[0]['value'].keys()if x not in ['sample_name', 'technical_replicates']]
    option_types = {}
    option_pretty = {}
    max_vals = {}
    for setting in settings[0]:
        df_dict = {}
        setting_id = setting['setting_id']
        organisms[setting_id] = setting['organism']['organism_name']
        experimental_factors[setting_id] = [x['factor'] for x in setting['experimental_factors']]

        conditions = list(utils.find_keys(setting, 'conditions'))[0]
        condition_names = []
        condition_index = []
        sample_names = []
        sample_index = []
        idx = []
        option_dict = {}
        annotated = {}
        c = 1
        j=1
        for cond in conditions:
            
            condition_name = cond['condition_name']
            samples = list(utils.find_keys(cond, 'samples'))[0]
            
            i = 1
            for sample in samples:
                
                condition_names.append(condition_name)
                condition_index.append(f'Condition {c}')
                sample_name = sample['sample_name']
                sample_index.append(f'Sample {i}')
                idx.append(j)
                j+=1
                i+=1
                sample_names.append(sample_name)

                for key in options:
                    if key not in option_dict:
                        option_dict[key] = []
                        annotated[key] = []
                    if key in sample:
                        if isinstance(sample[key], int) or isinstance(sample[key], float):
                            option_dict[key].append(sample[key])
                        elif (isinstance(sample[key], dict) and 'value' in sample[key] and 'unit' in sample[key]):
                            option_dict[key].append(sample[key])
                        else:
                            option_dict[key].append(str(sample[key]))
                        annotated[key].append('<br>'.join(annotate(sample[key])))
                    else:
                        option_dict[key].append(None)
                        annotated[key].append('')

            c+=1        
        df_dict = {'condition_name': condition_names,
                   'condition_index': condition_index,
                    'sample_name': sample_names,
                    'sample_index': sample_index,
                    'index': idx}
        
        for option in option_dict:
            option_structure = list(utils.find_keys(keys, option))[0]
            if option not in option_pretty:
                option_pretty[option] = option_structure['display_name']
            if 'input_type' in option_structure:
                option_types[option] = option_structure['input_type']
            elif 'special_case' in option_structure and 'value_unit' in option_structure['special_case']:
                option_types[option] = 'value_unit'
            else:
                option_types[option] = 'nested'
        
        max_options = max([len(set([str(y) for y in option_dict[x] if y is not None])) for x in option_dict.keys() if option_types[x] not in ['number', 'value_unit']])#, 'value_unit']]) 
        max_number = max([max([y for y in option_dict[x] if y is not None] + [1]) for x in option_dict.keys() if option_types[x] == 'number'])
        vu_values = {}
        for option in option_dict:
            if option_types[option] == 'value_unit':
                for i in range(len(option_dict[option])):
                    if option_dict[option][i] is not None:
                        if option_dict[option][i]['unit'] not in vu_values:
                            vu_values[option_dict[option][i]['unit']] = {}
                        if 'vals' not in vu_values[option_dict[option][i]['unit']]:
                            vu_values[option_dict[option][i]['unit']]['vals'] = []
                        vu_values[option_dict[option][i]['unit']]['vals'].append(option_dict[option][i]['value'])
        
        min_vu = 0.1
        max_vu = 1
        for unit in vu_values:
            vu_values[unit]['max'] = max_vu
            vu_values[unit]['min'] = min_vu
            min_vu += 1
            max_vu += 1
        
        for option in option_dict:
            option_num = []
            if option_types[option] == 'value_unit':
                option_values = [x for x in option_dict[option] if x is not None]
            else:
                option_values = list(set([x for x in option_dict[option] if x is not None]))
            if len(option_values) > 0:
                if option_types[option] == 'number':
                    num_vals = [normalize(x, 0, max_number, 0.1, 1) for x in option_values]
                else:
                    num_vals = list(np.linspace(1, len(option_values), len(option_values)))
                option_values = [str(x) for x in option_values]
            for value in option_dict[option]:
                if value is None:
                    option_num.append(value)
                elif option_types[option] == 'value_unit':
                    option_num.append(normalize(value['value'], 0, max(vu_values[value['unit']]['vals']), vu_values[value['unit']]['min'], vu_values[value['unit']]['max']))
                else:
                    option_num.append(num_vals[option_values.index(str(value))])

            df_dict[option] = option_dict[option]
            df_dict[f'{option}_num'] = option_num
        
        for option in option_dict:
            if option_types[option] == 'value_unit':
                for i in range(len(option_dict[option])):
                    if option_dict[option][i] is not None:
                        option_dict[option][i] = str(option_dict[option][i])

        df = pd.DataFrame(df_dict) 
        setting_dict[setting_id] = df
        annotated_dict[setting_id] = annotated
        max_vals[setting_id] = max_options
    return setting_dict, experimental_factors, organisms, max_vals, option_pretty, annotated_dict


def normalize(x, minIn, maxIn, minOut, maxOut):
    input = (x-minIn)/(maxIn-minIn)
    return minOut + input * (maxOut-minOut)

def annotate(value):
    annotated_value = []
    if isinstance(value, list):
        for elem in value:
            annotated_value += annotate(elem)
    elif isinstance(value, dict):
        if 'value' in value and 'unit' in value:
            annotated_value.append(f'{value["value"]}{value["unit"]}')
        else:
            for key in value:
                annotated_value += annotate(value[key])
    else:
        annotated_value.append(re.sub("0000(0)*", "...", str(value)))
    return list(set(annotated_value))