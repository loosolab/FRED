import argparse
import pathlib
import git
import os
from src import generate_metafile
from src import find_metafiles

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
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":

    if not os.path.exists('metadata_whitelists'):
        git.Repo.clone_from('https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.git/', 'metadata_whitelists')
    else:
        repo = git.Repo('metadata_whitelists')
        o = repo.remotes.origin
        o.pull()

    main()
