import json
import logging
from datetime import datetime, time, timedelta
from git import Repo
import pdb
import re
import os.path

import click
import structlog
from evergreen.api import EvergreenApi
from evergreen.api import CachedEvergreenApi

from selectedtests.test_mappings.find_revisions import add_revisions_for_project
from selectedtests.test_mappings.heatmap import Heatmap

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]


def _setup_logging(verbose: bool):
    """Setup logging configuration"""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    for external_lib in EXTERNAL_LIBRARIES:
        logging.getLogger(external_lib).setLevel(logging.WARNING)


#  def _repo_for_module(evg_api: EvergreenApi, project: str, module_repo: str):
    #  pdb.set_trace()
    #  most_recent_project_version = evg_api.recent_version_by_project(project)[0]
    #  modules = most_recent_project_version.get_manifest().modules
    #  for module in modules:
        #  if modules[module].repo == module_repo:
            #  module_repo_url = modules[module].url
    #  return module_repo_url


def _get_module_repo(evg_api: EvergreenApi, project: str, module_repo: str):
    repo_url = "https://github.com/10gen/mongo-enterprise-modules"
    repo_dest = "./mongo-enterprise-modules"
    repo = Repo.clone_from(repo_url, repo_dest)
    return repo


def _get_project_repo(evg_api: EvergreenApi, project: str, module_repo: str):
    repo_url = "https://github.com/mongodb/mongo"
    CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    PROJECT_REPO = os.path.join(CURRENT_DIRECTORY, "mongo")
    if os.path.exists(PROJECT_REPO):
        repo = Repo(PROJECT_REPO)
    else:
        repo = Repo.clone_from(repo_url, PROJECT_REPO)
    return repo


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose: str):
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = CachedEvergreenApi.get_api(use_config_file=True)

    _setup_logging(verbose)


@cli.command()
@click.pass_context
@click.option(
    "--project", type=str, required=True, help="Evergreen project to analyze."
)
@click.option(
    "--module-repo", type=str, default="", help="Evergreen project's module to analyze."
)
@click.option("--days-back", type=int, required=True, help="How far back to analyze.")
def find_mappings(ctx, project: str, module_repo: str, days_back: int):
    evg_api = ctx.obj["evg_api"]

    LOGGER.debug("calling find_flips", project=project, evg_api=evg_api)
    start_date = datetime.combine(datetime.now() - timedelta(days=days_back), time())
    revisions_for_project = add_revisions_for_project(evg_api, project, start_date, module_repo)
    #  revisions_for_project = _repo_for_module(evg_api, project, module_repo)
    repo = _get_project_repo(evg_api, project, module_repo)
    revisions = revisions_for_project["project_revisions_to_analyze"]
    source_re = re.compile("^src/mongo")
    test_re = re.compile("^jstests")
    heatmap = Heatmap.create_heatmap(repo, revisions, test_re, source_re, start_date)

    #  print(json.dumps(revisions_for_project, indent=4))
    print(json.dumps(heatmap.get_heatmap(), indent=4))


def main():
    """Entry point into commandline."""
    return cli(obj={})
