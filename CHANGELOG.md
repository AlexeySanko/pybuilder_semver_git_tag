PyBuilder SemVer Git Tag Plugin [![Build Status](https://travis-ci.org/AlexeySanko/pybuilder_semver_git_tag.svg?branch=master)](https://travis-ci.org/AlexeySanko/pybuilder_semver_git_tag)
=======================
1.2.0
---
- take `project.name` from repository name (value from `build.py` overwrites it)

1.1.0
---
- `coverage<4.4.2` - wait PyBuilder fix
- add default initialization on import stage (work with command line properties)
- `__version__` added

1.0.7
-----
- Re-upload to PyPi

1.0.6
-----
- Added tag prefix with property `semver_git_tag_version_prefix`
- For release added possibility to check that changelog file was changed since previous release tag

1.0.5
-----
- Travis deployment added