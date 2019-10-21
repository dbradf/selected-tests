import os.path

from typing import Any, Set
from git import Repo, Commit, Diff

import structlog
from structlog.stdlib import LoggerFactory


structlog.configure(logger_factory=LoggerFactory())
GITHUB_BASE_URL = "https://github.com"


def init_repo(temp_dir, repo_name: str, branch: str, org_name: str = "mongodb") -> Repo:
    """
    Create the given repo in the given directory and checkout the given branch.

    :param temp_dir: The place where to clone the repo to.
    :param org_name: The org name in github that owns the repo.
    :param repo_name: The name of the repo to clone.
    :param branch: The branch to checkout in the repo.
    :return: An Repo instance that further git operations can be done on.
    """
    repo_path = os.path.join(temp_dir, repo_name)
    url = f"{GITHUB_BASE_URL}/{org_name}/{repo_name}.git"
    repo = Repo.clone_from(url, repo_path, branch=branch)
    return repo


def _paths_for_iter(diff: Diff, iter_type: str):
    """
    Get the set for all the files in the given diff for the specified type.

    :param diff: git diff to query.
    :param iter_type: Iter type ['M', 'A', 'R', 'D'].
    :return: set of changed files.
    """
    a_path_changes = {change.a_path for change in diff.iter_change_type(iter_type)}
    b_path_changes = {change.b_path for change in diff.iter_change_type(iter_type)}
    return a_path_changes.union(b_path_changes)


def modified_files_for_commit(commit: Commit, log: Any) -> Set:
    if not commit.parents:
        return {}

    parent = commit.parents[0]
    diff = commit.diff(parent)

    modified_files = _paths_for_iter(diff, "M")
    log.debug("modified files", files=modified_files)

    added_files = _paths_for_iter(diff, "A")
    log.debug("added files", files=added_files)

    renamed_files = _paths_for_iter(diff, "R")
    log.debug("renamed files", files=renamed_files)

    deleted_files = _paths_for_iter(diff, "D")
    log.debug("deleted files", files=deleted_files)

    return modified_files.union(added_files).union(renamed_files).union(deleted_files)