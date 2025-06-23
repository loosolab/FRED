import pandas as pd
from src import utils
import numpy as np
import re

def get_data(path, keys_yaml):

    setting_dict = {}
    annotated_dict = {}
    experimental_factors = {}
    organisms = {}
    option_types = {}
    option_pretty = {}
    max_vals = {}
    max_anno = {}

    yaml = path
    keys = keys_yaml
    settings = list(utils.find_keys(yaml, 'experimental_setting'))

    if len(settings) > 0:

        options = [x for x in list(utils.find_keys(keys, 'samples'))[0]['value'].keys()if x not in ['sample_name']]

        for setting_index, setting in enumerate(settings[0]):
            
            df_dict = {}
            max_annotation = {}

            try:
                setting_id = setting['setting_id']
            except KeyError:
                setting_id = f'setting_{setting_index}'
            
            try:
                organisms[setting_id] = setting['organism']['organism_name']
            except KeyError:
                organisms[setting_id] = None

            try:
                experimental_factors[setting_id] = [x['factor'] for x in setting['experimental_factors']]
            except KeyError:
                experimental_factors[setting_id] = None

            conditions = list(utils.find_keys(setting, 'conditions'))
            
            if len(conditions) > 0:
                
                conditions = conditions[0]
                condition_names = []
                condition_index = []
                sample_index = []
                idx = []
                option_dict = {}
                annotated = {}
                
                j=1
                
                for cond_index, cond in enumerate(conditions):
                
                    # TODO: only table?
                    condition_name = cond['condition_name']
                    
                    samples = list(utils.find_keys(cond, 'samples'))
                    
                    if len(samples) > 0:
                        samples = samples[0]
                
                        for samp_index, sample in enumerate(samples):
                            
                            condition_names.append(condition_name)
                            condition_index.append(f'Condition {cond_index+1}')
                            
                            sample_index.append(f'Sample {samp_index+1}')
                            idx.append(j)
                            j+=1

                            for key in options:

                                if key not in option_dict:
                                    option_dict[key] = []
                                    annotated[key] = []
                                
                                if key in sample:
                                    
                                    if key == 'technical_replicates':
                                        try:
                                            option_dict[key].append(sample[key]['count'])
                                            annotated[key].append(str(sample[key]['count']))
                                        except KeyError:
                                            option_dict[key].append(None)
                                            annotated[key].append('')
                                    
                                    else:

                                        if isinstance(sample[key], int) or isinstance(sample[key], float):
                                            option_dict[key].append(sample[key])
                                        
                                        elif (isinstance(sample[key], dict) and 'value' in sample[key] and 'unit' in sample[key]):
                                            option_dict[key].append(sample[key])
                                        
                                        else:
                                            option_dict[key].append(str(sample[key]))
                                        
                                        key_structure = list(utils.find_keys(keys, key))
                                        group_key = None
                                        if len(key_structure) > 0:
                                            try:
                                                group_key = list(key_structure[0]['special_case']['control'].keys())[0]
                                            except:
                                                group_key = None
                                        annotation = annotate(sample[key], group_key)
                                        if key in max_annotation:
                                            max_annotation[key] = max(max_annotation[key], len(annotation))
                                        else:
                                            max_annotation[key] = len(annotation)
                                        annotated[key].append('<br>'.join(annotation))
                                else:
                                    option_dict[key].append(None)
                                    annotated[key].append('')

                    df_dict = {'condition_name': condition_names,
                               'condition_index': condition_index,
                               'sample_index': sample_index,
                               'index': idx}
                    
                for option in option_dict:

                    option_structure = list(utils.find_keys(keys, option))
                        
                    if len(option_structure) > 0:
                        option_structure = option_structure[0]
                            
                        if option not in option_pretty:
                            option_pretty[option] = option.replace('_', ' ').title()
                            
                        if option == 'technical_replicates':
                            option_types[option] = 'number'

                        elif 'input_type' in option_structure:
                            option_types[option] = option_structure['input_type']
                            
                        elif 'special_case' in option_structure and 'value_unit' in option_structure['special_case']:
                            option_types[option] = 'value_unit'
                            
                        else:
                            option_types[option] = 'nested'
                        
                max_options = max([len(set([str(y) for y in option_dict[x] if y is not None])) for x in option_dict.keys() if option_types[x] not in ['number', 'value_unit']])
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
                        # TODO: sort by unit
                        option_values = sorted([x for x in option_dict[option] if x is not None], key=lambda d: d['unit'])
                    else:
                        option_values = sorted(list(set([x for x in option_dict[option] if x is not None])))
                    if len(option_values) > 0:
                        if option_types[option] == 'number':
                            num_vals = [normalize(x, 0, max_number, 0.1, 1) for x in option_values]
                        else:
                            num_vals = list(np.linspace(1, len(option_values), len(option_values)))
                        option_values = sorted([str(x) for x in option_values])
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
                max_anno[setting_id] = max_annotation               
                    
    return setting_dict, experimental_factors, organisms, max_vals, option_pretty, annotated_dict, max_anno


def normalize(x, minIn, maxIn, minOut, maxOut):
    input = (x-minIn)/(maxIn-minIn)
    return minOut + input * (maxOut-minOut)

def annotate(value, group_key=None):
    annotated_value = []
    if isinstance(value, list):
        if all([isinstance(x, dict) for x in value]):
            if group_key is not None:
                group_vals = [x[group_key] for x in value if group_key in x]
                grouped_value = {}
                for val in group_vals:
                    grouped_value[val] = [val]
                    for elem in value:
                        if group_key in elem and elem[group_key] == val:
                            grouped_value[val] += [x for x in annotate(elem) if x not in grouped_value[val]]
                for key in list(grouped_value.keys()):
                    annotated_value += [x for x in grouped_value[key]]
            else:
                for elem in value:
                    annotated_value += [x for x in annotate(elem) if x not in annotated_value]
            keys = []
            for elem in [list(x.keys()) for x in value]:
                keys += elem
            keys = list(set(keys))

            for key in keys:
                key_vals = []
                for elem in value:
                    if key in elem:
                        key_vals += [x for x in annotate(elem[key]) if x not in key_vals]
                annotated_value += [x for x in key_vals if x not in annotated_value]
        else:
            for elem in value:
                annotated_value += [x for x in annotate(elem) if x not in annotated_value]
    elif isinstance(value, dict):
        if 'value' in value and 'unit' in value:
            annotated_value += [x for x in [f'{value["value"]}{value["unit"]}'] if x not in annotated_value]
        else:
            for key in value:
                annotated_value += [x for x in annotate(value[key]) if x not in annotated_value]
    else:
        annotated_value += [x for x in [re.sub("0000(0)*", "...", str(value))] if x not in annotated_value]
    
    return annotated_value