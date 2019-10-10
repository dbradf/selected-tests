from unittest.mock import MagicMock
import pdb
import git
import os
import re
import shutil
import pytest

from datetime import datetime, time, timedelta

import selectedtests.test_mappings.test_mapper as under_test

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TEMP_REPO_DIRECTORY = os.path.join(CURRENT_DIRECTORY, 'my-temp-repo')


@pytest.fixture(scope="module")
def git_repo():
    source_file_name = os.path.join(TEMP_REPO_DIRECTORY, 'new-source-file')
    test_file_name = os.path.join(TEMP_REPO_DIRECTORY, 'new-test-file')

    repo = git.Repo.init(TEMP_REPO_DIRECTORY)
    repo.index.add([])
    repo.index.commit("initial commit -- no files changed")
    open(source_file_name, 'wb').close()
    open(test_file_name, 'wb').close()
    repo.index.add([source_file_name, test_file_name])
    repo.index.commit("add source and test file in same commit")
    #  repo.active_branch // mastersource_file_name, test_file_name
    #  commits = [commit for commit in repo.iter_commits('master', max_count=50)]
    yield repo

    # teardown fixture
    shutil.rmtree(TEMP_REPO_DIRECTORY)


class TestTestMapper:
    def test_create_mappings(self, git_repo):
        revisions = [commit.hexsha for commit in git_repo.iter_commits('master')]
        source_re = re.compile(".*source")
        test_re = re.compile(".*test")
        start_date = datetime.combine(datetime.now() - timedelta(days=1), time())
        project = "project"
        branch = "branch"
        mappings = under_test.TestMapper.create_mappings(git_repo, revisions, test_re, source_re, start_date, project, branch);
        pdb.set_trace()
