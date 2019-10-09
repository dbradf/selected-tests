import json
import logging
import pdb
import re

from datetime import datetime, time, timedelta

import click
import structlog

from git import Repo
from evergreen.api import CachedEvergreenApi

from selectedtests.test_mappings.find_revisions import get_project_info
from selectedtests.test_mappings.test_mapper import TestMapper
from selectedtests.test_mappings.git_helper import pull_remote_repo

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]


def _setup_logging(verbose: bool):
    """Setup logging configuration"""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    for external_lib in EXTERNAL_LIBRARIES:
        logging.getLogger(external_lib).setLevel(logging.WARNING)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose: str):
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = CachedEvergreenApi.get_api(use_config_file=True)

    _setup_logging(verbose)


@cli.command()
@click.pass_context
@click.option("--project", type=str, required=True, help="Evergreen project to analyze.")
@click.option("--module-repo", type=str, default="", help="Evergreen project's module to analyze.")
@click.option("-s", "--source-regex", required=True, help="Regex to match source files in project.")
@click.option("-t", "--test-regex", required=True, help="Regex to match test files in project.")
@click.option(
    "-s", "--module-source-regex", required=True, help="Regex to match source files in module."
)
@click.option(
    "-t", "--module-test-regex", required=True, help="Regex to match test files in module."
)
@click.option("--days-back", type=int, required=True, help="How far back to analyze.")
def find_mappings(
    ctx,
    project: str,
    module_repo: str,
    source_regex: str,
    test_regex: str,
    module_source_regex: str,
    module_test_regex: str,
    days_back: int,
):
    evg_api = ctx.obj["evg_api"]

    start_date = datetime.combine(datetime.now() - timedelta(days=days_back), time())
    project_info = get_project_info(evg_api, project, start_date, module_repo)

    project_revisions = project_info["project_revisions_to_analyze"]
    project_repo = pull_remote_repo(project_info["repo"], project_info["branch"])
    source_re = re.compile(source_regex)
    test_re = re.compile(test_regex)
    project_test_mappings = TestMapper.create_mappings(
        project_repo,
        project_revisions,
        test_re,
        source_re,
        start_date,
        project,
        project_info["branch"],
    )
    project_test_mappings_list = project_test_mappings.get_mappings()

    module_revisions = project_info["module_revisions_to_analyze"]
    module_repo = pull_remote_repo(
        project_info["module_repo"], project_info["module_branch"], project_info["module_owner"]
    )
    module_source_re = re.compile(module_source_regex)
    module_test_re = re.compile(module_test_regex)
    module_test_mappings = TestMapper.create_mappings(
        module_repo,
        module_revisions,
        module_test_re,
        module_source_re,
        start_date,
        project,
        project_info["module_branch"],
    )
    module_test_mappings_list = module_test_mappings.get_mappings()

    test_mappings_list = project_test_mappings_list + module_test_mappings_list
    print(json.dumps(test_mappings_list, indent=4))


def main():
    """Entry point into commandline."""
    return cli(obj={})
