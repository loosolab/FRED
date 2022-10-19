import argparse
import pathlib
from src import metaTools_functions
from src import generate_metafile
from src import find_metafiles

def find(args):
    """
    calls src.metaTools_functions.find to find matching yaml
    :param args:
    path: a path containing metadata yaml
    search: a string specifying search parameters linked via 'and', 'or' and
    'not'
    """
    result = metaTools_functions.find(args.path, args.search, True)
    if len(result) > 0:
        print(find_metafiles.print_summary(result))
    else:
        print('No matches found')


def generate(args):
    generate_metafile.generate_file(args.path, args.id, args.name, args.mandatory_only)


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
    create_function.add_argument('-mo', '--mandatory_only', default=False, action='store_true',
                                 help='If True, only mandatory keys will be filled out')

    create_function.set_defaults(func=generate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
