import os
from src.utils import read_in_yaml
from src import validate_yaml


# The following functions were inspired by Mampok and slightly customized
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/
# file_reading.py


def iterate_dir_metafiles(path_metafiles):
    """
    iterate through a list of paths to find all _metadata.yaml(yml) files
    :param path_metafiles: list of paths containing yaml files
    :return: metafile_list: list of dictionaries containing information from
             found metadata files
    """

    # turn string into list
    if isinstance(path_metafiles, str):
        path_metafiles = [path_metafiles]

    # iterate through paths, through directories, through files
    metafile_list = []
    for path_metafile in path_metafiles:
        for subdir, dirs, files in os.walk(path_metafile):
            for file in files:
                # add files with suffix '_metadata.y(a)ml'
                if file.lower().endswith(
                        "_metadata.yaml") or file.lower().endswith(
                        '_metadata.yml'):
                    ypath = os.path.join(subdir, file)
                    # read these yaml as dict and append to metafile-list:
                    metafile = read_in_yaml(ypath)
                    # test if metafile is valid
                    valid, missing_mandatory_keys, invalid_keys, \
                        invalid_entries = validate_yaml.validate_file(metafile)
                    # add path to dic
                    metafile['path'] = ypath
                    if not valid:
                        validate_yaml.print_validation_report(
                            metafile, missing_mandatory_keys, invalid_keys,
                            invalid_entries)
                    else:
                        if metafile:
                            metafile_list.append(metafile)
    return metafile_list
