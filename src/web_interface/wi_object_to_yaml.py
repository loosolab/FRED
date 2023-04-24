import src.utils as utils
import src.web_interface.wi_utils as wi_utils
import os
import pytz
from dateutil import parser


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

    # iterate over parts (from general structure to ensure order)
    for key in key_yaml:

        # make sure the key is present in the wi object
        if key in wi_object:

            # parse every part into yaml format
            result[key], organism, sample_name, nom = parse_part(
                wi_object[key], key_yaml, wi_object['all_factors'], project_id,
                organism, sample_name, nom)

    # remove keys with value None
    result = {k: v for k, v in result.items() if v is not None}

    return result


def parse_part(wi_object, key_yaml, factors, project_id, organism, sample_name,
               nom):
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

            # iterate over the list elements
            for i in range(len(wi_object['list_value'])):

                # test if the element is a dictionary
                if isinstance(wi_object['list_value'][i], dict):

                    # special case: condition
                    if wi_object['list_value'][i]['position'].split(
                            ':')[-1] == 'condition':

                        # define emtpy list to save parsed samples to
                        samples = []

                        # iterate over all samples
                        for sub_elem in \
                                wi_object['list_value'][i]['list_value']:

                            # convert samples
                            sample, organism, sample_name, nom = \
                                parse_list_part(sub_elem, key_yaml, factors,
                                                project_id, organism,
                                                sample_name, nom)

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
                        c_val, organism, sample_name, nom = \
                            parse_list_part(wi_object['list_value'][i],
                                            key_yaml, factors[i], project_id,
                                            organism, sample_name, nom)
                        val.append(c_val)

                    # no special case
                    else:

                        # call parse function with all experimental factors
                        c_val, organism, sample_name, nom = \
                            parse_list_part(wi_object['list_value'][i],
                                            key_yaml, factors, project_id,
                                            organism, sample_name, nom)
                        val.append(c_val)

                # if list element is str/int/bool
                else:

                    # add list element to list
                    val.append(wi_object['list_value'][i])

            if len(val) == 0:
                val = None

        # the values are not saved as a list
        else:

            # wi object contains input fields
            if 'input_fields' in wi_object:

                # special case: technical replicates
                if wi_object['position'].split(':')[-1] == \
                        'technical_replicates':

                    # TODO: comment
                    t_sample_name = []
                    count = [x['value'] for x in wi_object['input_fields'] if
                             x['position'].split(':')[-1] == 'count'][0]

                    for c in range(count):
                        for m in range(nom):
                            t_sample_name.append(f'{project_id}_'
                                                 f'{organism}_'
                                                 f'{sample_name}'
                                                 f'_t{"{:02d}".format(c + 1)}_'
                                                 f'm{"{:02d}".format(m + 1)}')
                    val = {'count': count, 'sample_name': t_sample_name}

                # no special case
                else:

                    # call this function on the input fields
                    val, organism, sample_name, nom = \
                        parse_part(wi_object['input_fields'], key_yaml,
                                   factors, project_id, organism, sample_name,
                                   nom)

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

                        # TODO: own function
                        # convert the default time to local time
                        default_time = parser.parse(wi_object['value'])
                        timezone = pytz.timezone("Europe/Berlin")
                        local_time = default_time.astimezone(timezone)
                        val = local_time.strftime("%d.%m.%Y")

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

                        # save value
                        val = convert_value

                        # set the number of replicates
                        if wi_object['position'].split(':')[-1] == \
                                'number_of_measurements':
                            nom = val

    # wi object is a list
    elif isinstance(wi_object, list):

        # call parse list function
        val, organism, sample_name, nom = parse_list_part(
            wi_object, key_yaml, factors, project_id, organism, sample_name,
            nom)

    return val, organism, sample_name, nom


def parse_list_part(wi_object, key_yaml, factors, project_id, organism,
                    sample_name, nom):
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
            organism = wi_object[i]['value'].split(' ')[0]
            short = utils.get_whitelist(
                os.path.join('abbrev', 'organism_name'), organism)['whitelist']

            organism = short[organism]

        # special case: experimental factors
        elif wi_object[i]['position'].split(':')[-1] == 'experimental_factors':

            # iterate over experimental factors
            for r in range(len(factors)):

                # nested factor
                if len(factors[r]['values']) == 1 and isinstance(
                        factors[r]['values'][0], dict):

                    # remove key 'multi'
                    if 'multi' in factors[r]['values'][0]:
                        factors[r]['values'][0].pop('multi')

                    # remove keys with None as value
                    factors[r]['values'][0] = {
                        k: v for k, v in factors[r]['values'][0].items()
                        if v is not None}

                    # test if the key in the 'values' dictionary matches the
                    # factor and overwrite the dictionary with its list values
                    # -> this is the case if a factor can be a list and can
                    #    therefor occur multiple times in a condition
                    # -> key multi has to be added -> change 'values' from list
                    #    to dict
                    # -> e.g. factor tissue -> values {tissue: [...], multi: }
                    if list(factors[r]['values'][0].keys()) == \
                            [factors[r]['factor']]:
                        factors[r]['values'] = \
                            factors[r]['values'][0][factors[r]['factor']]

                else:

                    # fetch the properties of the experimental factor from the
                    # general structure
                    infos = list(utils.find_keys(
                        key_yaml, factors[r]['factor']))

                    # iterate over values of experimental factor
                    for j in range(len(factors[r]['values'])):

                        # factor contains whitelist keys
                        if 'whitelist_keys' in factors[r]:

                            # replace value with converted one
                            factors[r]['values'][j] = \
                                wi_utils.parse_whitelist_keys(
                                factors[r]['whitelist_keys'],
                                factors[r]['values'][j], factors[r]['headers']
                                if 'headers' in factors[r] else None)

                        # factor contains headers but no whitelist keys
                        elif 'headers' in factors[r]:

                            # replace the original value with the one split
                            # according to the header
                            factors[r]['values'][j] = wi_utils.parse_headers(
                                factors[r]['headers'], factors[r]['values'][j])

                        # factor of type value_unit
                        elif len(infos) > 0 and 'special_case' in infos[0]\
                                and 'value_unit' in infos[0]['special_case']:

                            factors[r]['values'][j] = \
                                wi_utils.split_value_unit(
                                    factors[r]['values'][j])

                    # remove the keys 'header' and 'whitelist_keys'
                    if 'whitelist_keys' in factors[r]:
                        factors[r].pop('whitelist_keys')
                    if 'headers' in factors[r]:
                        factors[r].pop('headers')

            # set val to factors
            val = factors

        # no special case
        else:

            # call parse part function
            val, organism, sample_name, nom = parse_part(
                wi_object[i], key_yaml, factors, project_id, organism,
                sample_name, nom)

        # test if the value is not empty
        if val is not None or (type(val) in [str, dict] and len(val) > 0):

            # overwrite the old value with the converted one
            res[wi_object[i]['position'].split(':')[-1]] = val

    return res if len(res) > 0 else None, organism, sample_name, nom
