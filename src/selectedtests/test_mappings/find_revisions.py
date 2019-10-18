from datetime import datetime, timedelta
from typing import Dict
import pdb

from evergreen.api import EvergreenApi
from evergreen.version import Version
from structlog import get_logger

LOGGER = get_logger(__name__)


def _get_module_info(version: Version, module_repo: str):
    modules = version.get_manifest().modules
    for module in modules:
        if modules[module].repo == module_repo:
            return {
                "module_owner": modules[module].owner,
                "module_repo": modules[module].repo,
                "module_branch": modules[module].branch,
            }


def get_project_info(evg_api: EvergreenApi, project: str, module_repo: str = "") -> Dict:
    version_iterator = evg_api.versions_by_project(project)
    branch = None
    repo_name = None
    module_info = None

    for num, version in enumerate(version_iterator):
        if num == 0:
            branch = version.branch
            repo_name = version.repo
            module_info = _get_module_info(version, module_repo)
            break

    return {
        "repo_name": repo_name,
        "branch": branch,
        "module_owner": module_info["module_owner"],
        "module_repo_name": module_info["module_repo"],
        "module_branch": module_info["module_branch"],
    }
