import os
import shutil
import git
import re
from urllib.parse import quote, urlsplit, urlunsplit


def get_whitelists(
    whitelist_path, whitelist_repo, whitelist_branch, update_whitelist, name=None, token=None
):
    """
    This function clones the whitelist repository. If the repository already
    exists then it pulls the most recent changes. If the local clone belongs
    to a different repository than the one configured (e.g. after changing
    whitelist_repository in the config), the stale clone is discarded and
    re-cloned from scratch. If name/token are given, they are used to
    authenticate against private repositories over HTTP(S).
    """
    auth_repo = _authenticated_url(whitelist_repo, name, token)

    if os.path.exists(whitelist_path) and _is_stale_clone(whitelist_path, whitelist_repo):
        print(
            f"Local whitelist clone at '{whitelist_path}' does not match "
            f"configured repository '{whitelist_repo}', re-cloning...\n"
        )
        shutil.rmtree(whitelist_path)

    if not os.path.exists(whitelist_path) or update_whitelist:

        print("Fetching whitelists...\n")

        if not os.path.exists(whitelist_path):
            repo = git.Repo.clone_from(auth_repo, whitelist_path)
            whitelist_branch = get_branch(repo, whitelist_branch)
            repo.git.checkout(whitelist_branch)
        else:
            repo = git.Repo(whitelist_path)
            repo.remotes.origin.set_url(auth_repo)
            repo.remotes.origin.fetch(prune=True, prune_tags=True)
            whitelist_branch = get_branch(repo, whitelist_branch)
            repo.git.checkout(whitelist_branch)
            repo.remotes.origin.pull(whitelist_branch)

        print(f"Fetched branch {whitelist_branch}.\n")
    else:
        repo = git.Repo(whitelist_path)
        repo.remotes.origin.set_url(auth_repo)
        repo.remotes.origin.fetch(prune=True, prune_tags=True)
        whitelist_branch = get_branch(repo, whitelist_branch)
    return whitelist_branch


def _authenticated_url(url, name, token):
    """Embeds name/token into an http(s) URL for git authentication."""
    if not name or not token:
        return url
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return url
    netloc = f"{quote(name, safe='')}:{quote(token, safe='')}@{parts.hostname}"
    if parts.port:
        netloc += f":{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _strip_credentials(url):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or "@" not in parts.netloc:
        return url
    netloc = parts.hostname
    if parts.port:
        netloc += f":{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _is_stale_clone(whitelist_path, whitelist_repo):
    def normalize(url):
        url = _strip_credentials(url)
        return url.rstrip("/")[: -len(".git")] if url.rstrip("/").endswith(".git") else url.rstrip("/")

    try:
        repo = git.Repo(whitelist_path)
        return normalize(repo.remotes.origin.url) != normalize(whitelist_repo)
    except (git.InvalidGitRepositoryError, AttributeError, IndexError):
        return True


def get_branch(repo, whitelist_branch):
    if "*" in whitelist_branch:
        regex_branch = (
            whitelist_branch.replace(".", "\.")
            .replace("$", "\$")
            .replace("+", "\+")
            .replace("*", ".*")
        )
        branch_list = [
            a.name.replace("origin/", "")
            for a in repo.tags + repo.remote().refs
            if a.name != "origin/HEAD"
        ]
        matching_branches = [
            x.lstrip("v").split(".")
            for x in branch_list
            if re.search(f"^{regex_branch}$", x) is not None
        ]
        splitted_branches = []
        for branch in matching_branches:
            try:
                splitted_branches.append([int(x) for x in branch])
            except ValueError:
                pass
        splitted_branches.sort(reverse=True)
        whitelist_branch = f'v{".".join([str(s) for s in splitted_branches[0]])}'
    return whitelist_branch
