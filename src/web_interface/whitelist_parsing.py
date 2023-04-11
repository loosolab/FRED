import src.utils as utils
import copy


def get_single_whitelist(ob):
    """
    This functions returns a sigle whitelist of type 'plain' for a key that is
    specified within a given dictionary. If the organism is specified as well,
    dependent whitelists only contain the values for said organism.
    (-> used for metadata generation and editing) If no organism is given, the
    whitelists of multiple organisms are merged together. (-> used for
    searching)
    :param ob: a dictionary containing the key 'key_name' and optionally the
    key 'organism'
    :return: either a whitelist or None if no whitelist exists
    """
    if 'organism' in ob:
        infos = {'organism': ob['organism']}
        all_plain = False
    else:
        infos = {}
        all_plain = True
    whitelist = utils.get_whitelist(ob['key_name'], infos, all_plain)
    if whitelist and 'whitelist' in whitelist:
        return whitelist['whitelist']
    else:
        return None


def get_whitelist_with_type(key, key_yaml, organism, headers):
    """
    This function reads in a whitelist and returns it together with its type.
    :param key: the key containing a whitelist
    :param key_yaml: the read in keys.yaml
    :param organism: the selected organism
    :param headers: the headers that a whitelist may contain
    :return:
    whitelist: the read in whitelist
    whitelist_type: the whitelist type
    input_type: the type of the expected value
    headers: the headers that might occur in the whitelist
    """
    whitelist_type = None
    is_list = False
    whitelist_keys = None
    filled_object = {'organism': copy.deepcopy(organism)}
    organism = organism.split(' ')[0]
    input_type = list(utils.find_keys(key_yaml, key))
    if len(input_type) > 0:
        if input_type[0]['list']:
            is_list = True
        if isinstance(input_type[0]['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) \
                <= set(input_type[0]['value'].keys()):
            if len(input_type[0]['value'].keys()) == 2 and 'value' in \
                    input_type[0]['value'] and 'unit' in \
                    input_type[0]['value']:
                input_type = 'value_unit'
            elif 'special_case' in input_type[0] and 'merge' in \
                    input_type[0]['special_case']:
                input_type = 'select'
            else:
                val = []
                for k in input_type[0]['value']:
                    k_val = {}
                    k_val['whitelist'], k_val['whitelist_type'], \
                        k_val['input_type'], \
                        header, whitelist_keys = get_whitelist_with_type(
                        k, key_yaml, organism, headers)
                    if header is not None:
                        k_val['headers'] = header
                    if whitelist_keys is not None:
                        k_val['whitelist_keys'] = whitelist_keys
                    node = list(utils.find_keys(key_yaml, k))[0]
                    if k_val['input_type'] == 'value_unit':
                        k_val['unit'] = None
                    k_val['displayName'] = node['display_name']
                    k_val['required'] = node['mandatory']
                    k_val['position'] = k
                    k_val['value'] = []
                    val.append(k_val)
                val.append({'displayName': 'Multi', 'position': 'multi',
                            'whitelist': [True, False], 'input_type': 'bool',
                            'value': False})
                input_type = 'nested'
                return val, whitelist_type, input_type, headers, whitelist_keys
        else:
            if input_type[0]['input_type'] == 'bool':
                input_type = 'bool'
            else:
                input_type = input_type[0]['input_type']
    else:
        input_type = 'short_text'

    if input_type == 'value_unit':
        whitelist = utils.read_whitelist('unit')
    elif input_type == 'select':
        whitelist = utils.read_whitelist(key)
    elif input_type == 'bool':
        whitelist = [True, False]
        input_type = 'select'
    else:
        whitelist = None

    if isinstance(whitelist, dict):
        if 'headers' in whitelist:
            headers = whitelist['headers']
        if whitelist['whitelist_type'] == 'group':
            whitelist = utils.read_grouped_whitelist(whitelist, filled_object)
            input_type = 'group_select'
            if 'headers' in whitelist:
                headers = whitelist['headers']
            if 'whitelist_keys' in whitelist:
                whitelist_keys = whitelist['whitelist_keys']
            if isinstance(whitelist['whitelist'], dict):
                new_w = []
                for value in whitelist['whitelist']:
                    if value not in ['headers', 'whitelist_keys']:
                        new_w.append({'title': value,
                                      'whitelist':
                                          whitelist['whitelist'][value]})
                whitelist = new_w
                whitelist_type = 'group'
            else:
                whitelist_type = 'plain_group'
                input_type = 'select'
        elif whitelist['whitelist_type'] == 'depend':
            whitelist = utils.read_depend_whitelist(whitelist['whitelist'],
                                                    organism)
            whitelist_type = 'depend'
            if 'headers' in whitelist:
                headers = whitelist['headers']
    if isinstance(whitelist, dict) and 'whitelist' in whitelist:
        whitelist = whitelist['whitelist']

    if whitelist and len(whitelist) > 30:
        input_type = 'multi_autofill'
        whitelist = None
    if is_list:
        node = list(utils.find_keys(key_yaml, key))[0]
        new_w = [
            {'whitelist': whitelist, 'position': key,
             'displayName': node['display_name'], 'required': True, 'value': [],
             'input_type': input_type, 'whitelist_type': whitelist_type},
            {'displayName': 'Multi', 'position': 'multi',
             'whitelist': [True, False], 'input_type': 'bool',
             'value': False}]
        for i in range(len(new_w)):
            if new_w[i]['input_type'] == 'multi_autofill' or new_w[i]['input_type'] == 'single_autofill':
                new_w[i]['search_info'] = {'key_name': key, 'organism': organism}
        whitelist = new_w
        whitelist_type = 'list_select'
        input_type = 'nested'
    return whitelist, whitelist_type, input_type, headers, whitelist_keys


def get_whitelist_object(item, organism_name, whitelists):
    """
    This function creates a whitelist object containing the whitelists of all
    keys of  sample.
    :param item: a key containing a whitelist
    :param organism_name: the selected organism
    :param whitelists: a dictionary to save the whitelists to
    :return:
    item: the key containing the whitelist
    whitelists: the whitelist object
    """
    if 'input_type' in item:
        input_type = item['input_type']
        if input_type == 'select' or input_type == 'single_autofill' or input_type == 'multi_autofill' or input_type == 'dependable':
            whitelist = utils.get_whitelist(item['position'].split(':')[-1],
                                            {'organism': organism_name})
            if 'headers' in whitelist:
                item['headers'] = whitelist['headers']
            if 'whitelist_keys' in whitelist:
                item['whitelist_keys'] = whitelist['whitelist_keys']

            if whitelist['whitelist_type'] == 'group':
                input_type = 'group_select'
            if whitelist['whitelist_type'] == 'plain' or \
                    whitelist['whitelist_type'] == 'plain_group':
                whitelist = whitelist['whitelist']
        elif input_type == 'bool':
            whitelist = [True, False]
            input_type = 'select'
        elif input_type == 'value_unit':
            if 'value_unit' not in item:
                item['value_unit'] = None
            whitelist = utils.read_whitelist('unit')
            if 'whitelist_type' in whitelist and whitelist[
                    'whitelist_type'] == 'plain':
                whitelist = whitelist['whitelist']
        else:
            whitelist = None

        item['whitelist'] = item['position'].split(':')[-1] if whitelist is not None else None
        if whitelist and isinstance(whitelist, list) and len(whitelist) > 30:
            if item['list']:
                input_type = 'multi_autofill'
            else:
                input_type = 'single_autofill'
            item['search_info'] = {'organism': organism_name,
                                   'key_name': item['position'].split(':')[-1]}
            if not 'list_value' in item:
                item['list_value'] = []
            whitelist = None
        item['input_type'] = input_type
        if input_type == 'group_select':
            w = []
            for key in whitelist['whitelist']:
                w.append({'title': key,
                          'whitelist': whitelist['whitelist'][key]})
            whitelist = w
        if whitelist:
            whitelists[item['position'].split(':')[-1]] = whitelist
        if input_type == 'value_unit':
            whitelists['unit'] = whitelist
    elif 'input_fields' in item:
        for i in item['input_fields']:
            i, whitelists = get_whitelist_object(i, organism_name, whitelists)
    return item, whitelists

