from collections import defaultdict

import structlog
from structlog.stdlib import LoggerFactory
import pdb
from selectedtests.test_mappings.git_repo import GitCommit
import os.path

structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.get_logger(__name__)


class TestMapper(object):
    def __init__(
        self, file_intersection, file_count_map, commit_count, project, repo, branch
    ):
        """
        Create a TestMapper object.

        :param file_intersection: Map of how files intersect.
        :param file_count_map: Map of how many times files where seen.
        :param commit_count: Number of commits seen.
        """
        self._file_intersection = file_intersection
        self._file_count_map = file_count_map
        self.commit_count = commit_count
        self._test_mappings = None
        self.project = project
        self.repo = repo
        self.branch = branch

    @classmethod
    def create_mappings(
        cls, repo, revisions, test_re, source_re, start_date, project, branch
    ):
        file_intersection = defaultdict(lambda: defaultdict(int))
        file_count = defaultdict(int)

        LOGGER.debug("searching until", ts=start_date)
        commit_count = 0
        for revision in revisions:
            commit = GitCommit(repo.commit(revision))
            LOGGER.debug(
                "Investigating commit",
                summary=commit.summary(),
                ts=commit.commit_time,
                id=commit.id,
            )

            if start_date and commit.commit_time.timestamp() < start_date.timestamp():
                break

            commit_count += 1

            tests_changed = set()
            src_changed = set()
            for path in commit.new_or_changed_files(commit.parent):
                LOGGER.debug("found change", path=path)

                if test_re.match(path):
                    tests_changed.add(path)
                elif source_re.match(path):
                    src_changed.add(path)

            for src in src_changed:
                file_count[src] += 1
                for test in tests_changed:
                    file_intersection[src][test] += 1

        return TestMapper(
            file_intersection, file_count, commit_count, project, repo, branch
        )

    def get_mappings(self):
        if not self._test_mappings:
            self._test_mappings = self._transform_mappings()
        return self._test_mappings

    def _transform_mappings(self):
        test_mappings = []
        repo_name = os.path.basename(self.repo.working_dir)
        for source_file, test_file_count_dict in self._file_intersection.items():
            test_files = []
            for test_file, test_file_seen_count in test_file_count_dict.items():
                test_files.append({"name": test_file, "test_file_seen_count": test_file_seen_count})
            test_mapping = {
                "source_file": source_file,
                "project": self.project,
                "repo": repo_name,
                "branch": self.branch,
                "source_file_seen_count": self._file_count_map[source_file],
                "test_files": test_files,
            }
            test_mappings.append(test_mapping)
        return test_mappings
