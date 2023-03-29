import os
from src.utils import read_in_yaml
from src import validate_yaml


# The following functions were inspired by Mampok and slightly customized
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/
# file_reading.py


def iterate_dir_metafiles(path_metafiles, mode='metadata', logical_validation=True, yaml=None, whitelist_path=None):
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
    file_reports = []
    error_count = 0
    warning_count = 0
    corrupt_count = 0
    all_files = 0
    for path_metafile in path_metafiles:
        for subdir, dirs, files in os.walk(path_metafile):
            for file in files:
                error_reports = None
                warning_reports = None
                corrupted = False
                report = {}
                # add files with suffix '_metadata.y(a)ml'
                if file.lower().endswith(
                        f'{mode}.yaml') or file.lower().endswith(
                        f'{mode}.yml'):
                    ypath = os.path.join(subdir, file)
                    # read these yaml as dict and append to metafile-list:
                    print('reading file ' + ypath)
                    all_files += 1
                    metafile = read_in_yaml(ypath)
                    # test if metafile is valid
                    valid, missing_mandatory_keys, invalid_keys, \
                        invalid_entries, invalid_values, logical_warn = validate_yaml.validate_file(metafile, mode, logical_validation=logical_validation, yaml=yaml, whitelist_path=whitelist_path)
                    # add path to dic
                    metafile['path'] = ypath
                    if not valid:
                        error_reports = (missing_mandatory_keys, invalid_keys, invalid_entries, invalid_values)
                        corrupted = True
                        error_count += (len(missing_mandatory_keys) + len(invalid_keys) + len(invalid_entries) + len(invalid_values))
                    else:
                        metafile_list.append(metafile)
                    if len(logical_warn) > 0:
                        corrupted = True
                        warning_count += len(logical_warn)
                        warning_reports = logical_warn
                    if corrupted:
                        corrupt_count += 1
                        file_reports.append({'file': metafile, 'error': error_reports, 'warning': warning_reports})
    return metafile_list, {'all_files': all_files, 'corrupt_files': {'count': corrupt_count, 'report': file_reports}, 'error_count': error_count, 'warning_count': warning_count}
