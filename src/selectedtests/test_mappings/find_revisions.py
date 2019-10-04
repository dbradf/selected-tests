from datetime import datetime, timedelta
from typing import Dict

from evergreen.api import EvergreenApi
from evergreen.version import Version
from structlog import get_logger

LOGGER = get_logger(__name__)


def _add_project_revision_for_version(version: Version, project_revisions_to_analyze: list):
    """
    Build a dictionary of tasks that flipped for builds in this version.

    :param work_item: Container of work items to analyze.
    :return: RevisionPair of what tasks flipped.
    """
    project_revisions_to_analyze.append(version.revision)


def _add_module_revision_for_version(version: Version, module_repo: str, module_revisions_to_analyze: list):
    """
    Build a dictionary of tasks that flipped for builds in this version.

    :param work_item: Container of work items to analyze.
    :return: RevisionPair of what tasks flipped.
    """
    modules = version.get_manifest().modules
    for module in modules:
        if modules[module].repo == module_repo:
            module_revision = modules[module].revision
    if (
        len(module_revisions_to_analyze) == 0
        or module_revisions_to_analyze[-1] != module_revision
    ):
        module_revisions_to_analyze.append(module_revision)


def add_revisions_for_project(
    evg_api: EvergreenApi, project: str, module_repo: str = ""
) -> Dict:
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
        if version.create_time < (datetime.now() - timedelta(days=3)):
            log.debug("done", create_time=version.create_time)
            break

        _add_project_revision_for_version(version, project_revisions_to_analyze)
        if bool(module_repo):
            _add_module_revision_for_version(
                version, module_repo, module_revisions_to_analyze
            )

    return {
        "project_revisions_to_analyze": project_revisions_to_analyze,
        "module_revisions_to_analyze": module_revisions_to_analyze,
    }
