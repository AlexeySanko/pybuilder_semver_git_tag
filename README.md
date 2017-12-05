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
Plugin seek last tag which satisfies SemVer.
* If wasn't found - return execution to the core and warning about it.
* If current repo is dirty (has uncommitted changes) or tag commit isn't equal last commit - the plugin increment version with specified part (major, minor or patch) and add `.dev` suffix.
* If current repo isn't dirty and tag commit is equal last commit - we're on release tag and the plugin copy version from tag.

Changelog changes
------
Additional features of plugin:
- check for release tag that changelog file was changes since previous release tag - `semver_git_tag_changelog`
- take `project.name` from Git repository name.

How to use
----------

Add plugin dependency to your `build.py`
```python
use_plugin('pypi:pybuilder_semver_git_tag')
```

Project properties should be passed from command line:
```
pyb clean analyze publish -P semver_git_tag_increment_part=minor
```
Or within initializers, but in this case some version-related properties could 
be spoiled. Also output will have default `1.0.dev0` version before `prepare` 
task what could bring confusion. So command line usage is preferred way.

Properties
----------

Plugin has next properties with provided defaults

| Name | Type | Default Value | Description |
| --- | --- | --- | --- |
| semver_git_tag_increment_part | string | patch | Part for develop version increment - `major`, `minor` or `patch` (SemVer version: `major.minor.patch`) |
| semver_git_tag_repo_dir | string | None | Git repository directory full path. If `None` directory with` build.py` file will be used |
| semver_git_tag_changelog | string | None | Relative path with name of changelog file. If not `None` for release tag plugin will check that changelog was changed since previous tag release |
| semver_git_tag_version_prefix | string | '' | Specific prefix of release tags. For example, `v` for `v1.2.3` tag |