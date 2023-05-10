import src.find_metafiles as find_metafiles
import src.utils as utils
import os


def save_object(dictionary, path, filename):
    """
    This function saves the yaml structure into a file
    :param dictionary: the parsed wi object in yaml format
    :param path: the path to save the file to
    :param filename: the name of the file
    :return: new_filename: the name under which the file was saved
    """
    metafiles = find_metafiles.find_projects(path,
                                         f'id:"{dictionary["project"]["id"]}"',
                                         False)
    if len(metafiles) > 0:
        for elem in metafiles:
            for key in elem:
                if key == dictionary['project']['id']:
                    path = elem[key]
        new_filename = path
        utils.save_as_yaml(dictionary, path)
    else:
        new_filename = f'{filename}_{dictionary["project"]["id"]}' \
                       f'_metadata.yaml'
        utils.save_as_yaml(dictionary, os.path.join(path, new_filename))
        new_filename = os.path.join(path, new_filename)
    return new_filename


def save_filenames(file_str, path):
    """
    This function saves the generated filenames into a file.
    :param file_str: the filenames to be saved
    :param path: the path to save the file to
    :return: filename: the name under which the generated filenames are saved
    """
    if file_str is not None:
        filename = f'{file_str[0]}_samples.txt'
        text_file = open(os.path.join(path, filename), "w")
        text_file.write(file_str[1])
        text_file.close()
    else:
        filename = None
    return filename