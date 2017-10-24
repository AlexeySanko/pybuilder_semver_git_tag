PyBuilder SemVer Git Tag Plugin [![Build Status](https://travis-ci.org/AlexeySanko/pybuilder_semver_git_tag.svg?branch=master)](https://travis-ci.org/AlexeySanko/pybuilder_semver_git_tag)
=======================

Plugin for PyBuilder which provides dynamic project version based on SemVer git tag
More about SemVer: http://semver.org/

PEP-440 compatibility
---------------------

Note that the plugin doesn't follow PEP-440 according develop versions because PyPi repo denies to upload existing version.
For example, we have release `1.0.0` and develop `1.1.dev0` if we upload it we will need to increment `dev0` part next time. So any automatic build will need to increment version.

Behaviour
---------
Plugin seek last tag which satisfies SemVer. If wasn't found - return execution to the core and warning about it.
If current repo is dirty (has uncommitted changes) or tag commit isn't equal last commit - the plugin increment version with specified part (major, minor or patch) and add `.dev` suffix.
If current repo isn't dirty and tag commit is equal last commit - we're on release tag and the plugin copy version from tag.

How to use
----------

Add plugin dependency to your `build.py`
```python
use_plugin('pypi:pybuilder_semver_git_tag')

@init
def set_properties(project, logger):
    # Semver Git Tag properties
    # Part for develop increment - 'major', 'minor' or 'patch'
    project.set_property('semver_git_tag_increment_part', 'patch')
    # Git repository directory path. If None parent directory for build.py will be used
    project.set_property_if_unset('semver_git_tag_repo_dir', None)
```
