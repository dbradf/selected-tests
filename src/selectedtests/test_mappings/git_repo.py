from typing import Set

from git import Repo, Commit, DiffIndex

import structlog
from structlog.stdlib import LoggerFactory


structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.get_logger(__name__)


class GitRepo(object):
    """A git repository."""
    def __init__(self, repo: Repo):
        """
        Create a new GitRepo.
        :param repo: Repository representing repo.
        """
        self._repo = repo

    @classmethod
    def local_repo(cls, path):
        """
        Create a GitRepo for a local repository.
        :param path: Path to local repository.
        :return: GitRepo for local repository.
        """
        return cls(Repo(path))

    def head(self):
        return self._repo.head.commit

    def walk_commits(self, start_commit):
        """
        Walk the commits in the repository.

        :param start_commit: Commit to start walking.
        :return: Generator that walks commits.
        """
        for commit in self._repo.iter_commits(start_commit):
            yield GitCommit(commit)


class GitCommit(object):
    """A git commit object."""
    def __init__(self, commit: Commit):
        """
        Create an object representing a commit.

        :param commit: commit object.
        """
        self._commit = commit

    def summary(self):
        """
        Get a summary of the commit message.
        :return: Summary of commit message.
        """
        return self._commit.message.splitlines()[0]

    @property
    def commit_time(self):
        """
        Get the time the commit was created.
        :return: commit time.
        """
        return self._commit.committed_datetime

    @property
    def id(self):
        return self._commit.hexsha

    @property
    def parent(self):
        """
        Get the parent for this commit.

        Returns the first commit if this is a merge commit.
        :return: Parent of commit.
        """
        LOGGER.debug('getting parents', parents=self._commit.parents)
        return self._commit.parents[0]

    def diff_to_parent(self):
        """
        Compare this commit to its parent.

        :return:
        """
        return GitDiff(self._commit.diff(self.parent))

    def new_or_changed_files(self, commit: Commit) -> Set:
        """
        Get a set of files that were new or changed compared to the given commit.

        :param commit: Commit to compare against.
        :return: Set of files that are new or changed between commits.
        """
        diff = GitDiff(self._commit.diff(commit))
        return {change.b_path for change in diff.new_file_iter()}


class GitDiff(object):
    """A Git diff object."""
    def __init__(self, diff: DiffIndex):
        """
        Create an object representing a diff.
        :param diff: diff object.
        """
        self._diff = diff

    def new_file_iter(self):
        """
        Iterate over file for added changes in the diff.

        :return: Iterator for added files.
        """
        for patch in self._diff.iter_change_type('M'):
            yield patch

        for patch in self._diff.iter_change_type('A'):
            yield patch

        for patch in self._diff.iter_change_type('R'):
            yield patch
