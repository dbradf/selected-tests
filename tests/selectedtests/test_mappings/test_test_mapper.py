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
        test_mappings = under_test.TestMapper.create_mappings(git_repo, revisions, test_re, source_re, start_date, project, branch)
        test_mappings_list = test_mappings.get_mappings()
        source_file_test_mapping = test_mappings_list[0]
        assert source_file_test_mapping['source_file'] == 'new-source-file'
        assert source_file_test_mapping['project'] == project
        assert source_file_test_mapping['repo'] == os.path.basename(git_repo.working_dir)
        assert source_file_test_mapping['branch'] == branch
        assert source_file_test_mapping['source_file_seen_count'] == 1
        for test_file_mapping in source_file_test_mapping['test_files']:
            assert test_file_mapping['name'] == 'new-test-file'
            assert test_file_mapping['test_file_seen_count'] == 1
