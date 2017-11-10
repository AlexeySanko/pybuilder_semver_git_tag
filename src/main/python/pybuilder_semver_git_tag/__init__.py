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
    Plugin which provides dynamic project version based on SemVer git tag
"""
import sys

import git
from pybuilder.core import before, init, use_plugin
from pybuilder.plugins.python.core_plugin import DISTRIBUTION_PROPERTY
from pybuilder.errors import BuildFailedException
from pybuilder.reactor import Reactor
import semver

from pybuilder_semver_git_tag import version


__author__ = 'Alexey Sanko'
__version__ = version.__version__

use_plugin("python.core")


DEFAULT_PROPERTIES = {
    'semver_git_tag_increment_part': 'patch',
    'semver_git_tag_repo_dir': None,
    'semver_git_tag_version_prefix': ''
}
SAVED_PROP_SUFFIX = '_on_import_plugin'


def _add_dev(project_version):
    return project_version + '.dev'


class _TagInfo(object):     # pylint: disable=too-few-public-methods
    def __init__(self, name, commit, version_prefix):
        self.name = name
        self.commit = commit
        self._version_prefix = version_prefix

    @property
    def short(self):
        """ Return short form of tag name - without version prefix"""
        if self._version_prefix:
            if str(self.name).startswith(self._version_prefix):
                return str(self.name).replace(self._version_prefix, '', 1)
            return ''
        return self.name


def _get_repo(path):
    try:
        repo = git.Repo(path)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        raise BuildFailedException("Directory `%s` isn't git repository root."
                                   % path)
    return repo


def _get_repo_info(path, version_prefix):
    """
    Collect information about Git repository

    Function include all communication with Git repository.
    That allow to cover basic functionality with tests.

    :param path:
    :return: (list of TagInfo, last commit for head, is_dirty flag)
    """
    repo = _get_repo(path)
    result_tags = []
    for tag in repo.tags:
        result_tags.append(_TagInfo(tag.name, tag.commit, version_prefix))
    return (result_tags,
            list(repo.iter_commits(repo.head, max_count=1))[0],
            repo.is_dirty())


def _seek_last_semver_tag(tags, excluded_short=''):
    """
    Seek last SemVer version from tags
    :param tags: list of _TagInfo
    :param version_prefix: prefix into version tag
    :param excluded_short: short which should be excluded
    :return: _TagInfo with the latest SemVer tag name
    """
    last_semver_tag = None
    semver_regex = semver._REGEX  # pylint: disable=protected-access
    for tag in tags:
        match = semver_regex.match(tag.short)
        if match and tag.short != excluded_short:
            if ((not last_semver_tag) or
                    (semver.compare(tag.short, last_semver_tag.short) == 1)):
                last_semver_tag = tag
    return last_semver_tag


def check_changelog(changelog_file, repo_path, last_semver_tag, tags, logger):
    """
    Function check fact of changing into changelog file
    since previous release tag
    :param changelog_file : path to changelog file
    :param repo_path: path to dir with git repo
    :param last_semver_tag: release tag
    :param tags: list of _TagInfo object for git repo
    """
    logger.debug("Checking changelog changes into file %s" % changelog_file)
    previous_release_tag = _seek_last_semver_tag(
        tags, excluded_short=last_semver_tag.short)
    repo = _get_repo(repo_path)
    diff = repo.git.diff(
        previous_release_tag.commit,
        last_semver_tag.commit,
        changelog_file)
    if not diff:
        raise BuildFailedException(
            "Not found changes between previous tag %s and current tag %s"
            " into configured changelog file %s"
            % (previous_release_tag.name, last_semver_tag.name,
               changelog_file))


def set_version_from_git_tag(project, logger):
    """ Set project version according git tags"""
    # get git info
    version_prefix = project.get_property('semver_git_tag_version_prefix')
    repo_path = (project.get_property('semver_git_tag_repo_dir')
                 if project.get_property('semver_git_tag_repo_dir')
                 else project.basedir)
    tags, last_commit, repo_is_dirty = _get_repo_info(repo_path, version_prefix)
    tag_list = []
    for tag in tags:
        tag_list.append(tag.name)
    logger.debug("All git tags: %s." % ','.join(tag_list))
    # get last tag which satisfies SemVer
    last_semver_tag = _seek_last_semver_tag(tags)
    if not last_semver_tag:
        logger.warn(
            "No SemVer git tag found. "
            "Consider removing plugin pybuilder_semver_git_tag.")
        return
    else:
        logger.info("Found SemVer tag: %s" % last_semver_tag.name)
    # get last commit for HEAD
    # if dirty or last commit isn't equal last tag commit
    # - increase version and add .dev
    if last_commit != last_semver_tag.commit or repo_is_dirty:
        if repo_is_dirty:
            logger.debug("Repo is marked as dirty - use dev version.")
        else:
            logger.debug("Last tag %s has commit %s, "
                         "but last commit is %s - use dev version."
                         % (last_semver_tag.name,
                            str(last_semver_tag.commit),
                            str(last_commit)))
        increase_part = project.get_property('semver_git_tag_increment_part')
        if increase_part == 'major':
            project.version = _add_dev(semver.bump_major(last_semver_tag.name))
        elif increase_part == 'minor':
            project.version = _add_dev(semver.bump_minor(last_semver_tag.name))
        elif increase_part == 'patch':
            project.version = _add_dev(semver.bump_patch(last_semver_tag.name))
        else:
            raise BuildFailedException(
                "Incorrect value for `semver_git_tag_increment_part` property. "
                "Has to be in (`major`, `minor`, `patch`), but `%s` passed."
                % project.get_property('semver_git_tag_increment_part'))
    # if not dirty and last commit is equal last tag commit
    # - it's release tag
    else:
        project.version = last_semver_tag.name
        if project.get_property('semver_git_tag_changelog'):
            check_changelog(project.expand_path('$semver_git_tag_changelog'),
                            repo_path, last_semver_tag, tags, logger)
    logger.info("Project version was set to: %s, dist_version: %s"
                % (project.version, project.dist_version))


def force_semver_git_tag_plugin(project, logger):
    """ Force call SemVer git tag plugin on import stage"""
    # workaround for command line properties
    # until https://github.com/pybuilder/pybuilder/pull/515
    # set default or from command line properties
    for key in DEFAULT_PROPERTIES:
        project.set_property_if_unset(key, DEFAULT_PROPERTIES[key])
        for arg in sys.argv:
            if str(arg).startswith(key + '='):
                project.set_property(key, str(arg).replace(key + '=', ''))
    set_version_from_git_tag(project, logger)
    # save current properties
    for key in DEFAULT_PROPERTIES:
        project.set_property_if_unset(key + SAVED_PROP_SUFFIX,
                                      project.get_property(key))


# if we're in working project - update version according git tag
if Reactor.current_instance():
    force_semver_git_tag_plugin(
        Reactor.current_instance().project, Reactor.current_instance().logger)


@init
def initialize_semver_git_tag(project):
    """ Init default plugin project properties. """
    project.plugin_depends_on('GitPython')
    project.plugin_depends_on('semver')
    # Part for develop increment - 'major', 'minor' or 'patch'
    project.set_property_if_unset('semver_git_tag_increment_part', 'patch')
    # Git repository directory path.
    # If None parent directory for build.py will be used
    project.set_property_if_unset('semver_git_tag_repo_dir', None)
    # Relative path with name of changelog file.
    # If not None for release tag plugin will check
    # that changelog was changed since previous tag release
    project.set_property_if_unset('semver_git_tag_changelog', None)
    # Specific prefix of release tags. For example, 'v' for 'v1.2.3' tag
    project.set_property_if_unset('semver_git_tag_version_prefix', '')


@before("prepare", only_once=True)
def update_version_from_git_tag(project, logger):
    """ Update project version according git tags if any property was changed"""
    # Compare properties saved on import stage with actual
    are_properties_changed = False
    for key in DEFAULT_PROPERTIES:
        if (project.get_property(key + SAVED_PROP_SUFFIX) !=
                project.get_property(key)):
            logger.warn("Property `{prop}` was changed. "
                        "For better compatibility recommended to use "
                        "command line `pyb ... -P {prop}=...`, "
                        "otherwise some version-related properties could "
                        "be spoiled.".format(prop=key))
            are_properties_changed = True
    if are_properties_changed:
        logger.info("Updating project version according git tag...")
        set_version_from_git_tag(project, logger)
        # DISTRIBUTION_PROPERTY is also be affected
        project.set_property(DISTRIBUTION_PROPERTY,
                             "$dir_target/dist/{0}-{1}".format(
                                 project.name, project.version))
        logger.info("Additional affected properties: %s: %s"
                    % (DISTRIBUTION_PROPERTY,
                       project.get_property(DISTRIBUTION_PROPERTY)))
