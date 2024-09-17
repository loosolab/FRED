import copy
import json
import multiprocessing
import os
import sys
import time
from functools import partial

sys.path.append("metadata-organizer")
from src import validate_yaml
from src.utils import read_in_yaml

# The following functions were inspired by Mampok and slightly customized
# https://gitlab.gwdg.de/loosolab/software/mampok/-/blob/master/mampok/
# file_reading.py


def iterate_dir_metafiles(
    key_yaml,
    path_metafiles,
    filename="_metadata",
    logical_validation=True,
    yaml=None,
    whitelist_path=None,
    return_false=False,
    run_as_sub=False,
):
    """
    iterate through a list of paths to find all _metadata.yaml(yml) files
    :param path_metafiles: list of paths containing yaml files
    :return: metafile_list: list of dictionaries containing information from
             found metadata files
    """
    if run_as_sub == False:
        # turn string into list
        if isinstance(path_metafiles, str):
            path_metafiles = [path_metafiles]

        # iterate through paths, through directories, through files
        metafile_list = []
        file_reports = []
        error_count = 0
        warning_count = 0
        corrupt_count = 0
        items = []
        for path_metafile in path_metafiles:
            items += [
                os.path.join(subdir, file)
                for subdir, dirs, files in os.walk(path_metafile)
                for file in files
                if file.lower().endswith(f"{filename}.yaml")
                or file.lower().endswith(f"{filename}.yml")
            ]
        pool = multiprocessing.Pool()
        results = pool.map(
            partial(
                validate,
                filename=filename,
                key_yaml=key_yaml,
                logical_validation=logical_validation,
                whitelist_path=whitelist_path,
                yaml=copy.deepcopy(key_yaml),
            ),
            items,
        )
        pool.close()
        for result in results:
            if result[3] == 0 or return_false:
                metafile_list.append(result[0])

            if result[1]:
                corrupt_count += 1
                file_reports.append(
                    {"file": result[0], "error": result[2], "warning": result[4]}
                )

            error_count += result[3]
            warning_count += result[5]
        return metafile_list, {
            "all_files": len(results),
            "corrupt_files": {"count": corrupt_count, "report": file_reports},
            "error_count": error_count,
            "warning_count": warning_count,
        }
    else:
        print("try running subprocess")
        import subprocess

        input_file = "func_params" + str(time.time_ns()) + ".json"
        output_file = "workaround" + str(time.time_ns()) + ".json"
        print(
            "input",
            os.path.abspath(os.path.join(os.path.dirname(__file__), input_file)),
            "output",
            os.path.abspath(os.path.join(os.path.dirname(__file__), output_file)),
        )
        print(key_yaml)
        print(path_metafiles)
        print("writing file now")
        with open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), input_file)), "w"
        ) as f:
            json.dump({"key_yaml": key_yaml, "path_metafiles": path_metafiles}, f)
        print("is this right", os.path.abspath(os.path.join(os.path.dirname(__file__))))
        process = subprocess.Popen(
            [
                "python",
                "run_file_reading.py",
                "--input",
                input_file,
                "--output",
                output_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__))),
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            with open(
                os.path.abspath(os.path.join(os.path.dirname(__file__), output_file)),
                "r",
            ) as f:
                output_dict = json.loads(f.read())
            print("Script ran successfully")
            return output_dict
        else:
            print(f"Error: {stderr.decode()}")
            return


def validate(ypath, filename, key_yaml, logical_validation, whitelist_path, yaml):
    error_reports = None
    warning_reports = None
    warning_count = False
    error_count = 0
    corrupted = False
    report = {}
    # add files with suffix '_metadata.y(a)ml'
    metafile = read_in_yaml(ypath)
    # test if metafile is valid
    (
        valid,
        missing_mandatory_keys,
        invalid_keys,
        invalid_entries,
        invalid_values,
        logical_warn,
    ) = validate_yaml.validate_file(
        metafile,
        key_yaml,
        filename,
        logical_validation=logical_validation,
        yaml=yaml,
        whitelist_path=whitelist_path,
    )
    # add path to dic
    metafile["path"] = ypath
    if not valid:
        error_reports = (
            missing_mandatory_keys,
            invalid_keys,
            invalid_entries,
            invalid_values,
        )
        corrupted = True
        error_count += (
            len(missing_mandatory_keys)
            + len(invalid_keys)
            + len(invalid_entries)
            + len(invalid_values)
        )

    if len(logical_warn) > 0:
        corrupted = True
        warning_count += len(logical_warn)
        warning_reports = logical_warn
    print(f"validated file {ypath}")
    return (
        metafile,
        corrupted,
        error_reports,
        error_count,
        warning_reports,
        warning_count,
    )
