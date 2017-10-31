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

from unittest import TestCase

from mock import Mock, patch
from pybuilder.core import Project
from pybuilder.errors import BuildFailedException

from pybuilder_semver_git_tag import (
    _add_dev,
    _TagInfo,
    initialize_semver_git_tag,
    version_from_git_tag
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

    def test_should_leave_user_specified_properties(self):  # pylint: disable=invalid-name
        """ We need to keep user-defined properties"""
        self.project.set_property('semver_git_tag_increment_part', 'minor')
        self.project.set_property('semver_git_tag_repo_dir', '/some/dir')
        initialize_semver_git_tag(self.project)
        self.assertEquals(
            self.project.get_property('semver_git_tag_increment_part'), 'minor')
        self.assertEquals(
            self.project.get_property('semver_git_tag_repo_dir'), '/some/dir')


class VersionFromGitTests(TestCase):
    """ Test plugin functionality    """
    def setUp(self):
        self.project = Project("basedir")

    def test__add_dev(self):
        """ Test _add_dev   """
        self.assertEquals(_add_dev('1.2.3'), '1.2.3.dev')

    def test_should_raise_if_git_repo_not_exists(self):     # pylint: disable=invalid-name
        """ Plugin should raise exception if cannot find git root directory"""
        self.assertRaises(BuildFailedException, version_from_git_tag,
                          self.project, Mock())

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('not_semver2', 'commit2'),
                          _TagInfo('not_semver1', 'commit1')],
                         'last_commit', False))
    def test_should_warning_if_semver_tag_not_found(self, mock_git_info):   # pylint: disable=invalid-name, unused-argument
        """ Plugin should warning if SemVer tag wasn't found and return"""
        logger_mock = Mock()
        version_from_git_tag(self.project, logger_mock)
        logger_mock.warn.assert_called_once()
        logger_mock.info.assert_not_called()

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'last_commit'),
                          _TagInfo('not_semver1', 'commit1')],
                         'last_commit', False))
    def test_release_version_found(self, mock_git_info):    # pylint: disable=invalid-name, unused-argument
        """ Plugin should find release version"""
        logger_mock = Mock()
        version_from_git_tag(self.project, logger_mock)
        self.assertEqual(logger_mock.info.call_count, 2)
        self.assertEqual(self.project.version, '1.2.3')

    def get_dev_version(self, increment_part):
        """ Util method which call version_from_git_tag
            with particular level of version increment part
        """
        logger_mock = Mock()
        self.project.set_property(
            'semver_git_tag_increment_part', increment_part)
        version_from_git_tag(self.project, logger_mock)
        self.assertEqual(logger_mock.info.call_count, 2)

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'last_commit'),
                          _TagInfo('not_semver1', 'commit1')],
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
        logger_mock = Mock()
        self.project.set_property('semver_git_tag_increment_part', 'incorrect')
        self.assertRaises(BuildFailedException, version_from_git_tag,
                          self.project, logger_mock)
        logger_mock.info.assert_called_once()

    @patch("pybuilder_semver_git_tag._get_repo_info",
           return_value=([_TagInfo('1.2.3', 'commit2'),
                          _TagInfo('not_semver1', 'commit1')],
                         'last_commit', False))
    def test_dev_version_if_tagged_not_last_commit(self, mock_git_info):    # pylint: disable=invalid-name, unused-argument
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
        logger_mock = Mock()
        self.project.set_property('semver_git_tag_increment_part', 'incorrect')
        with self.assertRaises(BuildFailedException) as context:
            version_from_git_tag(self.project, logger_mock)
        err_msg = str(context.exception)
        self.assertTrue(
            ("Incorrect value for `semver_git_tag_increment_part` property. "
             "Has to be in (`major`, `minor`, `patch`), "
             "but `incorrect` passed.") in err_msg)
        logger_mock.info.assert_called_once()
