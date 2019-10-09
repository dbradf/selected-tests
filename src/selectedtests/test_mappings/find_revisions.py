from datetime import datetime, timedelta
from typing import Dict
import pdb

from evergreen.api import EvergreenApi
from evergreen.version import Version
from structlog import get_logger

LOGGER = get_logger(__name__)


def _add_project_revision_for_version(version: Version, project_revisions_to_analyze: list):
    project_revisions_to_analyze.append(version.revision)


def _add_module_revision_for_version(
    version: Version, module_repo: str, module_revisions_to_analyze: list
):
    modules = version.get_manifest().modules
    for module in modules:
        if modules[module].repo == module_repo:
            module_revision = modules[module].revision
    if len(module_revisions_to_analyze) == 0 or module_revisions_to_analyze[-1] != module_revision:
        module_revisions_to_analyze.append(module_revision)


def _get_module_info(version: Version, module_repo: str):
    modules = version.get_manifest().modules
    for module in modules:
        if modules[module].repo == module_repo:
            return {
                "module_owner": modules[module].owner,
                "module_repo": modules[module].repo,
                "module_branch": modules[module].branch,
            }


def get_project_info(
    evg_api: EvergreenApi, project: str, start_date: int, module_repo: str = ""
) -> Dict:
    version_iterator = evg_api.versions_by_project(project)
    project_revisions_to_analyze = []
    module_revisions_to_analyze = []
    branch = None
    repo = None
    module_info = None

    for num, version in enumerate(version_iterator):
        if num == 0:
            branch = version.branch
            repo = version.repo
            module_info = _get_module_info(version, module_repo)
        log = LOGGER.bind(version=version.version_id)
        if version.create_time < start_date:
            log.debug("done", create_time=version.create_time)
            break

        _add_project_revision_for_version(version, project_revisions_to_analyze)
        if bool(module_repo):
            _add_module_revision_for_version(version, module_repo, module_revisions_to_analyze)

    return {
        "repo": repo,
        "branch": branch,
        "module_owner": module_info["module_owner"],
        "module_repo": module_info["module_repo"],
        "module_branch": module_info["module_branch"],
        "project_revisions_to_analyze": project_revisions_to_analyze,
        "module_revisions_to_analyze": module_revisions_to_analyze,
    }
