from src import file_reading
from src import find_metafiles
from src import utils


# This script includes all functions called by the metaTools CLI


def find(dir_path, search, return_dict):
    """
    search for metadata files that match given search parameters
    :param dir_path: a path containing metadata yaml
    :param search: a string specifying search parameters linked via 'and', 'or'
    and 'not'
    :param return_dict: bool: if True, whole dictionary is returned,
    if False path of dictionary is returned
    :return: result: a dictionary containing all matches, key=input_id,
    value=dictionary or path depending on return_dict
    """

    # read in all *_metadata.yaml(yml) within the path
    metafiles = file_reading.iterate_dir_metafiles([dir_path])
    search = '(' + search + ')'

    result = []

    for metafile in metafiles:

        sub_list = ''
        sub = ''
        for letter in search:
            if letter == '(':
                sub_list += sub
                sub = ''
            elif letter == ')':
                if sub != '':
                    res = find_metafiles.find_projects(metafile, sub, return_dict)
                    sub_list += str(True) if res else str(False)
                if sub_list != ('True' or 'False'):
                    res = find_metafiles.find_projects(metafile, sub_list, return_dict)
                    sub_list = str(True) if res else str(False)
                sub = ''
            else:
                sub += letter
        if sub_list == 'True':
            result.append({metafile['project']['id']: metafile['path'] if
            return_dict == False else metafile})
    return result


def add(file_path, add_parameters):
    metafile = file_reading.iterate_dir_metafiles([file_path])
    for i in range(len(add_parameters)):
        add_parameters[i] = add_parameters[i].split(':')
    for param in add_parameters:
        return test(metafile, param[:-1], param[-1])



def test(metafile, param, value):
    if len(param)==1:
        metafile[param[0]] = value
    else:
        if param[0] in metafile:
            r = metafile[param[0]]
            if isinstance(r,list):
                if len(r) == 1:
                    metafile[param[0]][0] = test(metafile[param[0]][0], param[1:],  value)
            else:
                metafile[param[0]] = test(metafile[param[0]], param[1:], value)
    return metafile


def generate(file_path, meta_dict):
    """
    generates a yaml file of a given dictionary
    :param file_path: path the yaml should be saved at
    :param meta_dict: dictionary to be converted to yaml
    """

    # TODO: test for validity

    utils.save_as_yaml(meta_dict, file_path)
