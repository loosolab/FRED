import argparse
import pathlib
from src import file_reading
from src import find_metafiles

def find(args):
    search_parameters = args.search.split('or')
    for i in range(len(search_parameters)):
        search_parameters[i] = search_parameters[i].split('and')
        for j in range(len(search_parameters[i])):
            should_be_in = True
            if 'not' in search_parameters[i][j]:
                should_be_in = False
                search_parameters[i][j] = search_parameters[i][j].\
                    replace('not','')
            search_parameters[i][j] = search_parameters[i][j].strip() + \
                                      (':'+str(should_be_in))
    print(search_parameters)

    metafiles = file_reading.iterate_dir_metafiles([args.path])
    ids = find_metafiles.find_projects(metafiles, search_parameters)
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
    add_function.set_defaults(func=add)
    create_function = subparsers.add_parser('create',
                                            help='This command is used to '
                                                 'create a metadata file.')
    create_function.set_defaults(func=create)
    args= parser.parse_args()
    args.func(args)

if __name__=="__main__":
    main()