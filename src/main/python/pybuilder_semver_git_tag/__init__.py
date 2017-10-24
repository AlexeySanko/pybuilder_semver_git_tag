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
import git
from pybuilder.core import before, init, use_plugin
from pybuilder.plugins.python.core_plugin import DISTRIBUTION_PROPERTY
from pybuilder.errors import BuildFailedException
import semver


__author__ = 'Alexey Sanko'

use_plugin("python.core")


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


def _add_dev(version):
    return version + '.dev'


class _TagInfo(object):     # pylint: disable=too-few-public-methods
    def __init__(self, name, commit):
        self.name = name
        self.commit = commit


def _get_repo_info(path):
    """
    Collect information about Git repository

    Function include all communication with Git repository.
    That allow to cover basic functionality with tests.

    :param path:
    :return: (list of TagInfo, last commit for head, is_dirty flag)
    """
    try:
        repo = git.Repo(path)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        raise BuildFailedException("Directory `%s` isn't git repository root."
                                   % path)
    result_tags = []
    for tag in repo.tags:
        result_tags.append(_TagInfo(tag.name, tag.commit))
    return (result_tags,
            list(repo.iter_commits(repo.head, max_count=1))[0],
            repo.is_dirty())


@before("prepare", only_once=True)
def version_from_git_tag(project, logger):
    """ Set project version according git tags"""
    # get git info
    tags, last_commit, repo_is_dirty = _get_repo_info(
        project.get_property('semver_git_tag_repo_dir')
        if project.get_property('semver_git_tag_repo_dir')
        else project.basedir)
    # get last tag which satisfies SemVer
    last_semver_tag = None
    semver_regex = semver._REGEX    # pylint: disable=protected-access
    for tag in reversed(tags):
        match = semver_regex.match(tag.name)
        if match:
            last_semver_tag = tag
            break
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
                "Has to be in (`major`, `minor`, `patch`), but %s passed."
                % project.get_property('semver_git_tag_increment_part'))
    # if not dirty and last commit is equal last tag commit
    # - it's release tag
    else:
        project.version = last_semver_tag.name
    # DISTRIBUTION_PROPERTY is also be affected
    project.set_property(DISTRIBUTION_PROPERTY,
                         "$dir_target/dist/{0}-{1}".format(
                             project.name, project.version))
    logger.info("Project version was changed to: %s, dist_version: %s, %s: %s"
                % (project.version, project.dist_version, DISTRIBUTION_PROPERTY,
                   project.get_property(DISTRIBUTION_PROPERTY)))
