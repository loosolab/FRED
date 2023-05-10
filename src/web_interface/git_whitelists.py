import os
import git


def get_whitelists():

    if not os.path.exists(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..',
            'metadata_whitelists')):
        repo = git.Repo.clone_from(
            'https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.'
            'git/',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                         'metadata_whitelists'))
    else:
        repo = git.Repo(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                         'metadata_whitelists'))
        o = repo.remotes.origin
        o.pull()