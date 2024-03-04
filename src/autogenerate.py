import copy

from src import utils


class Autogenerate:

    def __init__(self, gen, position):
        """
        initialize class
        :param gen: an object generated from class Generate
        :param position: the position of the key
        """
        self.gen = gen
        self.position = position

    def get_id(self):
        """
        returns the project ID
        :return: project_id from class Generate
        """
        return self.gen.project_id

    def get_setting_id(self):
        """
        creates an ID for the experimental setting
        :return: setting_id (exp1, exp2, ...)
        """

        # search for setting IDs in result_dict
        setting_ids = list(utils.find_keys('setting_id', self.gen.result_dict))

        # find the setting_id with the highest index and add 1
        if len(setting_ids) > 0:
            max_id = 0
            for s_id in setting_ids[0]:
                max_id = max(max_id, int(s_id.replace('exp', '')))
            setting_id = f'exp{max_id+1}'

        # set setting_id to exp1 if it is the first setting
        else:
            setting_id = 'exp1'

        return setting_id

    def get_experimental_factors(self):
        """
        request the user to specify the experimental factors
        :return: experimental_factors: list of dictionaries
                 -> [{factor: <fac>, values: [<val>,...]}, ...]
        """


        factor_list = utils.get_whitelist('factor', self.gen.result_dict)['whitelist']
        plain_list = []
        exp_info = list(utils.find_keys(self.gen.key_yaml, 'experimental_factors'))[0]
        factor_info = \
        list(utils.find_keys(self.gen.key_yaml, 'factor'))[0]
        for fk in factor_list:
            plain_list += factor_list[fk]

        print(f'\n---\n{exp_info["factor_desc"]}')
        print(
            f'\nPlease select the analyzed experimental factors '
            f'(1-{len(plain_list)}) divided by comma:\n')

        used_factors = self.gen.get_input_list(factor_info, 'factor')
        experimental_factors = []

        for fac in used_factors:

            fac_node = list(utils.find_keys(self.gen.key_yaml, fac))[0]
            fac_dict = {}
            self.gen.parse_lists(fac_node, [fac], 2, fac_dict, is_factor=True)

            experimental_factors.append({'factor': fac, 'values': fac_dict[fac]})

        return experimental_factors

    def get_condition_name(self):
        experimental_setting = utils.find_position(self.gen.result_dict, self.position[:-3] + ['setting_id'])
        if experimental_setting not in self.gen.conditions:
            factors = utils.find_position(self.gen.result_dict, self.position[:-3] + ['experimental_factors'])
            factor_combis = {}
            for i in range(len(factors)):

                factor_info = \
                    list(utils.find_keys(self.gen.key_yaml, factors[i]['factor']))[0]
                factor = factors[i]['factor']
                values = copy.deepcopy(factors[i]['values'][0]) if len(
                    factors[i]['values']) == 1 and isinstance(
                    factors[i]['values'][0], dict) else copy.deepcopy(
                    factors[i]['values'])
                # if the values of the experimental factor are in a dictionary or the
                # factor contains a list (so the factor can occur multiple times in a
                # condition) than call the function get_combinations to create all
                # possible combinations of this factor with its values
                if factor_info['list'] or (
                        isinstance(factor_info['value'], dict)
                        and not ('special_case' in factor_info
                                 and 'value_unit' in
                                 factor_info['special_case'])):
                    for val in values:
                        val_info = list(utils.find_keys(self.gen.key_yaml, val))[0]
                        if 'special_case' in val_info:
                            if 'merge' in val_info['special_case']:
                                for j in range(len(values[val])):
                                    new_val = []
                                    for elem_key in values[val][j]:
                                        new_val.append(
                                            f'{elem_key}:"{values[val][j][elem_key]}"')
                                    values[val][
                                        j] = f'{"{"}{"|".join(new_val)}{"}"}'
                    if 'special_case' in factor_info:
                        if 'group' in factor_info['special_case']:
                            values['ident_key'] = factor_info['special_case'][
                                'group']
                        if 'control' in factor_info['special_case']:
                            values['control'] = factor_info['special_case'][
                                'control']
                    # overwrite the values with the combinations
                    factor_combis[factor] = utils.get_combis(
                        values, factor, self.gen.result_dict, self.gen.key_yaml)
                elif 'special_case' in factor_info and 'value_unit' in factor_info['special_case']:
                    values = [f'{val["value"]}{val["unit"]}' for val in values]
                    factor_combis[factor] = [f'{factor}:"{val}"' for val in values]
                else:
                    factor_combis[factor] = [f'{factor}:"{val}"' for val in values]
            factor_dict = []
            for elem_key in factor_combis:
                factor_dict.append(
                    {'factor': elem_key, 'values': factor_combis[elem_key]})
            # call get_condition_combinations to create all conditions
            combinations = utils.get_condition_combinations(factor_dict)
            for key in factor_combis:
                print(key, factor_combis[key])
                factor_combis[key] = [x for x in factor_combis[key] if x.count(f'{key}:') <= 1]
                print(key, factor_combis[key])
            self.gen.conditions[experimental_setting] = [factor_combis, combinations]

        i = 1
        print('Please combine the factors to create a condition.')
        for key in self.gen.conditions[experimental_setting][0]:
            print(f'\n\033[1m{key}\033[0m')
            for elem in self.gen.conditions[experimental_setting][0][key]:
                print(f'{i} {elem}')
                i += 1

        w = [x for xs in list(self.gen.conditions[experimental_setting][0].values())
             for x in xs]
        used_values = self.gen.parse_input_list(w, False)
        condition_name = None
        for elem in self.gen.conditions[experimental_setting][1]:
            if all([x in elem for x in used_values]) and len(elem) == len('-'.join(used_values)):
                condition_name = elem
                break
        if condition_name is not None:
            filled_conditions = []
            for i in range(self.position[-2]):
                filled_conditions.append(utils.find_position(self.gen.result_dict, self.position[:-2] + [i, 'condition_name']))
            if condition_name not in filled_conditions:
                return condition_name
            else:
                print('You already selected this condition. Try again.')
                return self.get_condition_name()
        else:
            print('Invalid condition. Please try again.')
            return self.get_condition_name()

    def get_samples(self):
        cond_name = utils.find_position(self.gen.result_dict, self.position[:-2] + ['condition_name'])
        test = utils.split_cond(cond_name)
        sample_structure = list(utils.find_keys(self.gen.key_yaml, 'samples'))[0]
        for elem in test:
            sample_structure['value'][elem[0]]['value'] = elem[1]
            if 'special_case' in sample_structure['value'][elem[0]]:
                sample_structure['value'][elem[0]]['special_case']['factor'] = True
            else:
                sample_structure['value'][elem[0]]['special_case'] = {'factor': True}
        self.gen.parse_lists(sample_structure, self.position, 2, self.gen.result_dict, is_factor=False)
        return utils.find_position(self.gen.result_dict, self.position)

    def get_sample_name(self):
        if self.position[-2] == 'technical_replicates':
            '''count = utils.find_position(self.gen.result_dict, self.position[:-1] + ['count'])
            nom = utils.find_position(self.gen.result_dict, self.position[:-2] + ['number_of_measurements'])
            sample_name = utils.find_position(self.gen.result_dict, self.position[:-2] + ['sample_name'])
            organism = utils.find_position(self.gen.result_dict, self.position[:self.position.index('experimental_setting')+2] + ['organism', 'organism_name'])
            samples = []
            for i in range(count):
                # iterate over the number of measurements
                for j in range(nom):
                    # add sample name containing id, organism, sample identifier,
                    # index of technical replicate and index of measurement to samples
                    # list
                    samples.append(f'{self.gen.project_id}_{organism}_{sample_name}_'
                                   f't{"{:02d}".format(i + 1)}_'
                                   f'm{"{:02d}".format(j + 1)}')'''
            return utils.create_sample_names(self.gen.result_dict, {}, self.position)
        else:
            condition = utils.find_position(self.gen.result_dict, self.position[:-4]+['condition_name'])
            return f'{utils.get_short_name(condition, self.gen.result_dict, self.gen.key_yaml)}_b{"{:02d}".format(self.position[-2] + 1)}'

    def get_filenames(self):
        setting_index = self.position.index('experimental_setting') + 1
        experimental_factors = utils.find_position(self.gen.result_dict, self.position[:setting_index+1] + ['experimental_factors'])
        double = []
        if len(list(utils.find_keys(experimental_factors, 'gene'))) > 0 or len(list(utils.find_values(experimental_factors, 'gene'))) > 0:
            gene_whitelist = utils.get_whitelist('gene', self.gen.result_dict)
            double = gene_whitelist['double'] if 'double' in gene_whitelist else []
        return utils.create_filenames(self.gen.result_dict, double, self.position, {})

    def get_count(self):
        return len(utils.find_position(self.gen.result_dict, self.position[:-1] + ['samples']))