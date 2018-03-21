#   -*- coding: utf-8 -*-
#
#   Copyright 2017 Alexey Sanko
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Tests for pybuilder_semver_git_tag module

"""
from random import shuffle
from unittest import TestCase

from mock import Mock, patch
from pybuilder.core import Project
from pybuilder.errors import BuildFailedException

from pybuilder_semver_git_tag import (
    _add_dev,
    _TagInfo,
    initialize_semver_git_tag,
    _seek_last_semver_tag,
    set_version_from_git_tag,
    force_semver_git_tag_plugin,
    update_version_from_git_tag,
    _get_repo_name,
    _get_repo_info
)


class SemVerGitPluginInitializationTests(TestCase):
    """ Test initialize_cram_console_scripts    """
    def setUp(self):
        self.project = Project("basedir")

    def test_should_set_default_properties(self):   # pylint: disable=invalid-name
        """ We need to init properties"""
        initialize_semver_git_tag(self.project)
        self.assertEquals(
            self.project.get_property('semver_git_tag_increment_part'), 'patch')
        self.assertEquals(
            self.project.get_property('semver_git_tag_version_prefix'), '')

    def test_should_leave_user_specified_properties(self):  # pylint: disable=invalid-name
        """ We need to keep user-defined properties"""
        self.project.set_property('semver_git_tag_increment_part', 'minor')
        self.project.set_property('semver_git_tag_repo_dir', '/some/dir')
        self.project.set_property('semver_git_tag_changelog',
                                  'dir/CHANGELOG.md')
        self.project.set_property('semver_git_tag_version_prefix', 'v')
        initialize_semver_git_tag(self.project)
        self.assertEquals(
            self.project.get_property('semver_git_tag_increment_part'), 'minor')
        self.assertEquals(
            self.project.get_property('semver_git_tag_repo_dir'), '/some/dir')
        self.assertEquals(
            self.project.get_property('semver_git_tag_changelog'),
            'dir/CHANGELOG.md')
        self.assertEquals(
            self.project.get_property('semver_git_tag_version_prefix'), 'v')


class SeekLastTagTests(TestCase):
    """ Test function _seek_last_semver_tag"""
    def test_basic_seek(self):
        """ Test result for basic versions"""
        tags = []
        for i in range(15):
            tags.append(_TagInfo(
                '1.0.' + str(i),
                'commit' + str(i),
                ''))
        for i in range(15):
            shuffle(tags)
            self.assertEqual(_seek_last_semver_tag(tags).name, '1.0.14')
            self.assertEqual(_seek_last_semver_tag(tags, '1.0.14').name,
                             '1.0.13')

    def test_none_return(self):
        """ Test than function returns None if not SemVer found"""
        tags = []
        for i in range(15):
            tags.append(_TagInfo('v1.0.' + str(i), 'commit' + str(i), ''))
        for i in range(15):
            shuffle(tags)
            self.assertEqual(_seek_last_semver_tag(tags), None)

    def test_none_return_if_all_excluded(self):     # pylint: disable=invalid-name
        """ Test than function returns None if excluded one SemVer tag"""
        tags = [_TagInfo('1.0.1', 'commit1', ''),
                _TagInfo('notsemver', 'commit2', '')]
        self.assertEqual(_seek_last_semver_tag(tags, '1.0.1'), None)

    def test_basic_version_seek(self):
        """ Test result for basic versions with prefix"""
        version_prefix = 'v'
        tags = []
        for i in range(15):
            tags.append(_TagInfo('%s1.0.%s' % (version_prefix, i),
                                 'commit%s' % i,
                                 version_prefix))
        for i in range(15):
            shuffle(tags)
            self.assertEqual(_seek_last_semver_tag(tags).name, 'v1.0.14')
            self.assertEqual(_seek_last_semver_tag(tags, '1.0.14').name,
                             'v1.0.13')

    def test_none_version_return(self):
        """ Test than function returns None if not SemVer found with prefix"""
        version_prefix = 'v'
        tags = []
        for i in range(15):
            tags.append(_TagInfo('1.0.' + str(i),
                                 'commit' + str(i),
                                 version_prefix))
        for i in range(15):
            shuffle(tags)
            self.assertEqual(_seek_last_semver_tag(tags, version_prefix), None)

    def test_none_version_return_if_all_excluded(self):     # pylint: disable=invalid-name
        """ Test than function returns None if excluded one SemVer tag"""
        version_prefix = 'v'
        tags = [_TagInfo('v1.0.1', 'commit1', version_prefix),
                _TagInfo('notsemver', 'commit2', version_prefix),
                _TagInfo('v1.0.v2', 'commit2', version_prefix)]
        self.assertEqual(_seek_last_semver_tag(tags, '1.0.1'), None)


class VersionFromGitTests(TestCase):
    """ Test plugin functionality    """
    def setUp(self):
        self.project = Project("basedir")
        self.logger = Mock()

    def test__add_dev(self):
        """ Test _add_dev   """
        self.assertEquals(_add_dev('1.2.3'), '1.2.3.dev')

    def test_should_raise_if_git_repo_not_exists(self):     # pylint: disable=invalid-name
        """ Plugin should raise exception if cannot find git root directory"""
        with self.assertRaises(BuildFailedException) as context:
            set_version_from_git_tag(self.project, self.logger)
        err_msg = str(context.exception)
        self.assertTrue(
            "Directory `basedir` isn't git repository root." in err_msg)

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('not_semver2', 'commit2', ''),
                          _TagInfo('not_semver1', 'commit1', '')],
                         'last_commit', False))
    def test_should_warning_if_semver_tag_not_found(self, mock_git_info):   # pylint: disable=invalid-name, unused-argument
        """ Plugin should warning if SemVer tag wasn't found and return"""
        set_version_from_git_tag(self.project, self.logger)
        self.logger.warn.assert_called_once_with(
            "No SemVer git tag found. "
            "Consider removing plugin pybuilder_semver_git_tag.")
        self.logger.info.assert_not_called()

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'last_commit', ''),
                          _TagInfo('not_semver1', 'commit1', '')],
                         'last_commit', False))
    def test_release_version_found(self, mock_git_info):    # pylint: disable=invalid-name, unused-argument
        """ Plugin should find release version"""
        set_version_from_git_tag(self.project, self.logger)
        self.assertEqual(self.logger.info.call_count, 2)
        self.assertEqual(self.project.version, '1.2.3')

    def get_dev_version(self, increment_part):
        """ Util method which call set_version_from_git_tag
            with particular level of version increment part
        """
        self.project.set_property(
            'semver_git_tag_increment_part', increment_part)
        set_version_from_git_tag(self.project, self.logger)

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'last_commit', ''),
                          _TagInfo('not_semver1', 'commit1', '')],
                         'last_commit', True))
    def test_dev_version_if_dirty(self, mock_git_info):     # pylint: disable=invalid-name, unused-argument
        """ Plugin should generate dev version if repo is dirty"""
        # Test `patch` part
        self.get_dev_version('patch')
        self.assertEqual(self.project.version, '1.2.4.dev')
        # Test `minor` part
        self.get_dev_version('minor')
        self.assertEqual(self.project.version, '1.3.0.dev')
        # Test `major` part
        self.get_dev_version('major')
        self.assertEqual(self.project.version, '2.0.0.dev')
        # Test incorrect part
        self.project.set_property('semver_git_tag_increment_part', 'incorrect')
        with self.assertRaises(BuildFailedException) as context:
            set_version_from_git_tag(self.project, self.logger)
        err_msg = str(context.exception)
        self.assertTrue(
            ("Incorrect value for `semver_git_tag_increment_part` property. "
             "Has to be in (`major`, `minor`, `patch`), "
             "but `incorrect` passed.") in err_msg)

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'commit2', ''),
                          _TagInfo('not_semver1', 'commit1', '')],
                         'last_commit', False))
    def test_dev_version_if_tagged_not_last_commit(self, mock_git_info):  # pylint: disable=invalid-name, unused-argument
        """ Plugin should generate dev version
            if repo had commit(s) after SemVer tagger commit
        """
        # Test `patch` part
        self.get_dev_version('patch')
        self.assertEqual(self.project.version, '1.2.4.dev')
        # Test `minor` part
        self.get_dev_version('minor')
        self.assertEqual(self.project.version, '1.3.0.dev')
        # Test `major` part
        self.get_dev_version('major')
        self.assertEqual(self.project.version, '2.0.0.dev')
        # Test incorrect part
        self.project.set_property('semver_git_tag_increment_part', 'incorrect')
        with self.assertRaises(BuildFailedException) as context:
            set_version_from_git_tag(self.project, self.logger)
        err_msg = str(context.exception)
        self.assertTrue(
            ("Incorrect value for `semver_git_tag_increment_part` property. "
             "Has to be in (`major`, `minor`, `patch`), "
             "but `incorrect` passed.") in err_msg)


class UpdateVersionTests(TestCase):
    """ Test update_version_from_git_tag function"""
    def setUp(self):
        self.project = Project("basedir")
        self.logger = Mock()

    @patch("pybuilder_semver_git_tag.set_version_from_git_tag")
    @patch("pybuilder_semver_git_tag._get_repo_name")
    def test_force_and_update(self, _get_repo_name,  # pylint: disable=unused-argument
                              set_version_from_git_tag_mock):
        """ Test force set and update after that"""
        force_semver_git_tag_plugin(self.project, self.logger)
        self.project.set_property('semver_git_tag_increment_part', 'minor')
        update_version_from_git_tag(self.project, self.logger)
        self.assertEqual(set_version_from_git_tag_mock.call_count, 2)
        self.assertEqual(self.logger.info.call_count, 2)
        self.logger.warn.assert_called_once_with(
            "Property `semver_git_tag_increment_part` was changed. "
            "For better compatibility recommended to use "
            "command line `pyb ... -P semver_git_tag_increment_part=...`, "
            "otherwise some version-related properties could "
            "be spoiled."
        )


class _Remotes(object):  # pylint: disable=too-few-public-methods
    def __init__(self, name, url):
        self.name = name
        self.url = url


class _Commit(object):  # pylint: disable=too-few-public-methods
    def __init__(self, hexsha):
        self.hexsha = hexsha


class _Tag(object):  # pylint: disable=too-few-public-methods
    def __init__(self, name, commit):
        self.name = name
        self.commit = commit


class _Head(object):  # pylint: disable=too-few-public-methods
    def __init__(self, last_commit, prev_commits):
        self.commit = last_commit
        self.commits_list = prev_commits + [last_commit]


class _Repo(object):     # pylint: disable=too-few-public-methods
    def __init__(self, remotes=None, head=None, is_dirty=False, tags=None):
        self.remotes = remotes if remotes else []
        self.dirty = is_dirty
        self.head = head
        self.tags = tags if tags else []

    def is_dirty(self):
        """ Stub for is_dirty flag"""
        return self.dirty

    def iter_commits(self, rev=None):  # pylint: disable=no-self-use
        """ Stub for iter_commits"""
        return iter(rev.commits_list)


class GetRepoNameTests(TestCase):
    """ Test _get_repo_name function"""

    def setUp(self):
        self.project = Project("basedir")
        self.logger = Mock()

    @patch("pybuilder_semver_git_tag._get_repo",
           return_value=(_Repo(remotes=[
               _Remotes(
                   'someremote',
                   'https://github.com/AlexeySanko/some_incorrect.git'),
               _Remotes(
                   'origin',
                   'https://github.com/AlexeySanko/pybuilder_semver_git_tag.git'),  # pylint: disable=line-too-long
               _Remotes(
                   'someotherremote',
                   'https://github.com/AlexeySanko/some_other_incorrect.git')
           ])))
    def test_get_name_from_origin(self, mock_get_repo):  # pylint: disable=unused-argument
        """Check that function correctly works with repositories with
                    origin remote"""
        self.assertEqual(_get_repo_name(''), 'pybuilder_semver_git_tag')

    @patch("pybuilder_semver_git_tag._get_repo",
           return_value=(_Repo(remotes=[
               _Remotes(
                   'myremote',
                   'https://github.com/AlexeySanko/pybuilder_semver_git_tag.git'),  # pylint: disable=line-too-long
               _Remotes(
                   'someotherremote',
                   'https://github.com/AlexeySanko/some_other_incorrect.git')
           ])))
    def test_get_name_from_any_remote(self, mock_get_repo):  # pylint: disable=unused-argument
        """Check that function correctly works with repositories without
            origin remote"""
        self.assertEqual(_get_repo_name(''), 'pybuilder_semver_git_tag')


class GetRepoInfoTests(TestCase):
    """ Test _get_repo_info function"""

    def setUp(self):
        self.project = Project("basedir")
        self.logger = Mock()

    @patch("pybuilder_semver_git_tag._get_repo",
           return_value=_Repo(
               head=_Head(
                   last_commit=_Commit("shaforlastcommit"),
                   prev_commits=[_Commit("shaforfirstcommit"),
                                 _Commit("shaforsecondcommit"),
                                 _Commit("shaforthirdcommit")]),
               tags=[_Tag('tag1', _Commit("shaforfirstcommit")),
                     _Tag('tag4', _Commit("shaforlastcommit")),
                     _Tag('tagotherbranch',
                          _Commit("shaforcommitfromotherbranch"))],
               is_dirty=True
           ))
    def test_get_info_for_active_branch(self, mock_get_repo):  # pylint: disable=unused-argument
        """Check that function correctly returns tags for active branch"""
        tags, last_commit, repo_is_dirty = _get_repo_info('', None)
        self.assertEqual(repo_is_dirty, True)
        self.assertEqual(last_commit.hexsha, 'shaforlastcommit')
        self.assertEqual(len(tags), 2)
        for tag in tags:
            self.assertTrue(tag.name in ['tag1', 'tag4'])
