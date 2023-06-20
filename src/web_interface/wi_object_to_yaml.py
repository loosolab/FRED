import src.utils as utils
import src.web_interface.wi_utils as wi_utils
import os


def parse_object(wi_object, key_yaml):
    """
    This function parses a wi object back into a yaml
    :param key_yaml: the read in general structure
    :param wi_object: the filled wi object
    :return: result: a dictionary matching the metadata yaml structure
    """

    # define an empty dictionary to store the converted wi_object
    result = {}

    # TODO: needed? better solution?
    # save project id
    project_id = ''
    for elem in wi_object['project']['input_fields']:
        if elem['position'].split(':')[-1] == 'id' and elem['value'] \
                is not None:
            project_id = elem['value']

    # set parameters organism, sample_name and nom -> get filled during
    # conversion
    organism = ''
    sample_name = ''
    nom = 1
    global_count = 1
    local_count = 1
    double = []

    # iterate over parts (from general structure to ensure order)
    for key in key_yaml:

        # make sure the key is present in the wi object
        if key in wi_object:

            # parse every part into yaml format
            result[key], organism, sample_name, nom, global_count, local_count, double = parse_part(
                wi_object[key], key_yaml, wi_object['all_factors'], project_id,
                organism, sample_name, nom, global_count, local_count, double)

    # remove keys with value None
    result = {k: v for k, v in result.items() if v is not None}

    return result


def get_file_name(sample_name, double):
    splitted_name = sample_name.split('-')
    new_name = []
    for elem in splitted_name:
        new_elem, gene = split_name(elem, double)
        if new_elem != '':
            new_name.append(new_elem)
    sample_name = '_'.join(new_name)
    return sample_name


def split_name(elem, double, gene=True):
    new_name = []
    if '+' in elem:
        new_split = elem.split('+')
        for part in new_split:
            new_part, gene = split_name(part, double, gene=gene)
            if new_part != '':
                new_name.append(new_part)
        elem = '-'.join(new_name)

    if '#' in elem:
        remove = elem.split('#')[0]
        elem, gene = split_name(elem[len(f'{remove}#'):], double, gene=gene)

    if '.' in elem:
        if elem.lower() in [f'gn.{x.lower()}' for x in double]:
            gene = False
            elem = ''
        elif elem.lower().startswith('embl.') and gene is True:
            elem = ''
        else:
            elem = elem.split('.')[1]

    return elem, gene


def parse_part(wi_object, key_yaml, factors, project_id, organism, sample_name,
               nom, global_count, local_count, double):
    """
    This function parses a part of the wi object to create the yaml structure
    :param key_yaml: the read in general structure
    :param sample_name: the name of a sample build from condition name and
                        index of biological replicate
    :param wi_object: a part of the filled wi object
    :param factors: the selected experimental factors
    :param organism: the selected organism
    :param project_id: the project id
    :param nom: the number of measurements
    :return: val: the parsed part in yaml structure
             organism: the shortened version of the used organism
             sample_name: the name of the current sample
             nom: the number of measurements for the current sample
    """

    # initialize the converted value with None
    val = None

    # test if the object to parse is a dictionary
    if isinstance(wi_object, dict):

        # test if the values were stored in the 'list_value' key
        # (if the key takes a list or is of type single- or multi-autofill)
        if 'list_value' in wi_object and not (
                'input_type' in wi_object and wi_object['input_type'] ==
                'single_autofill'):

            # define an empty list to store the converted list values
            val = []

            # TODO: headers for list element (if gene is a list)
            # iterate over the list elements
            for i in range(len(wi_object['list_value'])):

                # test if the element is a dictionary
                if isinstance(wi_object['list_value'][i], dict):

                    # special case: condition
                    if wi_object['list_value'][i]['position'].split(
                            ':')[-1] == 'condition':

                        # define emtpy list to save parsed samples to
                        samples = []
                        local_count = 1

                        # iterate over all samples
                        for sub_elem in \
                                wi_object['list_value'][i]['list_value']:

                            # convert samples
                            sample, organism, sample_name, nom, global_count, local_count, double = \
                                parse_list_part(sub_elem, key_yaml, factors,
                                                project_id, organism,
                                                sample_name, nom, global_count, local_count, double)

                            # remove empty keys
                            sample = {k: v for k, v in sample.items() if v is
                                      not None}

                            # add sample to the samples list
                            samples.append(sample)

                        # add dictionary with condition name and biological
                        # replicates (samples) to list parsed list
                        condition = (
                            {'condition_name': wi_object['list_value'][
                                i]['correct_value'],
                             'biological_replicates': {'count': len(samples)}})

                        # add samples to the condition dictionary if count > 0
                        if len(samples) > 0:
                            condition['biological_replicates']['samples'] = \
                                samples

                        # add condition to list of converted values
                        val.append(condition)

                # test if list element is a list
                elif isinstance(wi_object['list_value'][i], list):

                    # special case: experimental setting
                    if wi_object['position'].split(':')[-1] == \
                            'experimental_setting':

                        # call parse function using the experimental factors
                        # with the same index as the setting
                        c_val, organism, sample_name, nom, global_count, local_count, double = \
                            parse_list_part(wi_object['list_value'][i],
                                            key_yaml, factors[i], project_id,
                                            organism, sample_name, nom, global_count, local_count, double)

                        # add the converted value to the list
                        val.append(c_val)

                    # no special case
                    else:

                        # call parse function with all experimental factors
                        c_val, organism, sample_name, nom, global_count, local_count, double = \
                            parse_list_part(wi_object['list_value'][i],
                                            key_yaml, factors, project_id,
                                            organism, sample_name, nom, global_count, local_count, double)

                        # add the converted value to the list
                        val.append(c_val)

                # if list element is str/int/bool
                else:

                    # add list element to list
                    val.append(wi_object['list_value'][i])

            # set the converted value to None if it is an empty list
            if len(val) == 0:
                val = None

        # the values are not saved as a list
        else:

            # wi object contains input fields
            if 'input_fields' in wi_object:

                # special case: technical replicates
                if wi_object['position'].split(':')[-1] == \
                        'technical_replicates':

                    file_name = get_file_name(sample_name.rstrip(f'_{sample_name.split("_")[-1]}'), double)
                    # TODO: comment
                    t_sample_name = []
                    t_file_name = []
                    count = [x['value'] for x in wi_object['input_fields'] if
                             x['position'].split(':')[-1] == 'count'][0]

                    for c in range(count):
                        for m in range(nom):
                            t_sample_name.append(f'{project_id}_'
                                                 f'{organism}_'
                                                 f'{sample_name}'
                                                 f'_t{"{:02d}".format(c + 1)}_'
                                                 f'm{"{:02d}".format(m + 1)}')
                            t_file_name.append(f'{project_id}__'
                                               f'{global_count}__'
                                               f'{file_name}__'
                                               f'{local_count}')
                            local_count += 1
                            global_count += 1

                    val = {'count': count, 'sample_name': t_sample_name, 'filenames': t_file_name}

                # no special case
                else:

                    # call this function on the input fields
                    val, organism, sample_name, nom, global_count, local_count, double = \
                        parse_part(wi_object['input_fields'], key_yaml,
                                   factors, project_id, organism, sample_name,
                                   nom, global_count, local_count, double)

            # no input fields
            else:

                # set the value that should be converted (saved in list_value
                # if input type is 'single_autofill', else saved in value)
                convert_value = wi_object['list_value'][0] if \
                    wi_object['input_type'] == 'single_autofill' and \
                    len(wi_object['list_value']) > 0 else wi_object['value']

                # test if value was filled
                if convert_value is not None:

                    # wi object contains whitelist keys
                    if 'whitelist_keys' in wi_object:

                        # replace value with converted one
                        convert_value = wi_utils.parse_whitelist_keys(
                            wi_object['whitelist_keys'], convert_value,
                            wi_object['headers']
                            if 'headers' in wi_object else None)

                    # wi object contains headers but no whitelist keys
                    elif 'headers' in wi_object:

                        # replace the original value with the one split
                        # according to the header
                        convert_value = wi_utils.parse_headers(
                            wi_object['headers'], convert_value)

                    # value is of type value_unit
                    if wi_object['input_type'] == 'value_unit':

                        # save the value and unit as a dictionary
                        val = {'value': wi_object['value'],
                               'unit': wi_object['value_unit']}

                    # value is of type date
                    elif wi_object['input_type'] == 'date':

                        # convert the date to a string of format 'DD.MM.YYYY'
                        val = wi_utils.date_to_str(wi_object['value'])

                    # value was changed for display -> original value saved at
                    # key 'correct_value'
                    elif 'correct_value' in wi_object:

                        # special_case sample name
                        if wi_object['position'].split(':')[-1] == \
                                'sample_name':

                            # split and save index of sample from sample name
                            sample_count = int(
                                convert_value.split('_')[-1])

                            # reformat sample name with ending 'b<index>' for
                            # number of biological replicate
                            val = f'{wi_object["correct_value"]}_b'\
                                  f'{"{:02d}".format(sample_count)}'

                            # set the sample name to the value
                            sample_name = val

                        else:

                            # save correct value
                            val = wi_object['correct_value']

                    else:

                        if isinstance(convert_value, str):
                            val = convert_value.replace('\\n', ' ').replace('\n', ' ').replace('\\', ' ')
                            val = ' '.join(val.split())
                        else:
                            # save value
                            val = convert_value

                        # set the number of replicates
                        if wi_object['position'].split(':')[-1] == \
                                'number_of_measurements':
                            nom = val

    # wi object is a list
    elif isinstance(wi_object, list):

        # call parse list function
        val, organism, sample_name, nom, global_count, local_count, double = parse_list_part(
            wi_object, key_yaml, factors, project_id, organism, sample_name,
            nom, global_count, local_count, double)

    return val, organism, sample_name, nom, global_count, local_count, double


def parse_list_part(wi_object, key_yaml, factors, project_id, organism,
                    sample_name, nom, global_count, local_count, double):
    """
    This function parses a part of the wi object of type list into the yaml
    structure
    :param sample_name: the name of a sample build from condition name and
                        index of biological replicate
    :param key_yaml: the read in general structure
    :param wi_object: the part of the wi object
    :param factors: the selected experimental factors
    :param organism: the selected organism
    :param project_id: the project id
    :param nom: the number of measurements
    :return: res: the parsed part in yaml structure
             organism: the shortened version of the used organism
             sample_name: the name of the current sample
             nom: the number of measurements for the current sample
    """

    # create dictionary to save parsed elements to
    res = {}

    # iterate over list
    for i in range(len(wi_object)):

        # special case: organism
        if wi_object[i]['position'].split(':')[-1] == 'organism':

            # TODO: headers
            # save the organism name
            organism = wi_object[i]['value'].split(' ')[0]

            # read in the abbrev whitelist for organisms
            short = utils.get_whitelist(os.path.join(
                'abbrev', 'organism_name'),
                {'organism': organism})['whitelist']

            # save the shortened version of the organism
            organism = short[organism]

        # special case: experimental factors
        if wi_object[i]['position'].split(':')[-1] == 'experimental_factors':

            # iterate over experimental factors
            for r in range(len(factors)):

                factors[r], double = parse_factor(factors[r], key_yaml, double)

            # set val to factors
            val = factors

        # no special case
        else:

            # call parse part function
            val, organism, sample_name, nom, global_count, local_count, double = parse_part(
                wi_object[i], key_yaml, factors, project_id, organism,
                sample_name, nom, global_count, local_count, double)

        # test if the value is not empty
        if val is not None and (
                (type(val) in [str, list, dict] and len(val) > 0) or
                type(val) not in [str, list, dict]):

            # overwrite the old value with the converted one
            res[wi_object[i]['position'].split(':')[-1]] = val

    return res if len(res) > 0 else None, organism, sample_name, nom, global_count, local_count, double


def parse_factor(factors, key_yaml, double):

    # nested factor
    if len(factors['values']) == 1 and isinstance(
            factors['values'][0], dict):

        if 'nested_infos' in factors:
            for key_ in factors['nested_infos']:
                if 'double' in factors['nested_infos'][key_]:
                    double = set(double + factors['nested_infos'][key_]['double'])

        # remove key 'multi'
        if 'multi' in factors['values'][0]:
            factors['values'][0].pop('multi')

        # remove keys with None as value
        factors['values'][0] = {
            k: v for k, v in factors['values'][0].items()
            if v is not None}

        # test if the key in the 'values' dictionary matches the
        # factor and overwrite the dictionary with its list values
        # -> this is the case if a factor can be a list and can
        #    therefor occur multiple times in a condition
        # -> key multi has to be added -> change 'values' from list
        #    to dict
        # -> e.g. factor tissue -> values {tissue: [...], multi: }
        if list(factors['values'][0].keys()) == \
                [factors['factor']]:
            factors['values'] = \
                factors['values'][0][factors['factor']]

        for i in range(len(factors['values'])):
            if isinstance(factors['values'][i], dict):
                remove_keys = []
                for key in factors['values'][i]:

                    if factors['values'][i][key] is None or (isinstance(factors['values'][i][key], list) and len(factors['values'][i][key]) == 0):
                        remove_keys.append(key)
                    if key == 'gene':
                        headers = 'gene_name ensembl_id'

                        for j in range(len(factors['values'][i][key])):
                            factors['values'][i][key][j] = wi_utils.parse_headers(
                                headers, factors['values'][i][key][j], mode='dict')
                    #if isinstance(factors['values'][i][key], dict):
                    #    if not 'factor' in factors['values'][i][key]:
                    #        factors['values'][i][key]['factor'] = key
                    #    factors['values'][i][key] = parse_factor(factors['values'][i][key], key_yaml)
                    #    factors['values'][i][key].pop('factor')
                for r_key in remove_keys:
                    factors['values'][i].pop(r_key)

    else:

        # fetch the properties of the experimental factor from the
        # general structure
        infos = list(utils.find_keys(
            key_yaml, factors['factor']))

        if 'double' in factors:
            double = set(double + factors['double'])

        # iterate over values of experimental factor
        for j in range(len(factors['values'])):

            # factor contains whitelist keys
            if 'whitelist_keys' in factors:

                # replace value with converted one
                factors['values'][j] = \
                    wi_utils.parse_whitelist_keys(
                        factors['whitelist_keys'],
                        factors['values'][j], factors['headers']
                        if 'headers' in factors else None)

            # factor contains headers but no whitelist keys
            elif 'headers' in factors:

                # replace the original value with the one split
                # according to the header
                factors['values'][j] = wi_utils.parse_headers(
                    factors['headers'], factors['values'][j])

            # factor of type value_unit
            elif len(infos) > 0 and 'special_case' in infos[0] \
                    and 'value_unit' in infos[0]['special_case']:

                factors['values'][j] = \
                    wi_utils.split_value_unit(
                        factors['values'][j])

    # remove the keys 'header' and 'whitelist_keys'
    if 'whitelist_keys' in factors:
        factors.pop('whitelist_keys')
    if 'headers' in factors:
        factors.pop('headers')
    if 'nested_infos' in factors:
        factors.pop('nested_infos')
    if 'double' in factors:
        factors.pop('double')
    return factors, double