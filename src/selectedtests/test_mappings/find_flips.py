from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, List

from boltons.iterutils import windowed_iter
from evergreen.api import EvergreenApi
from evergreen.build import Build
from evergreen.task import Task
from evergreen.version import Version
from structlog import get_logger

LOGGER = get_logger(__name__)

DEFAULT_THREADS = 16


def _add_test_mappings_for_version(version, project_revisions_to_analyze, module_revisions_to_analyze):
    """
    Build a dictionary of tasks that flipped for builds in this version.

    :param work_item: Container of work items to analyze.
    :return: RevisionPair of what tasks flipped.
    """
    project_revisions_to_analyze.append(version.revision)
    if len(module_revisions_to_analyze) == 0 or module_revisions_to_analyze[-1] != version.get_manifest().modules["enterprise"].revision:
        module_revisions_to_analyze.append(version.get_manifest().modules["enterprise"].revision)


def find(project: str, evg_api: EvergreenApi) -> Dict:
    """
    Find test flips in the evergreen project.

    :param project: Evergreen project to analyze.
    :param look_back: Look at commits until the given project.
    :param evg_api: Evergreen API.
    :param n_threads: Number of threads to use.
    :return: Dictionary of commits that introduced task flips.
    """
    LOGGER.debug("Starting find_flips iteration")
    version_iterator = evg_api.versions_by_project(project)
    project_revisions_to_analyze = []
    module_revisions_to_analyze = []

    for version in version_iterator:
        log = LOGGER.bind(version=version.version_id)
        log.debug("Starting to look")
        if version.create_time < (datetime.now() - timedelta(days=3)):
            log.debug("done", create_time=version.create_time)
            break

        _add_test_mappings_for_version(version, project_revisions_to_analyze, module_revisions_to_analyze)

    return {"project_revisions_to_analyze": project_revisions_to_analyze, "module_revisions_to_analyze": module_revisions_to_analyze}
