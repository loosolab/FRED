import os
import git
import re

#TODO: username, pw
def get_whitelists(whitelist_path, whitelist_repo, whitelist_branch, update_whitelist):
    """
    This function clones the whitelist repository. If the repository already
    exists then it pulls the most recent changes
    """
    if not os.path.exists(whitelist_path) or update_whitelist:

        print('Fetching whitelists...\n')

        if not os.path.exists(whitelist_path):
            repo = git.Repo.clone_from(whitelist_repo,
                                   whitelist_path)
            whitelist_branch = get_branch(repo, whitelist_branch)
            repo.git.checkout(whitelist_branch)
        else:
            repo = git.Repo(whitelist_path)
            repo.remotes.origin.fetch(prune=True, prune_tags=True)
            whitelist_branch = get_branch(repo, whitelist_branch)
            repo.git.checkout(whitelist_branch)
            repo.remotes.origin.pull(whitelist_branch)

        print(f'Fetched branch {whitelist_branch}.\n')
    else:
        repo = git.Repo(whitelist_path)
        repo.remotes.origin.fetch(prune=True, prune_tags=True)
        whitelist_branch = get_branch(repo, whitelist_branch)
    return whitelist_branch


def get_branch(repo, whitelist_branch):
    if '*' in whitelist_branch:
        regex_branch = whitelist_branch.replace(".", "\.").replace("$", "\$").replace("+", "\+").replace("*", ".*")
        branch_list = [a.name.replace('origin/', '') for a in repo.tags + repo.remote().refs if a.name != 'origin/HEAD']
        matching_branches = [x.lstrip('v').split('.') for x in branch_list if re.search(f'^{regex_branch}$', x) is not None]
        splitted_branches = []
        for branch in matching_branches:
            try:
                splitted_branches.append([int(x) for x in branch])
            except ValueError:
                pass
        splitted_branches.sort(reverse=True)
        whitelist_branch = f'v{".".join([str(s) for s in splitted_branches[0]])}'
    return whitelist_branch