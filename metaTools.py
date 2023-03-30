import argparse
import pathlib
import time

import git
import os
from src import generate_metafile
from src import find_metafiles
from src import validate_yaml
from src import file_reading
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
    fetch_whitelists()
    generate_metafile.generate_file(args.path, args.id,
                                    args.mandatory_only, args.mode)


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
        options = ['print report', 'save report to file']
        print(f'Do you want to see a report? Choose from the following options (1,...,{len(options)} or n)')
        generate_metafile.print_option_list(options, '')
        res = generate_metafile.parse_input_list(options, True)
        if res:
            if 'save report to file' in res:
                timestamp = time.time()
                filename = f'validation_report_{str(timestamp).split(".")[0]}.txt'
                f = open(filename, 'w')

            rep = ''
            for report in validation_reports['corrupt_files']['report']:
                rep += f'{"".center(80, "_")}\n\n'
                rep += validate_yaml.print_full_report(report['file'], report['error'], report['warning'])
            rep += f'{"".center(80, "_")}\n\n'

            if 'print report' in res:
                print(rep)
            if 'save report to file' in res:
                f.write(rep)
                print(f'The report was saved to the file \'{filename}\'.')
                f.close()


def edit(args):
    if args.mode == 'metadata':
        key_yaml = utils.read_in_yaml(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'keys.yaml'))
    else:
        key_yaml = utils.read_in_yaml(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'mamplan_keys.yaml'))
    file = utils.read_in_yaml(args.path)
    options = [key for key in key_yaml]
    print(f'Choose the parts you want to edit (1,...,{len(options)}) divided by comma.\n')
    generate_metafile.print_option_list(options, False)
    edit_keys = generate_metafile.parse_input_list(options, True)
    for key in edit_keys:
        if key in file:
            file[key] = generate_metafile.edit_item(key, file[key], key_yaml[key], file, args.mandatory_only, args.mode)
        else:
            file[key] = generate_metafile.get_redo_value(key_yaml[key], key, True, args.mandatory_only, file, True, False, True, args.mode)

        while True:
            print(generate_metafile.get_summary(file[key]))
            correct = generate_metafile.parse_list_choose_one(
                ['True ', 'False '], f'\nIs the input correct? You can redo '
                                     f'it by selecting \'False\'')
            if correct:
                break
            else:
                file[key] = generate_metafile.edit_item(key, file[key],
                                              key_yaml[key], file,
                                              args.mandatory_only, args.mode)
    utils.save_as_yaml(file, args.path)
    print(f'Changes were saved to {args.path}')


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
