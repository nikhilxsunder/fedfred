# Changelog

All notable changes to FedFred will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.1] - 2025-07-08

### Added

- Complete testing suite

### Fixed

- Minor fixes to source modules

## [2.1.0] - 2025-04-30

### Added

- Added more testing classes (still incomplete)

### Fixed

- Rebuilt documentation using pydata sphinx theme
- Added better documentnation pages with dynamic elements
- Reindexing with Bing Webmaster, Index Now, annd Google Search Console
- Logic fixes for parameter validation
- Nested methods for FredHelpers class refactored

## [2.0.9] - 2025-04-14 (PUBLISHING FIX)

## [2.0.8] - 2025-04-14 (YANKED)

## [2.0.7] - 2025-04-14 (YANKED)

## [2.0.6] - 2025-04-14 (YANKED)

## [2.0.5] - 2025-04-14 (YANKED)

## [2.0.4] - 2025-04-14 (YANKED)

## [2.0.3] - 2025-04-14 (YANKED)

## [2.0.2] - 2025-04-14 (YANKED)

## [2.0.1] - 2025-04-14 (YANKED)

## [2.0.0] - 2025-04-14

### Added

- [clients_property_based_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/fedfred_property_based_test.py)
- [objects_property_based_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/fred_data_property_based_test.py)
- [helpers_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/helpers_test.py)
- [helpers_property_based_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/helpers_property_based_test.py)
- Type annotations directly in source code
- More comprehensive error handling for all methods
- [asyncache](https://pypi.org/project/asyncache/) dependency for cachetools async decorator
- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md) badges for 'in repositories' and 'Socket'
- Optional DataFrame support for [dask](https://pypi.org/project/dask/)
- OpenSSF Silver & Gold
- [DCO.md](https://github.com/nikhilxsunder/fedfred/blob/main/DCO.md)
- [ROADMAP.md](https://github.com/nikhilxsunder/fedfred/blob/main/ROADMAP.md)
- helper methods now housed in [helpers.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/helpers.py) FredHelpers class
- polars dependency moved to extra dependency group
- dunder methods for all classes
- appropriate dunder modules and corresponding precommit hooks/scripts
- [polars-st](https://pypi.org/project/polars-st/) added to polars dependency group for polars geodataframes
- [layout.html](https://github.com/nikhilxsunder/fedfred/blob/main/docs/source/_templates/layout.html)
- [BingSiteAuth.xml](https://github.com/nikhilxsunder/fedfred/blob/main/docs/source/BingSiteAuth.xml)
- [/conda-forge/meta.yaml](https://github.com/nikhilxsunder/fedfred/blob/main/conda-forge/meta.yaml)

### Removed

- .pyi type stub files
- 'file_type' arg for all methods (will only support JSON)
- update_fedstock.py

### Fixed

- Caching logic rework for better type annotations and execution
- Cache type changed from TTL to FIFO
- Error handling logic moved to private helper method.
- Async helper method logic rework to reduce boilerplate code
- Date args now accept datetime objects
- Semicolon-seperated string args now accept list objects
- Dataclass object outputs simplified and output types adjusted accordingly
- Dataclass objects now have async methods
- fedfred.py renamed to [clients.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/clients.py)
- fred_data.py renamed to [objects.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/objects.py)
- fedfred_test.py renamed to [clients_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/clients_test.py)
- fred_data_test.py renamed to [objects_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/objects_test.py)
- update_feedstock.yml merged into [main.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/main.yml)
- [tox.ini](https://github.com/nikhilxsunder/fedfred/blob/main/tox.ini) config fixed
- [conf.py](https://github.com/nikhilxsunder/fedfred/blob/main/docs/source/conf.py)

## [1.2.9] - 2025-03-20

### Added

- Added codecov
- Conda-forge packaging and distribution
- Documentation for Anaconda

### Changed

- [main.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/main.yml) updated for conda

## [1.2.8] - 2025-03-20

### Changed

- Moved type hinting and stub packages to optional dependency group
- Duplicated type packages in dev dependencies
- [tox.ini](https://github.com/nikhilxsunder/fedfred/blob/main/tox.ini) adjusted

## [1.2.7] - 2025-03-20

### Added

- [cachetools](https://pypi.org/project/cachetools/) (prepping for conda release)
- [types-cachetools](https://pypi.org/project/types-cachetools/)
- scripts/[sync_conda_recipe.py](https://github.com/nikhilxsunder/fedfred/blob/main/scripts/sync_conda_recipe.py)

### Changed

- [test.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/test.yml) dropped linting, type-checking, and security analysis, ([analyze.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/analyze.yml) already does this.)
- "test-coverage.yml" merged into [test.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/test.yml)
- [pre-commit-config.yaml](https://github.com/nikhilxsunder/fedfred/blob/main/pre-commit-config.yaml) updated for conda

### Removed

- [cacheout](https://pypi.org/project/cacheout/) dependency due to conda issue

## [1.2.6] - 2025-03-19

### Fixed

- publishing patch for toml version error

## [1.2.5] - 2025-03-19

### Fixed

- publishing patch for gpg keys

## [1.2.4] - 2025-03-19

### Changed

- "sign-release.yml" merged into [main.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/main.yml)

### Fixed

- test coverage error due to missing async dependency

## [1.2.3] - 2025-03-19

### Fixed

- Minor workflow config patch

## [1.2.2] - 2025-03-19

### Added

- [tox.ini](https://github.com/nikhilxsunder/fedfred/blob/main/tox.ini)
- [test-coverage.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/test-coverage.yml)
- Dev dependency: [tox](https://pypi.org/project/tox/)
- Dev dependency: [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)
- Dev dependency: [pytest-mock](https://pypi.org/project/pytest-mock/)

### Changed

- "\_test.py" -> [fedfred_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/fedfred_test.py)
- [main.yml](https://github.com/nikhilxsunder/fedfred/blob/main/.github/workflows/main.yml) publishing backend
- [pre-commit-config.yaml](https://github.com/nikhilxsunder/fedfred/blob/main/pre-commit-config.yaml)
- [poetry.lock](https://github.com/nikhilxsunder/fedfred/blob/main/poetry.lock)
- [fedfred-logo.png](https://github.com/nikhilxsunder/fedfred/blob/main/docs/source/_static/fedfred-logo.png)
- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)
- [SECURITY.md](https://github.com/nikhilxsunder/fedfred/blob/main/SECURITY.md)
- [TEST_COVERAGE.md](https://github.com/nikhilxsunder/fedfred/blob/main/TEST_COVERAGE.md)

## [1.2.1] - 2025-03-15

### Added

- Google analytics tag for sphinx
- Dev dependency 'sphinxcontrib.googleanalytics'

## [1.2.0] - 2025-03-14

### Added

- FredAPI.Maps subclass
- FredAPI.Async subclass
- FredAPI.Async.Maps subclass
- [cacheout](https://pypi.org/project/cacheout/) dependency
- [fred_data_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/fred_data_test.py)

### Fixed

- Async logic (asyncio.run cannot be called within a loop)
- Caching logic

### Deprecated

- async_mode -> bool for all classes
- FredMapsAPI class
- [typed-diskcache](https://pypi.org/project/typed-diskcache/) dependency

## [1.1.0] - 2025-03-12

### Added

- Sphinx Documentation Structure Created
- Documentation Workflow (Github Pages)
- Docs Workflow
- [CONTRIBUTIONS.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)
- [SECURITY.md](https://github.com/nikhilxsunder/fedfred/blob/main/SECURITY.md)
- [CODE_OF_CONDUCT.md](https://github.com/nikhilxsunder/fedfred/blob/main/CODE_OF_CONDUCT.md)
- [CHANGELOG.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)
- [bug_report.md](https://github.com/nikhilxsunder/fedfred/blob/main/.github/ISSUE_TEMPLATE/bug_report.md)
- [feature_report.md](https://github.com/nikhilxsunder/fedfred/blob/main/.github/ISSUE_TEMPLATE/feature_report.md)
- GPG Key file
- Sign-Release Workflow
- OpenSSF Passing
- Full conversion to poetry
- Added dev dependencies
- [pre-commit-config.yaml](https://github.com/nikhilxsunder/fedfred/blob/main/pre-commit-config.yaml) for devs

### Changed

- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md) sections
- CodeQL schedule changed to daily

### Removed

- setuptools backend

### Fixed

- PEP257 compliance for docstrings

## [1.0.26] - 2025-03-11

### Fixed

- minor functionality patch

## [1.0.25] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.24] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.23] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.22] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.21] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.20] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.19] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.18] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.17] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.16] - 2025-03-11 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.15] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.14] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.13] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.12] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.11] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.10] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.9] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.8] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.7] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.6] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.5] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.4] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.3] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.2] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.1] - 2025-03-10 (YANKED RELEASE)

### Fixed

- minor functionality patch

## [1.0.0] - 2025-03-10

### Added

- [polars](https://pypi.org/project/polars/) output
- [pandas](https://pypi.org/project/pandas/) output
- [geopandas](https://pypi.org/project/geopandas/) output
- Type stubs ([fedfred.pyi](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/fedfred.pyi), [fred_data.pyi](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/fred_data.pyi), [**init**.pyi](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.pyi))
- Local caching ([typed-diskcache](https://pypi.org/project/typed-diskcache/))
- Async support ([httpx](https://pypi.org/project/httpx/))
- Rate limiter ([tenacity](https://pypi.org/project/tenacity/))
- Data Classes for Method Outputs ([fred_data.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/fred_data.py) module)
- Unit Testing ([\_test.py](https://github.com/nikhilxsunder/fedfred/blob/main/tests/_test.py))
- Analyze workflow ([analyze.yml](https://github.com/nikhilxsunder/fedfred/blob/.github/workflows/analyze.yml))
- CodeQl workflow ([codeql.yml])(https://github.com/nikhilxsunder/fedfred/blob/.github/workflows/codeql.yml)
- Testing Workflow ([test.yml])(https://github.com/nikhilxsunder/fedfred/blob/.github/workflows/test.yml)
- Logo Image
- [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py) import all
- Import dataclasses in [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py):
- Mypy type stub recognition ([py.typed](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/py.typed))

### Changed

- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md) sections
- Package description (now "feature-rich" instead of "simple")
- Package backwards compatible to Python >= 3.7
- Api request library in favor of [httpx](https://pypi.org/project/httpx/)
- Documentation link

### Removed

- [requests](https://pypi.org/project/requests/) dependency

### Fixed

- [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py) module docstring

## [0.0.7] - 2025-01-29

### Changed

- Version bump for publishing error.

## [0.0.6] - 2025-01-29 (DELETED RELEASE)

### Fixed

- Issue with incorrect import syntax in [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py)

## [0.0.5] - 2025-01-29

### Added

- "Latest Update" in [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)
- FredMapsAPI Class for interacting with GeoFred
- Methods for FredMapsAPI
- Class and Method docstrings for FredMapsAPI Class
- FredMapsAPI Class importable in [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py)

### Changed

- "Installation" in [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)

## [0.0.4] - 2025-01-29

### Changed

- Version bump for publishing error

### Added

## [0.0.3] - 2025-01-19

### Added

- Added methods to FredAPI class to interact with all endpoints
- Completed Class, Method, and Module Docstrings
- Populated [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)

## [0.0.2] - 2025-01-17

### Added

- FredAPI Class
- Method structure notes in [fedfred.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/fedfred.py)
- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md) Badges
- Main publishing worklow

## [0.0.1] - 2025-01-16 (DELETED RELEASE)

### Added

- Initial pre-release of fedfred
- Core functionality for making api requests
- License file
- [README.md](https://github.com/nikhilxsunder/fedfred/blob/main/README.md)
- [fedfred.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/fedfred.py)
- [**init**.py](https://github.com/nikhilxsunder/fedfred/blob/main/src/fedfred/__init__.py)
- [requests](https://pypi.org/project/requests/) dependency
- [pyproject.toml](https://github.com/nikhilxsunder/fedfred/blob/main/pyproject.toml)
- initial directory structure
- setuptools for build backend

[Unreleased]: https://github.com/nikhilxsunder/fedfred/compare/v2.1.1...HEAD
[2.1.1]: https://github.com/nikhilxsunder/fedfred/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.9...v2.1.0
[2.0.9]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.8...v2.0.9
[2.0.8]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.7...v2.0.8
[2.0.7]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.6...v2.0.7
[2.0.6]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.5...v2.0.6
[2.0.5]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.4...v2.0.5
[2.0.4]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.3...v2.0.4
[2.0.3]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.2...v2.0.3
[2.0.2]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/nikhilxsunder/fedfred/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.9...v2.0.0
[1.2.9]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.8...v1.2.9
[1.2.8]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.7...v1.2.8
[1.2.7]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.6...v1.2.7
[1.2.6]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/nikhilxsunder/fedfred/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/nikhilxsunder/fedfred/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.26...v1.1.0
[1.0.26]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.25...v1.0.26
[1.0.25]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.24...v1.0.25
[1.0.24]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.23...v1.0.24
[1.0.23]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.22...v1.0.23
[1.0.22]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.21...v1.0.22
[1.0.21]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.20...v1.0.21
[1.0.20]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.19...v1.0.20
[1.0.19]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.18...v1.0.19
[1.0.18]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.17...v1.0.18
[1.0.17]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.16...v1.0.17
[1.0.16]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.15...v1.0.16
[1.0.15]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.14...v1.0.15
[1.0.14]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.13...v1.0.14
[1.0.13]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.12...v1.0.13
[1.0.12]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.11...v1.0.12
[1.0.11]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.10...v1.0.11
[1.0.10]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.6...v1.0.7
[1.0.5]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/nikhilxsunder/fedfred/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.7...v1.0.0
[0.0.7]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.6...v0.0.7
[0.0.5]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/nikhilxsunder/fedfred/compare/v0.0.1...v0.0.2
