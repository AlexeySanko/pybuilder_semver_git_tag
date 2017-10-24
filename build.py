from pybuilder.core import Author, use_plugin, init

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.frosted")
use_plugin("python.pylint")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("python.unittest")


name = "pybuilder_semver_git_tag"
version = '1.0.0'
authors = [Author('Alexey Sanko', 'alexeycount@gmail.com')]
url = 'https://github.com/AlexeySanko/pybuilder_semver_git_tag'
description = 'Please visit {0} for more information!'.format(url)
license = 'Apache License, Version 2.0'
summary = 'PyBuilder SemVer Git Tag Plugin'

default_task = ['clean', 'analyze', 'publish']


@init
def set_properties(project):
    # dependencies
    project.build_depends_on('mock')

    # flake8
    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_break_build', True)
    project.set_property('flake8_max_line_length', 80)

    # frosted
    project.set_property("frosted_break_build", True)
    project.set_property("frosted_include_test_sources", True)

    # pylint
    project.set_property("pylint_options", ["--max-line-length=80"])

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
