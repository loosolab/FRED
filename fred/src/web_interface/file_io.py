import fred.src.utils as utils
import os

# TODO: comment


def save_object(dictionary, path, filename, edit_state):
    """
    This function saves the yaml structure into a file
    :param dictionary: the parsed wi object in yaml format
    :param path: the path to save the file to
    :param filename: the name of the file
    :return: new_filename: the name under which the file was saved
    """
    project_id = list(utils.find_keys(dictionary, "id"))
    if len(project_id) > 0:
        project_id = project_id[0]
    else:
        project_id = ""

    if not edit_state:
        filename = f"{project_id}_{filename}_metadata.yaml"

    # stamps every file the web interface creates or re-saves with the
    # current FRED version, same as CLI generate/edit -- otherwise a file
    # produced here would carry no version at all and immediately look
    # pre-3.0.0 to the version gate
    dictionary["version"] = utils.get_fred_version()
    utils.save_as_yaml(dictionary, os.path.join(path, filename))

    return filename, project_id


def save_filenames(file_str, path):
    """
    This function saves the generated filenames into a file
    :param file_str: the filenames to be saved
    :param path: the path to save the file to
    :return: filename: the name under which the generated filenames are saved
    """
    if file_str is not None:
        filename = f"{file_str[0]}_samples.txt"
        text_file = open(os.path.join(path, filename), "w")
        text_file.write(file_str[1])
        text_file.close()
    else:
        filename = None
    return filename
