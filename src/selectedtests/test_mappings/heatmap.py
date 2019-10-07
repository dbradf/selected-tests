from collections import defaultdict

import structlog
from structlog.stdlib import LoggerFactory
import pdb
from selectedtests.test_mappings.git_repo import GitCommit

structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.get_logger(__name__)


class Heatmap(object):
    def __init__(self, file_intersection, file_count_map, commit_count):
        """
        Create a Heatmap object.

        :param file_intersection: Map of how files intersect.
        :param file_count_map: Map of how many times files where seen.
        :param commit_count: Number of commits seen.
        """
        self._file_intersection = file_intersection
        self._file_count_map = file_count_map
        self._normalized_map = None
        self.commit_count = commit_count

    @classmethod
    def create_heatmap(cls, repo, revisions, test_re, source_re, start_date):
        """
        Create a heatmap for the given repository.

        :param repo: Repository to analyze.
        :param test_re: Regular expression to match tests.
        :param source_re: Regular expression to match source.
        :param start_date: How far back to analyze commits.
        :return: Number of commits visited, Heatmap of repo, count file.
        """
        file_intersection = defaultdict(lambda: defaultdict(int))
        file_count = defaultdict(int)

        LOGGER.debug('searching until', ts=start_date)
        commit_count = 0
        for revision in revisions:
            commit = GitCommit(repo.commit(revision))
            LOGGER.debug('Investigating commit', summary=commit.summary(), ts=commit.commit_time,
                         id=commit.id)

            if start_date and commit.commit_time.timestamp() < start_date.timestamp():
                break

            commit_count += 1

            tests_changed = set()
            src_changed = set()
            for path in commit.new_or_changed_files(commit.parent):
                LOGGER.debug('found change', path=path)

                if test_re.match(path):
                    tests_changed.add(path)
                elif source_re.match(path):
                    src_changed.add(path)

            for src in src_changed:
                file_count[src] += 1
                for t in tests_changed:
                    file_intersection[src][t] += 1

        return Heatmap(file_intersection, file_count, commit_count)

    def get_heatmap(self, normalize=False):
        """
        Get a dictionary of the heatmap.

        :param normalize: Return a normalized version.
        :return: Dictionary of the heatmap.
        """
        if normalize:
            return self.normalize()
        return self._file_intersection

    @staticmethod
    def _normalize_row(test_map, src_file_count):
        """
        Normalize the given row.

        :param test_map: Map to normalize.
        :param src_file_count: Number of time the source file has been seen.
        :return: Normalized version of row.
        """
        return {k: v / src_file_count for k, v in test_map.items()}

    def normalize(self):
        """
        Get a normalized version of the heatmap.

        :return: Normalized version of heatmap.
        """
        if not self._normalized_map:
            self._normalized_map = {
                k: self._normalize_row(v, self._file_count_map[k])
                for k, v in self._file_intersection.items()}
        return self._normalized_map
