import os.path

from typing import Any, Set
from git import Repo, Commit

import structlog
from structlog.stdlib import LoggerFactory


structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.get_logger(__name__)
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def pull_remote_repo(repo: str, branch: str, owner: str = "mongodb"):
    repo_url = f"https://github.com/{owner}/{repo}"
    repo_destination_folder = repo
    project_folder = os.path.join(CURRENT_DIRECTORY, repo_destination_folder)
    if os.path.exists(project_folder):
        repo = Repo(project_folder)
        repo.remotes.origin.pull()
    else:
        repo = Repo.clone_from(repo_url, project_folder, branch=branch)
    return repo


def _paths_for_iter(diff, iter_type):
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
    parent = commit.parents[0] if commit.parents else None

    if not bool(parent):
        return {}

    diff = commit.diff(parent)

    modified_files = _paths_for_iter(diff, 'M')
    log.debug("modified files", files=modified_files)

    added_files = _paths_for_iter(diff, 'A')
    log.debug("added files", files=added_files)

    renamed_files = _paths_for_iter(diff, 'R')
    log.debug("renamed files", files=renamed_files)

    deleted_files = _paths_for_iter(diff, 'D')
    log.debug("deleted files", files=deleted_files)

    return modified_files.union(added_files).union(renamed_files).union(deleted_files)
