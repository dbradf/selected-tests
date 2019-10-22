import json
import pdb
import pytest
import os
import git
import shutil

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.test_mappings.cli import cli
from datetime import datetime, time, timedelta

NS = "selectedtests.test_mappings.cli"
MAPPINGS_NS = "selectedtests.test_mappings.mappings"
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


def m_ns(relative_name):
    """Return a full name to mappings from a name relative to the tested module"s name space."""
    return MAPPINGS_NS + "." + relative_name


def initialize_temp_repo(directory):
    repo = git.Repo.init(directory)
    repo.index.commit("initial commit -- no files changed")
    return repo


def destroy_temp_repo(directory):
    shutil.rmtree(directory)


@pytest.fixture(scope="module")
def lydia_repo():
    temp_directory = os.path.join(
        CURRENT_DIRECTORY, "lydia_repo"
    )
    repo = initialize_temp_repo(temp_directory)
    source_file = os.path.join(temp_directory, "new-source-file")
    test_file = os.path.join(temp_directory, "new-test-file")
    open(source_file, "wb").close()
    open(test_file, "wb").close()
    repo.index.add([source_file, test_file])
    repo.index.commit("add source and test file in same commit")
    yield repo

    destroy_temp_repo(temp_directory)


class TestCli:
    @patch(ns("CachedEvergreenApi"))
    @patch(ns("init_repo"))
    def test_integration(
        self,
        init_repo_mock,
        cached_evg_api,
        evg_projects,
        evg_versions,
        expected_test_mappings_output,
        lydia_repo,
    ):
        mock_evg_api = MagicMock()
        mock_evg_api.all_projects.return_value = evg_projects
        mock_evg_api.versions_by_project.return_value = evg_versions
        cached_evg_api.get_api.return_value = mock_evg_api
        init_repo_mock.return_value = (
            lydia_repo
        )

        one_day_ago = datetime.combine(datetime.now() - timedelta(days=1), time())
        one_day_from_now = datetime.combine(datetime.now() + timedelta(days=1), time())

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--source-file-regex",
                    ".*source",
                    "--test-file-regex",
                    ".*test",
                    "--output-file",
                    output_file,
                    "--start",
                    str(one_day_ago),
                    "--end",
                    str(one_day_from_now),
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert output == expected_test_mappings_output
