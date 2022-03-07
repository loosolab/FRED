import os
from src.utils import read_in_yaml

# from Mampok -> changed mamplan to metafile
def iterate_dir_metafiles(path_metafiles):
    # turn string into list
    if isinstance(path_metafiles, str):
        path_metafiles = [path_metafiles]
    # iterate through paths, through directories, through files
    metafile_list = []
    for path_metafile in path_metafiles:
        for subdir, dirs, files in os.walk(path_metafile):
            for file in files:
                try:
                    # add files with suffix 'metadata.y(a)ml'
                    if file.lower().endswith(
                            "metadata.yaml") or file.lower().endswith(
                            'metadata.yml'):
                        ypath = os.path.join(subdir, file)
                        # read these yaml as dict and append to metafile-list:
                        metafile = read_in_yaml(ypath)
                        metafile['path'] = ypath  # add path to dic
                        if metafile:
                            metafile_list.append(metafile)
                except Exception as e:
                    print("Problem with YAML format or entries!")

    return metafile_list
