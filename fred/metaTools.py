import argparse
import copy
import pathlib

from src.generate import Generate
import os
from src import find_metafiles
from src import validate_yaml
from src import file_reading
from src import utils
from src import git_whitelists
from src.heatmap import create_heatmap
import time


class FRED:

    def __init__(self, config, skip_validation=False):
        self.whitelist_repo, self.whitelist_branch, self.whitelist_path, \
        self.username, self.password, structure, self.update_whitelists, \
        self.output_path, self.filename, self.email = utils.parse_config(config)
        if not skip_validation:
            self.fetch_whitelists()
        self.structure = utils.read_in_yaml(structure)

    def fetch_whitelists(self):
        git_whitelists.get_whitelists(self.whitelist_path, self.whitelist_repo, self.whitelist_branch, self.update_whitelists)

    def find(self, search_path, search, output, output_filename, skip_validation):
        result = find_metafiles.find_projects(self.structure, search_path,
                                              search, True, skip_validation)
        if output == 'print':
            if len(result) > 0:

                # print summary of matching files
                print(find_metafiles.print_summary(result, output))

            else:

                # print information that there are no matching files
                print('No matches found')
        elif output == 'json':
            if not output_filename:
                output_filename = 'search_result'
            json_filename = f'{output_filename}.json'
            utils.save_as_json({'data': find_metafiles.print_summary(result, output)}, json_filename)
            print(
                f'The report was saved to the file \'{json_filename}\'.')

    def generate(self, path, project_id, mandatory_only):
        gen = Generate(path, project_id, mandatory_only, self.filename, self.structure, self.email)
        gen.generate()

    def validate(self, logical_validation, path, output, output_filename, save_empty=False):
        validation_reports = {'all_files': 1,
                              'corrupt_files': {'count': 0, 'report': []},
                              'error_count': 0, 'warning_count': 0}
        if os.path.isdir(path):
            metafiles, validation_reports = file_reading.iterate_dir_metafiles(
                self.structure, [path], filename=self.filename,
                logical_validation=logical_validation, yaml=copy.deepcopy(self.structure),
                whitelist_path=self.whitelist_path)
        else:
            metafile = utils.read_in_yaml(path)
            file_reports = {'file': metafile, 'error': None, 'warning': None}
            valid, missing_mandatory_keys, invalid_keys, \
            invalid_entries, invalid_values, logical_warn = validate_yaml.validate_file(
                metafile, self.structure, self.filename,
                logical_validation=logical_validation, yaml=copy.deepcopy(self.structure),
                whitelist_path=self.whitelist_path)
            metafile['path'] = path
            if not valid:
                validation_reports['corrupt_files']['count'] = 1
                validation_reports['error_count'] += (
                            len(missing_mandatory_keys) + len(
                        invalid_keys) + len(invalid_entries) + len(
                        invalid_values))
                file_reports['error'] = (
                missing_mandatory_keys, invalid_keys, invalid_entries,
                invalid_values)
            if len(logical_warn) > 0:
                validation_reports['corrupt_files']['count'] = 1
                validation_reports['warning_count'] += len(logical_warn)
                file_reports['warning'] = logical_warn
            validation_reports['corrupt_files']['report'].append(file_reports)

        print(f'{validation_reports["all_files"]} files were validated.')
        print(
            f'Found {validation_reports["error_count"]} errors and {validation_reports["warning_count"]} warnings in {validation_reports["corrupt_files"]["count"]} of those files.')

        if validation_reports['corrupt_files']['count'] > 0 or save_empty is True:

            res = None
            if output is not None:
                if output == 'print':
                    res = ['print report']
                elif output == 'txt':
                    res = ['save report to txt file']
                elif output == 'json':
                    res = ['save report to json file']
                elif output == 'yaml':
                    res = ['save report to yaml file']
            else:
                options = ['print report', 'save report to txt file',
                           'save report to json file',
                           'save report to yaml file']
                print(
                    f'Do you want to see a report? Choose from the following options (1,...,{len(options)} or n)')
                ask = Generate('', '', False, self.filename, self.structure, self.email)
                ask.print_option_list(options, '')
                res = ask.parse_input_list(options, True)

            try:
                output_report = {
                    'report': copy.deepcopy(validation_reports)['corrupt_files']['report']}
            except KeyError:
                output_report = {'report': []}
            for elem in output_report['report']:
                id = list(utils.find_keys(elem['file'], 'id'))
                if len(id) > 0:
                    elem['id'] = id[0]
                else:
                    elem['id'] = 'missing'
                elem['path'] = elem['file']['path']
                errors = list(elem['error']) if 'error' in elem and elem[
                    'error'] is not None else []
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
                            elem['warning'][
                                i] = f'{elem["warning"][i][0]}: {elem["warning"][i][1]}'
                    else:
                        elem.pop('warning')

            if res is not None:
                if output_filename is None:
                    timestamp = time.time()
                    output_filename = f'validation_report_{str(timestamp).split(".")[0]}'

                rep = ''
                for report in validation_reports['corrupt_files']['report']:
                    rep += f'{"".center(80, "_")}\n\n'
                    rep += validate_yaml.print_full_report(report['file'],
                                                           report['error'],
                                                           report['warning'])
                rep += f'{"".center(80, "_")}\n\n'

                if 'save report to txt file' in res:
                    txt_filename = f'{output_filename}.txt'
                    txt_f = open(txt_filename, 'w')
                    txt_f.write(rep)
                    print(
                        f'The report was saved to the file \'{txt_filename}\'.')
                    txt_f.close()

                if 'save report to json file' in res:
                    json_filename = f'{output_filename}.json'
                    utils.save_as_json(output_report, json_filename)
                    print(
                        f'The report was saved to the file \'{json_filename}\'.')

                if 'save report to yaml file' in res:
                    yaml_filename = f'{output_filename}.yaml'
                    utils.save_as_yaml(output_report, yaml_filename)
                    print(
                        f'The report was saved to the file \'{yaml_filename}\'.')

                if 'print report' in res:
                    print(rep)

        return validation_reports["error_count"], validation_reports["warning_count"]

    #def edit(self, path, mandatory_only):
    #    try:
    #        size = os.get_terminal_size()
    #        size = size.columns
    #    except OSError:
    #        size = 80

    #    edit_file.edit_file(path, self.filename, mandatory_only, size)

    def add_value(self, path, position, value, edit_existing):
        files, errors = file_reading.iterate_dir_metafiles(self.structure,
                                                           [path],
                                                           self.filename, False,
                                                           return_false=True,
                                                           whitelist_path=
                                                           self.whitelist_path)
        position = position.split(':')
        # TODO: type
        for file in files:
            file = utils.add_value_at_pos(self.structure, file, position, value,
                                          edit_existing)
            save_path = file['path']
            file.pop('path')
            print(f'edited file {save_path}')
            utils.save_as_yaml(file, save_path)

def find(args):
    """
    calls script find_metafiles to find matching files and print results
    :param args:
        path: a path of a folder that should be searched for metadata files
        search: a string specifying search parameters linked via 'and', 'or'
                and 'not'
    """
    finding = FRED(args.config, args.skip_validation)
    finding.find(args.path, args.search, args.output, args.filename,
                 args.skip_validation)


def generate(args):
    """
    calls script generate_metafile to start dialog
    :param args:
    """
    generating = FRED(args.config)
    generating.generate(args.path, args.id, args.mandatory_only)


def validate(args):
    validating = FRED(args.config)
    errors, warnings = validating.validate(not args.skip_logic, args.path, args.output, args.filename)


def plot(args):
    fred_object = FRED(args.config)
    input_file = utils.read_in_yaml(args.path)
    plots = create_heatmap.get_heatmap(input_file, fred_object.structure, mode=args.mode, labels=args.labels)
    output_filename = args.filename if args.filename is not None else 'fig1'
    if len(plots) > 0:
        try:
            plot = plots[args.setting-1][1]
        except IndexError:
            print(f'Setting exp{args.index} does not exist. Defaulting to exp1.')
            plot = plots[0][1]
        
        if plot is not None:
            if args.output == 'png':
                plot.write_image(f'{output_filename}.{args.output}', format='png')
                print(f'Plot was saved to {output_filename}.{args.output}')
            elif args.output == 'html':
                with open(f'{output_filename}.{args.output}', 'w') as file:
                    file.write(plot.to_html(full_html=False, include_plotlyjs='cdn'))
                print(f'Plot was saved to {output_filename}.{args.output}')
            else:
                plot.show()
        else:
            print('Plot could not be created due to missing samples or conditions.')
    else:
        print('No settings found.')

#def edit(args):
#    editing = FRED(args.config)
#    editing.edit(args.path, args.mandatory_only)

def add_value(args):
    adding = FRED(args.config)
    adding.add_value(args.path, args.position, args.value, args.edit_existing)

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
    find_group.add_argument('-c', '--config', type=pathlib.Path,
                              help='Config file', default=os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
    find_group.add_argument('-o', '--output', default='print', choices=['json', 'print'])
    find_group.add_argument('-f', '--filename', default=None)
    find_group.add_argument('-sv', '--skip_validation', default=False,
                            action='store_true')
    find_function.set_defaults(func=find)

    create_function = subparsers.add_parser('generate',
                                            help='This command is used to '
                                                 'create a metadata file.')
    create_group = create_function.add_argument_group('mandatory arguments')
    create_group.add_argument('-p', '--path', type=pathlib.Path,
                                 required=True,
                                 help='The path to save the yaml')
    create_group.add_argument('-c', '--config', type=pathlib.Path,
                              help='Config file', default=os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
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
    validate_function.add_argument('-f', '--filename', default=None)
    validate_function.add_argument('-c', '--config', type=pathlib.Path,
                              help='Config file', default=os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
    validate_function.set_defaults(func=validate)

    #edit_function = subparsers.add_parser('edit', help='')
    #edit_group = edit_function.add_argument_group('mandatory_arguments')
    #edit_group.add_argument('-p', '--path', type=pathlib.Path, required=True)
    #edit_function.add_argument('-mo', '--mandatory_only', default=False,
    #                             action='store_true',
    #                             help='If True, only mandatory keys will '
    #                                  'be filled out')
    #edit_function.add_argument('-c', '--config', type=pathlib.Path,
    #                          help='Config file', default='config.yaml')
    #edit_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    #edit_function.set_defaults(func=edit)

    add_value_function = subparsers.add_parser('add_value', help='')
    add_value_function.add_argument('-m', '--mode', default='metadata', choices=['metadata', 'mamplan'])
    add_value_function.add_argument('-pos', '--position', required=True)
    add_value_function.add_argument('-v', '--value', required=True)
    add_value_function.add_argument('-t', '--type', default='str', choices=['str', 'int', 'float', 'bool'])
    add_value_function.add_argument('-p', '--path', type=pathlib.Path, required=True)
    add_value_function.add_argument('-e', '--edit_existing', default=False, action='store_true')
    add_value_function.add_argument('-c', '--config', type=pathlib.Path,
                              help='Config file', default=os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
    add_value_function.set_defaults(func=add_value)

    plot_function = subparsers.add_parser('plot', help='')
    plot_function.add_argument('-p', '--path', type=pathlib.Path, required=True)
    plot_function.add_argument('-c', '--config', type=pathlib.Path,
                              help='Config file', default=os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
    plot_function.add_argument('-m', '--mode', default='samples', choices=['samples', 'conditions'])
    plot_function.add_argument('-s', '--setting', type=int, default=1)
    plot_function.add_argument('-l', '--labels', default='factors', choices=['factors', 'all', 'none'])
    plot_function.add_argument('-o', '--output', default='show', choices=['show', 'png', 'html', 'dash'])
    plot_function.add_argument('-f', '--filename', type=pathlib.Path)
    plot_function.set_defaults(func=plot)

    args = parser.parse_args()

    try:
        args.func(args)
    except AttributeError as e:
        print(e)
        parser.print_help()


if __name__ == "__main__":

    main()
