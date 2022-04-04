import argparse
import pathlib
from src import metaTools_functions


def find(args):
    """
    calls src.metaTools_functions.find to find matching yaml
    :param args:
    path: a path containing metadata yaml
    search: a string specifying search parameters linked via 'and', 'or' and
    'not'
    """
    ids = metaTools_functions.find(args.path, args.search, False)
    print(ids)


def add(args):
    print('TBA')


def create(args):
    print('TBA')


def main():
    parser = argparse.ArgumentParser(prog='metaTools.py')
    subparsers = parser.add_subparsers(title='commands')

    find_function = subparsers.add_parser('find',
                                          help='This command is used to find '
                                               'projects by searching the '
                                               'metadata files.')

    find_function.add_argument('-p', '--path', type=pathlib.Path,
                               help='The path to be searched')
    find_function.add_argument('-s', '--search', type=str,
                               help='The search parameters')
    find_function.set_defaults(func=find)
    add_function = subparsers.add_parser('add',
                                         help='This command is used to add '
                                              'informtion to a metadata file.')
    add_function.add_argument('-p', '--path', type=pathlib.Path,
                              help='The path of the yaml')
    add_function.add_argument('-a', '--add', type=str, nargs='+',
                              help='The parameters to be added')
    add_function.set_defaults(func=add)
    create_function = subparsers.add_parser('create',
                                            help='This command is used to '
                                                 'create a metadata file.')
    create_function.add_argument('-p', '--path', type=pathlib.Path,
                                 help='The path to save the yaml')
    add_function.add_argument('-d', '--dict', type=str, nargs='+',
                              help='The dictionary to be saved as yaml')
    create_function.set_defaults(func=create)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
