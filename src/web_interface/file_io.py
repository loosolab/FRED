import src.file_reading as file_reading
import src.utils as utils
import os

# TODO: comment


def save_object(dictionary, path, filename):
    """
    This function saves the yaml structure into a file
    :param dictionary: the parsed wi object in yaml format
    :param path: the path to save the file to
    :param filename: the name of the file
    :return: new_filename: the name under which the file was saved
    """

    # search for all metadata files
    metafiles, validation_reports = file_reading.iterate_dir_metafiles(
        [path], return_false=True)

    project_id = dictionary['project']['id']
    # TODO: own function
    correct_file = None
    for metafile in metafiles:
        if 'project' in metafile and 'id' in metafile['project'] and \
                metafile['project']['id'] == project_id:
            correct_file = metafile
            break

    if correct_file is not None:
        path = correct_file['path']
        new_filename = path
        utils.save_as_yaml(dictionary, path)
    else:
        new_filename = f'{project_id}_{filename}' \
                       f'_metadata.yaml'
        utils.save_as_yaml(dictionary, os.path.join(path, new_filename))
        new_filename = os.path.join(path, new_filename)
    return new_filename, project_id


def save_filenames(file_str, path):
    """
    This function saves the generated filenames into a file
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
