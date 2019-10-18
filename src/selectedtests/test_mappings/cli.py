"""Cli entry point for the test-mappings command."""
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
from selectedtests.test_mappings.mappings import TestMappings
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
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = CachedEvergreenApi.get_api(use_config_file=True)

    _setup_logging(verbose)


@cli.command()
@click.pass_context
@click.argument("evergreen_project", required=True)
@click.option(
    "--start",
    type=str,
    help="The date to begin analyzing the project at - has to be an iso date. "
    "Example: 2019-10-11T19:10:38",
    required=True,
)
@click.option(
    "--end",
    type=str,
    help="The date to stop analyzing the project at - has to be an iso date. "
    "Example: 2019-10-11T19:10:38",
    required=True,
)
@click.option(
    "--source-file-regex",
    type=str,
    help="Regex that will be used to map what files mappings will be created for. "
    "Example: 'src.*'",
    required=True,
)
@click.option(
    "--test-file-regex", type=str, required=True, help="Regex to match test files in project."
)
@click.option(
    "--module-name",
    type=str,
    help="The name of the associated module that should be analyzed. Example: enterprise",
)
@click.option(
    "--module-source-file-regex",
    type=str,
    help="Regex that will be used to map what module files mappings will be created. "
    "Example: 'src.*'",
)
@click.option(
    "--module-test-file-regex", required=True, help="Regex to match test files in module."
)
@click.option(
    "--output-file",
    type=str,
    help="Path to a file where the task mappings should be written to. Example: 'output.txt'",
)
def create(
    ctx,
    evergreen_project: str,
    start: str,
    end: str,
    source_file_regex: str,
    test_file_regex: str,
    module_name: str,
    module_source_file_regex: str,
    module_test_file_regex: str,
    output_file: str,
):
    evg_api = ctx.obj["evg_api"]

    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
    except ValueError as e:
        LOGGER.error(str(e))
        LOGGER.error("The start or end date could not be parsed - make sure it's an iso date")
        return

    project_info = get_project_info(evg_api, evergreen_project, module_name)

    project_repo = pull_remote_repo(project_info["repo_name"], project_info["branch"])
    source_re = re.compile(source_file_regex)
    test_re = re.compile(test_file_regex)
    project_test_mappings = TestMappings.create_mappings(
        project_repo,
        test_re,
        source_re,
        start_date,
        end_date,
        evergreen_project,
        project_info["branch"],
    )
    project_test_mappings_list = project_test_mappings.get_mappings()

    module_repo = pull_remote_repo(
        project_info["module_repo_name"],
        project_info["module_branch"],
        project_info["module_owner"],
    )
    module_source_re = re.compile(module_source_file_regex)
    module_test_re = re.compile(module_test_file_regex)
    module_test_mappings = TestMappings.create_mappings(
        module_repo,
        module_test_re,
        module_source_re,
        start_date,
        end_date,
        evergreen_project,
        project_info["module_branch"],
    )
    module_test_mappings_list = module_test_mappings.get_mappings()

    test_mappings_list = project_test_mappings_list + module_test_mappings_list

    json_dump = json.dumps(test_mappings_list, indent=4)

    if output_file is not None and output_file != "":
        f = open(output_file, "a")
        f.write(json_dump)
        f.close()
    else:
        print(json_dump)

    LOGGER.info("Finished processing test mappings")


def main():
    """Entry point into commandline."""
    return cli(obj={})
