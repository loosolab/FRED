import os
import git


def get_whitelists():
    """
    This function clones the whitelist repository. If the repository already
    exists then it pulls the most recent changes
    """

    # metadata whitelist folder does not exist
    if not os.path.exists(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', '..', 'metadata_whitelists')):

        # clone the repository
        git.Repo.clone_from(
            'https://gitlab.gwdg.de/loosolab/software/metadata_whitelists.'
            'git/', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', '..', 'metadata_whitelists'))

    # repository was already cloned
    else:

        # set repo to the repository
        repo = git.Repo(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', '..', 'metadata_whitelists'))

        # set o to origin of the repository
        o = repo.remotes.origin

        # git pull
        o.pull()
