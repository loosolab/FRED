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
    generate_metafile.generate_file(args.path, args.id, args.name,
                                    args.mandatory_only)


def validate(args):
    logical_validation = False if args.skip_logic else True
    validation_reports = {'errors': {'count': 0, 'report': []},
                          'warnings': {'count': 0, 'report': []}}
    if os.path.isdir(args.path):
        metafiles, validation_reports = file_reading.iterate_dir_metafiles([args.path], mode=args.mode, logical_validation=logical_validation, yaml=args.yaml)
    else:
        metafile = utils.read_in_yaml(args.path)
        valid, missing_mandatory_keys, invalid_keys, \
        invalid_entries, invalid_values, logical_warn = validate_yaml.validate_file(metafile, args.mode, logical_validation=logical_validation, yaml=args.yaml)
        metafile['path'] = args.path
        if not valid:
            validation_reports['errors']['count'] += 1
            validation_reports['errors']['report'].append((metafile, missing_mandatory_keys, invalid_keys, invalid_entries, invalid_values))
        if len(logical_warn) > 0:
            validation_reports['warnings']['count'] += 1
            validation_reports['warnings']['report'].append((metafile, logical_warn))

    print(f'Found {validation_reports["errors"]["count"]} errors and {validation_reports["warnings"]["count"]} warnings.')
    res = []
    if validation_reports['errors']['count'] > 0 or validation_reports['warnings']['count'] > 0:
        options = ['print report', 'save report to file']
        print(f'Do you want to see a report? Choose from the following options (1,...,{len(options)} or n)')
        generate_metafile.print_option_list(options, '')
        res = generate_metafile.parse_input_list(options, True)
    if 'save report to file' in res:
        timestamp = time.time()
        filename = f'validation_report_{str(timestamp).split(".")[0]}.txt'
        f = open(filename, 'w')

    if validation_reports['errors']['count'] > 0:
        for rep in validation_reports['errors']['report']:
            report = validate_yaml.print_validation_report(rep[0], rep[1], rep[2], rep[3], rep[4])
            if 'save report to file' in res:
                f.write(report)
            if 'print report' in res:
                print(report)
    if validation_reports['warnings']['count'] > 0:
        for rep in validation_reports['warnings']['report']:
            report = validate_yaml.print_warning(rep[0], rep[1])
            if 'save report to file' in res:
                f.write(report)
            if 'print report' in res:
                print(report)
    if 'save report to file' in res:
        print(f'The report was saved to the file \'{filename}\'.')
        f.close()


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
    create_group.add_argument('-n', '--name', type=str,
                                 required=True,
                                 help='The name of the experiment')
    create_function.add_argument('-mo', '--mandatory_only', default=False,
                                 action='store_true',
                                 help='If True, only mandatory keys will '
                                      'be filled out')
    create_function.set_defaults(func=generate)

    validate_function = subparsers.add_parser('validate',
                                              help='')
    validate_group = validate_function.add_argument_group('mandatory arguments')
    validate_group.add_argument('-p', '--path', type=pathlib.Path, required=True)
    validate_function.add_argument('-l', '--skip_logic', default=False,
                                   action='store_true')
    validate_function.add_argument('-y', '--yaml', type=pathlib.Path, default='keys.yaml')
    validate_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    validate_function.set_defaults(func=validate)

    args = parser.parse_args()

    try:
        args.func(args)
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":

    print('Fetching whitelists...\n')
    if not os.path.exists('metadata_whitelists'):
        repo = git.Repo.clone_from('https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.git/', 'metadata_whitelists')
    else:
        repo = git.Repo('metadata_whitelists')
        o = repo.remotes.origin
        o.pull()

    main()
