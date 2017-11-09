import sys
from pybuilder.core import Author, use_plugin, init

# Eating your own dog food
# This is only necessary for bootstrap
sys.path.insert(0, 'src/main/python')

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.frosted")
use_plugin("python.pylint")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("python.unittest")
use_plugin("filter_resources")
# third party plugins
use_plugin('pypi:pybuilder_pylint_extended')


# Eating your own dog food. Set version from git tag
import pybuilder_semver_git_tag


name = "pybuilder_semver_git_tag"
authors = [Author('Alexey Sanko', 'alexeycount@gmail.com')]
url = 'https://github.com/AlexeySanko/pybuilder_semver_git_tag'
description = 'Please visit {0} for more information!'.format(url)
license = 'Apache License, Version 2.0'
summary = 'PyBuilder SemVer Git Tag Plugin'

default_task = ['clean', 'analyze', 'publish']


@init
def filter_settings(project):
    # filter target files
    project.set_property('filter_resources_target', '$dir_dist')
    # provide verions and other properties
    project.get_property("filter_resources_glob").append(
        "%s/version.py" % name)


@init
def set_properties(project, logger):
    # dependencies
    project.build_depends_on('mock')
    project.depends_on('GitPython')
    project.depends_on('semver')

    # coverage
    project.set_property("coverage_reset_modules", True)

    # flake8
    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_break_build', True)

    # frosted
    project.set_property("frosted_break_build", True)
    project.set_property("frosted_include_test_sources", True)

    # semver git tag
    project.set_property('semver_git_tag_changelog', 'CHANGELOG.md')

    # distutils
    project.set_property('distutils_commands', ['bdist_wheel'])
    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ])
