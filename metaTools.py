import argparse
import copy
import pathlib
import time

import git
import os
from src import generate_metafile
from src import generate_file
from src import find_metafiles
from src import validate_yaml
from src import file_reading
from src import edit_file
from src import utils


def find(args):
    """
    calls script find_metafiles to find matching files and print results
    :param args:
        path: a path of a folder that should be searched for metadata files
        search: a string specifying search parameters linked via 'and', 'or'
                and 'not'
    """

    # call function find_projects in find_metafiles
    fetch_whitelists()
    result = find_metafiles.find_projects(args.path, args.search, True)

    # test if matching metadata files were found
    if len(result) > 0:

        # print summary of matching files
        print(find_metafiles.print_summary(result))

    else:

        # print information that there are no matching files
        print('No matches found')


def generate(args):
    """
    calls script generate_metafile to start dialog
    :param args:
    """
    try:
        size = os.get_terminal_size()
        size = size.columns
    except OSError:
        size = 80

    fetch_whitelists()
    generate_file.generate_file(args.path, args.id,
                                    args.mandatory_only, args.mode, size=size)


def validate(args):
    fetch_whitelists()
    logical_validation = False if args.skip_logic else True
    validation_reports = {'all_files': 1,
                          'corrupt_files': {'count': 0, 'report':[]},
                          'error_count': 0, 'warning_count': 0}
    structure_yaml = 'keys.yaml' if args.mode == 'metadata' else 'mamplan_keys.yaml'
    if os.path.isdir(args.path):
        metafiles, validation_reports = file_reading.iterate_dir_metafiles([args.path], mode=args.mode, logical_validation=logical_validation, yaml=structure_yaml)
    else:
        metafile = utils.read_in_yaml(args.path)
        file_reports = {'file': metafile, 'error': None, 'warning': None}
        valid, missing_mandatory_keys, invalid_keys, \
        invalid_entries, invalid_values, logical_warn = validate_yaml.validate_file(metafile, args.mode, logical_validation=logical_validation, yaml=structure_yaml)
        metafile['path'] = args.path
        if not valid:
            validation_reports['corrupt_files']['count'] = 1
            validation_reports['error_count'] += (len(missing_mandatory_keys) + len(invalid_keys) + len(invalid_entries) + len(invalid_values))
            file_reports['error'] = (missing_mandatory_keys, invalid_keys, invalid_entries, invalid_values)
        if len(logical_warn) > 0:
            validation_reports['corrupt_files']['count'] = 1
            validation_reports['warning_count'] += len(logical_warn)
            file_reports['warning'] = logical_warn
        validation_reports['corrupt_files']['report'].append(file_reports)

    print(f'{validation_reports["all_files"]} files were validated.')
    print(f'Found {validation_reports["error_count"]} errors and {validation_reports["warning_count"]} warnings in {validation_reports["corrupt_files"]["count"]} of those files.')

    if validation_reports['corrupt_files']['count'] > 0:

        if args.output is not None:
            if args.output == 'print':
                res = ['print report']
            elif args.output == 'txt':
                res = ['save report to txt file']
            elif args.output == 'json':
                res = ['save report to json file']
            elif args.output == 'yaml':
                res = ['save report to yaml file']
        else:
            options = ['print report', 'save report to txt file', 'save report to json file', 'save report to yaml file']
            print(f'Do you want to see a report? Choose from the following options (1,...,{len(options)} or n)')
            generate_metafile.print_option_list(options, '')
            res = generate_metafile.parse_input_list(options, True)

        output_report = {'report': copy.deepcopy(validation_reports)['corrupt_files']['report']}
        for elem in output_report['report']:
            id = list(utils.find_keys(elem['file'], 'id'))
            if len(id) > 0:
                elem['id'] = id[0]
            else:
                elem['id'] = 'missing'
            elem['path'] = elem['file']['path']
            errors = list(elem['error']) if 'error' in elem is not None else []
            elem['error'] = {}
            elem.pop('file')
            for i in range(len(errors)):

                if len(errors[i]) > 0:
                    if i == 0:
                        elem['error']['missing_mandatory_keys'] = errors[i]
                    elif i == 1:
                        elem['error']['invalid_keys'] = errors[i]
                    elif i == 2:
                        whitelist_values = []
                        for v in errors[i]:
                            key = ':'.join(v.split(':')[:-1])
                            entry = v.split(':')[-1]
                            whitelist_values.append(
                                entry + ' in ' + key + '\n')
                        elem['error']['invalid_entries'] = whitelist_values
                    elif i == 3:
                        value = []
                        for v in errors[i]:
                            value.append(f'{v[0]}: {v[1]} -> {v[2]}')
                        elem['error']['invalid_values'] = value

            if 'warning' in elem:
                if elem['warning'] is not None:
                    for i in range(len(elem['warning'])):
                        elem['warning'][i] = f'{elem["warning"][i][0]}: {elem["warning"][i][1]}'
                else:
                    elem.pop('warning')

        if res:
            timestamp = time.time()

            if 'save report to txt file' in res:
                txt_filename = f'validation_report_{str(timestamp).split(".")[0]}.txt'
                txt_f = open(txt_filename, 'w')

            rep = ''
            for report in validation_reports['corrupt_files']['report']:
                rep += f'{"".center(80, "_")}\n\n'
                rep += validate_yaml.print_full_report(report['file'], report['error'], report['warning'])
            rep += f'{"".center(80, "_")}\n\n'

            if 'save report to txt file' in res:
                txt_f.write(rep)
                print(f'The report was saved to the file \'{txt_filename}\'.')
                txt_f.close()

            if 'save report to json file' in res:
                json_filename = f'validation_report_{str(timestamp).split(".")[0]}.json'
                utils.save_as_json(output_report, json_filename)
                print(f'The report was saved to the file \'{json_filename}\'.')

            if 'save report to yaml file' in res:
                yaml_filename = f'validation_report_{str(timestamp).split(".")[0]}.yaml'
                utils.save_as_yaml(output_report, yaml_filename)
                print(f'The report was saved to the file \'{yaml_filename}\'.')

            if 'print report' in res:
                print(rep)

def edit(args):
    try:
        size = os.get_terminal_size()
        size = size.columns
    except OSError:
        size = 80

    edit_file.edit_file(args.path, args.mode, args.mandatory_only, size)


def fetch_whitelists():
    print('Fetching whitelists...\n')
    if not os.path.exists('metadata_whitelists'):
        repo = git.Repo.clone_from(
            'https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.git/',
            'metadata_whitelists')
    else:
        repo = git.Repo('metadata_whitelists')
        o = repo.remotes.origin
        o.pull()


def main():
    parser = argparse.ArgumentParser(prog='metaTools.py')
    subparsers = parser.add_subparsers(title='commands')

    find_function = subparsers.add_parser('find',
                                          help='This command is used to find '
                                               'projects by searching the '
                                               'metadata files.')

    find_group = find_function.add_argument_group('mandatory arguments')
    find_group.add_argument('-p', '--path', type=pathlib.Path, required=True,
                               help='The path to be searched')
    find_group.add_argument('-s', '--search', type=str, required=True,
                               help='The search parameters')
    find_function.set_defaults(func=find)

    create_function = subparsers.add_parser('generate',
                                            help='This command is used to '
                                                 'create a metadata file.')
    create_group = create_function.add_argument_group('mandatory arguments')
    create_group.add_argument('-p', '--path', type=pathlib.Path,
                                 required=True,
                                 help='The path to save the yaml')
    create_group.add_argument('-id', '--id', type=str,
                                 required=True,
                                 help='The ID of the experiment')
    create_function.add_argument('-mo', '--mandatory_only', default=False,
                                 action='store_true',
                                 help='If True, only mandatory keys will '
                                      'be filled out')
    create_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    create_function.set_defaults(func=generate)

    validate_function = subparsers.add_parser('validate',
                                              help='')
    validate_group = validate_function.add_argument_group('mandatory arguments')
    validate_group.add_argument('-p', '--path', type=pathlib.Path, required=True)
    validate_function.add_argument('-l', '--skip_logic', default=False,
                                   action='store_true')
    validate_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    validate_function.add_argument('-o', '--output', default=None, choices=['json', 'txt', 'print', 'yaml'])
    validate_function.set_defaults(func=validate)

    edit_function = subparsers.add_parser('edit', help='')
    edit_group = edit_function.add_argument_group('mandatory_arguments')
    edit_group.add_argument('-p', '--path', type=pathlib.Path, required=True)
    edit_function.add_argument('-mo', '--mandatory_only', default=False,
                                 action='store_true',
                                 help='If True, only mandatory keys will '
                                      'be filled out')
    edit_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    edit_function.set_defaults(func=edit)

    args = parser.parse_args()

    try:
        args.func(args)
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":

    main()
