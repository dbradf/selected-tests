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
SOURCE_RE = re.compile(".*source")
TEST_RE = re.compile(".*test")


def initialize_temp_repo(directory):
    repo = git.Repo.init(directory)
    repo.index.add([])
    repo.index.commit("initial commit -- no files changed")
    return repo


def destroy_temp_repo(directory):
    shutil.rmtree(directory)


@pytest.fixture(scope="module")
def repo_with_no_source_files_changed():
    temp_directory = os.path.join(CURRENT_DIRECTORY, "no_source_files_changed")
    repo = initialize_temp_repo(temp_directory)
    yield repo

    destroy_temp_repo(temp_directory)


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_no_test_files_changed():
    temp_directory = os.path.join(CURRENT_DIRECTORY, "one_source_file_and_no_test_files_changed")
    repo = initialize_temp_repo(temp_directory)
    source_file = os.path.join(temp_directory, 'new-source-file')
    open(source_file, 'wb').close()
    repo.index.add([source_file])
    repo.index.commit("add source file")
    yield repo

    destroy_temp_repo(temp_directory)


@pytest.fixture(scope="module")
def repo_with_no_source_files_and_one_test_file_changed():
    temp_directory = os.path.join(CURRENT_DIRECTORY, "no_source_files_and_one_test_file_changed")
    repo = initialize_temp_repo(temp_directory)
    test_file = os.path.join(temp_directory, 'new-test-file')
    open(test_file, 'wb').close()
    repo.index.add([test_file])
    repo.index.commit("add test file")
    yield repo

    destroy_temp_repo(temp_directory)


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_one_test_file_changed_in_same_commit():
    temp_directory = os.path.join(CURRENT_DIRECTORY, "one_source_file_and_one_test_file_changed_in_same_commit")
    repo = initialize_temp_repo(temp_directory)
    source_file = os.path.join(temp_directory, 'new-source-file')
    test_file = os.path.join(temp_directory, 'new-test-file')
    open(source_file, 'wb').close()
    open(test_file, 'wb').close()
    repo.index.add([source_file, test_file])
    repo.index.commit("add source and test file in same commit")
    yield repo

    destroy_temp_repo(temp_directory)


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_one_test_file_changed_in_different_commits():
    temp_directory = os.path.join(CURRENT_DIRECTORY, "one_source_file_and_one_test_file_changed_in_different_commits")
    repo = initialize_temp_repo(temp_directory)
    source_file = os.path.join(temp_directory, 'new-source-file')
    open(source_file, 'wb').close()
    repo.index.add([source_file])
    repo.index.commit("add source file")
    test_file = os.path.join(temp_directory, 'new-test-file')
    open(test_file, 'wb').close()
    repo.index.add([test_file])
    repo.index.commit("add test file")
    yield repo

    destroy_temp_repo(temp_directory)


class TestTestMapper:
    def test_create_mappings_with_no_source_files_changed(self, repo_with_no_source_files_changed):
        revisions = [commit.hexsha for commit in repo_with_no_source_files_changed.iter_commits('master')]
        start_date = datetime.combine(datetime.now() - timedelta(days=1), time())
        project = "my_project"
        branch = "master"
        test_mappings = under_test.TestMapper.create_mappings(repo_with_no_source_files_changed, revisions, TEST_RE, SOURCE_RE, start_date, project, branch)
        test_mappings_list = test_mappings.get_mappings()
        assert len(test_mappings_list) == 0


    def test_create_mappings_with_one_source_file_and_no_test_files_changed(self, repo_with_one_source_file_and_no_test_files_changed):
        revisions = [commit.hexsha for commit in repo_with_one_source_file_and_no_test_files_changed.iter_commits('master')]
        start_date = datetime.combine(datetime.now() - timedelta(days=1), time())
        project = "my_project"
        branch = "master"
        test_mappings = under_test.TestMapper.create_mappings(repo_with_one_source_file_and_no_test_files_changed, revisions, TEST_RE, SOURCE_RE, start_date, project, branch)
        test_mappings_list = test_mappings.get_mappings() #  assert len(test_mappings_list) == 0 #  def test_create_mappings_with_no_source_files_and_one_test_file_changed(self, repo_with_no_source_files_and_one_test_file_changed): #  revisions = [commit.hexsha for commit in repo_with_no_source_files_and_one_test_file_changed.iter_commits('master')] #  start_date = datetime.combine(datetime.now() - timedelta(days=1), time()) #  project = "my_project" #  branch = "master" #  test_mappings = under_test.TestMapper.create_mappings(repo_with_no_source_files_and_one_test_file_changed, revisions, TEST_RE, SOURCE_RE, start_date, project, branch) #  test_mappings_list = test_mappings.get_mappings()
        assert len(test_mappings_list) == 0


    def test_create_mappings_with_one_source_file_and_one_test_file_changed_in_same_commit(self, repo_with_one_source_file_and_one_test_file_changed_in_same_commit):
        git_repo = repo_with_one_source_file_and_one_test_file_changed_in_same_commit
        revisions = [commit.hexsha for commit in git_repo.iter_commits('master')]
        start_date = datetime.combine(datetime.now() - timedelta(days=1), time())
        project = "my_project"
        branch = "master"
        test_mappings = under_test.TestMapper.create_mappings(git_repo, revisions, TEST_RE, SOURCE_RE, start_date, project, branch)
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


    def test_create_mappings_with_one_source_file_and_one_test_file_changed_in_different_commits(self, repo_with_one_source_file_and_one_test_file_changed_in_different_commits):
        repo = repo_with_one_source_file_and_one_test_file_changed_in_different_commits
        revisions = [commit.hexsha for commit in repo.iter_commits('master')]
        start_date = datetime.combine(datetime.now() - timedelta(days=1), time())
        project = "my_project"
        branch = "master"
        test_mappings = under_test.TestMapper.create_mappings(repo, revisions, TEST_RE, SOURCE_RE, start_date, project, branch)
        test_mappings_list = test_mappings.get_mappings()
        assert len(test_mappings_list) == 0
