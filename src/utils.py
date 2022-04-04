import yaml


# The following functions were copied from Mampok
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/utils.py

def save_as_yaml(dictionary, file_path):
    """
    save dictionary as YAML file
    :param dictionary: a dictionary that should be saved
    :param file_path: the path of the yaml file to be created
    """
    with open(file_path, 'w') as file:  # format richtig so?
        documents = yaml.dump(dictionary, file)


def read_in_yaml(yaml_file):
    """
    read yaml, auto lower all keys
    :param yaml_file: the path to the yaml file to be read in
    :return: low_output: a dictionary containing the information of the yaml
    """
    with open(yaml_file) as file:
        output = yaml.load(file, Loader=yaml.FullLoader)
    low_output = {k.lower(): v for k, v in output.items()}
    return low_output


# The following function was found on Stackoverflow
# https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-
# nested-dictionaries-and-lists
# original function name: findkeys
# submitted by user 'arainchi' on Nov 9, 2013 at 3:14,
# edited on Sep 12, 2019 at 21:50

def find_keys(node, kv):
    """
    generator to return all values of given key in dictionary
    :param node: a dictionary to be searched
    :param kv: the key to search for
    """
    if isinstance(node, list):
        for i in node:
            for x in find_keys(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in find_keys(j, kv):
                yield x


# The following functions are based on 'findkeys' and customized to solve
# related problems

def find_values(node, kv):
    """
    generator to return all keys in dictionary that fit a given key value
    :param node: a dictionary to be searched
    :param kv: the key value to search for
    """
    if isinstance(node, list):
        for i in node:
            for x in find_values(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node.values():
            yield kv
        for j in node.values():
            for x in find_values(j, kv):
                yield x

def get_keys_as_list(node, nested, pre=''):
    """
    generator to return all keys in dictionary that fit a given key value
    :param node: a dictionary to be searched
    :param kv: the key value to search for
    """
    if isinstance(node, list):
        test = []
        is_list_or_dict = False
        for i in node:
            if isinstance(i, list) or isinstance(i, dict):
                is_list_or_dict = True
                for x in get_keys_as_list(i, nested):
                    if nested:
                        test.append(pre + str(x))
                    else:
                        yield pre + str(x)
                if nested:
                    yield test
        if not is_list_or_dict:
            yield pre + str(node)
    elif isinstance(node, dict):
        for j in list(node.keys()):
            for x in get_keys_as_list(node[j], nested, pre + j + ':'):
                yield x
    else:
        yield pre + str(node)


# split string of list into list
def split_str(s):
    splitted = s.split(':')
    keys = ':'.join(splitted[0:-1])
    value = splitted[-1].replace('[','').replace(']','').replace('\'','').split(',')
    return keys, value


# parse list to dictionary for webinterface
def parse_list_to_dict(node):
    if isinstance(node, list):
        for i in range(len(node)):
            node[i] = parse_list_to_dict(node[i])
        node = {'title': 'Information ' + node[0]['position'].split(':')[-2], 'desc' : 'TBA', 'input_fields': node}
    else:
        keys, value = split_str(node)
        node={'position': keys, 'value': value, 'whitelist': None, 'displayName': keys.split(':')[-1], 'desc': 'TBA'}
    return node
