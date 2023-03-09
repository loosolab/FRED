import os
from src.utils import read_in_yaml
from src import validate_yaml


# The following functions were inspired by Mampok and slightly customized
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/
# file_reading.py


def iterate_dir_metafiles(path_metafiles, mode='metadata', logical_validation=True, yaml=None):
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
    error_reports = []
    warning_reports = []
    error_count = 0
    warning_count = 0
    for path_metafile in path_metafiles:
        for subdir, dirs, files in os.walk(path_metafile):
            for file in files:
                # add files with suffix '_metadata.y(a)ml'
                if file.lower().endswith(
                        f'_{mode}.yaml') or file.lower().endswith(
                        f'_{mode}.yml'):
                    ypath = os.path.join(subdir, file)
                    # read these yaml as dict and append to metafile-list:
                    print('reading file ' + ypath)
                    metafile = read_in_yaml(ypath)
                    # test if metafile is valid
                    valid, missing_mandatory_keys, invalid_keys, \
                        invalid_entries, invalid_values, logical_warn = validate_yaml.validate_file(metafile, mode, logical_validation=logical_validation, yaml=yaml)
                    # add path to dic
                    metafile['path'] = ypath
                    if not valid:
                        error_reports.append((metafile, missing_mandatory_keys, invalid_keys, invalid_entries, invalid_values))
                        error_count += 1
                    else:
                        metafile_list.append(metafile)
                    if len(logical_warn) > 0:
                        warning_count += 1
                        warning_reports.append((metafile, logical_warn))
    return metafile_list, {'errors': {'count': error_count, 'report': error_reports}, 'warnings': {'count': warning_count, 'report': warning_reports}}
