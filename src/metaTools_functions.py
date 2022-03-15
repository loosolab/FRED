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
    :return: result: a dictionary containing all matches, key=id,
    value=dictionary or path depending on return_dict
    """

    # split parameters linked via or into list
    search_parameters = search.split(' or ')

    for i in range(len(search_parameters)):

        # split parameters linked via 'and' within the 'or-list' -> nested list
        search_parameters[i] = search_parameters[i].split(' and ')

        for j in range(len(search_parameters[i])):

            # parameter to declare if search parameter should occur
            # set to False if 'not' was declared for the search parameter
            # appended to the search parameter with ':' as delimiter
            should_be_in = True
            if 'not ' in search_parameters[i][j]:
                should_be_in = False
                search_parameters[i][j] = search_parameters[i][j]. \
                    replace('not ', '')
            search_parameters[i][j] = search_parameters[i][j].strip() + (
                        ':' + str(should_be_in))

    # read in all *_metadata.yaml(yml) within the path
    metafiles = file_reading.iterate_dir_metafiles([dir_path])

    # search for matches within the yaml
    result = find_metafiles.find_projects(metafiles, search_parameters,
                                          return_dict)
    return result


def add(file_path, add_parameters):
    # TODO: add function
    # TODO: test for validity

    return 'TBA'


def generate(file_path, meta_dict):
    """
    generates a yaml file of a given dictionary
    :param file_path: path the yaml should be saved at
    :param meta_dict: dictionary to be converted to yaml
    """

    # TODO: test for validity

    utils.save_as_yaml(meta_dict, file_path)
