<div align="center">
    <img src="https://raw.githubusercontent.com/nikhilxsunder/fedfred/v4-dev/docs/source/_static/fedfred_banner.png"  alt="FedFred Logo">
</div>

## A modern python package for interacting with the Federal Reserve Bank of St. Louis FRED, GeoFRED, ALFRED, and FRASER APIs.

| | |
|---|---|
| **CI / Quality** | [![Build](https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml) [![Analyze](https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml) [![Tests](https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml) |
| **Security** | [![CodeQL](https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml) [![Best Practices](https://www.bestpractices.dev/projects/10158/badge)](https://www.bestpractices.dev/projects/10158) [![Socket](https://socket.dev/api/badge/pypi/package/fedfred/3.0.0?artifact_id=tar-gz)](https://socket.dev/pypi/package/fedfred/overview/3.0.0/tar-gz) |
| **Coverage** | [![Coverage](https://codecov.io/gh/nikhilxsunder/fedfred/graph/badge.svg?token=VVEK415DF6)](https://codecov.io/gh/nikhilxsunder/fedfred) |
| **Packaging** | [![Repology](https://repology.org/badge/tiny-repos/python%3Afedfred.svg)](https://repology.org/project/python%3Afedfred/versions) |
| **Distribution** | [![PyPI](https://img.shields.io/pypi/v/fedfred.svg)](https://pypi.org/project/fedfred/) [![Conda](https://anaconda.org/conda-forge/fedfred/badges/version.svg)](https://anaconda.org/conda-forge/fedfred) |
| **Usage** | [![PyPI Downloads](https://static.pepy.tech/badge/fedfred)](https://pepy.tech/projects/fedfred) [![Conda Downloads](https://anaconda.org/conda-forge/fedfred/badges/downloads.svg)](https://anaconda.org/conda-forge/fedfred) |
| **Research / Index** | [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17635942.svg)](https://doi.org/10.5281/zenodo.17635942) [![Awesome](https://awesome.re/badge.svg)](https://github.com/wilsonfreitas/awesome-quant) |

## Table of Contents

- [Main Features](#main-features)
- [Used by & Featured In](#used-by--featured-in)
- [Installation](#installation)
- [Rest API Usage](#rest-api-usage)
- [Important Notes](#important-notes)
- [Continuous Integration](#continuous-integration)
- [Development](#development)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)


## Main Features

- Full endpoint coverage of FRED, ALFRED, GeoFRED, and FRASER.
- Pandas DataFrames are the native output for FRED observations.
- GeoPandas GeoDataFrame as native output for GeoFRED observations
- Built in support for alternative DataFrame and GeoDataFrame providers such as polars and dask.
- Intuitive handling of ALFRED data revisions and vintage dates via the Alfred client class.
- Local caching for easier data access and faster execution times.

## Used by & Featured In

> Note: Listing does not imply endorsement or affiliation.

#### Institutions / Organizations
<a href="https://herbert.miami.edu/" title="University of Miami Herbert Business School">
    <img src="https://ft-bschool-rankings.s3.eu-west-2.amazonaws.com/production/images/5c4bdeb1-1c63-4db1-a083-17788dc9e936-695b4305f38b114a94513f7f0a44085c"
         alt="University of Miami Herbert Business School"
         height="75">
</a>

<!--
#### Companies
-->

#### Open-source projects / Repositories
<div align="left">
  <a href="https://github.com/wilsonfreitas/awesome-quant" title="Awesome Quant">
    <img src="https://raw.githubusercontent.com/sindresorhus/awesome/main/media/logo.svg"
         alt="Awesome Quant"
         height="75">
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://conda-forge.org/" title="conda-forge">
    <img src="https://numfocus.org/wp-content/uploads/2018/09/conda-forge-square.png"
         alt="conda-forge"
         height="75">
  </a>
</div>

### Installation

You can install the package using pip:

```sh
pip install fedfred
```

Or install from conda-forge:

```sh
conda install -c conda-forge fedfred
```

For type checking support, install with optional type stubs:

```sh
pip install fedfred[types]
```

For use with Polars DataFrames and GeoDataFrames, install with:

```sh
pip install fedfred[polars]
```

For use with Dask DataFrames and GeoDataFrames, install with:

```sh
pip install fedfred[dask]
```

We recommend using a virtual environment with either installation method.

### Rest API Usage

I recommend consulting the documentation at:
https://nikhilxsunder.github.io/fedfred/

Here is a simple example of how to use the package:

```python
# FredAPI
import fedfred as fd
fd.set_api_key('your_api_key')
fred = fd.Fred()

# Get Series Observations as a pandas DataFrame
gdp = fred.get_series_observations('GDP')
gdp.head()

# Get Series Observations as a pandas DataFrame (async)
import asyncio
async def main():
    fred = fd.Fred(api_key).AsyncFred
    gdp = fred.get_series_observations('GNPCA')
    print(observations.head())
asyncio.run(main())
```

### Important Notes

- Store your API keys and secrets in environment variables or secure storage solutions.
- Do not hardcode your API keys and secrets in your scripts.
- XML filetype (file_type='xml') is currently not supported but will be in a future update

### Continuous Integration

FedFred uses GitHub Actions for continuous integration. The following workflows run automatically:

- **Build and Test**: Triggered on every push and pull request to verify the codebase builds and tests pass
- **Analyze**: Runs static code analysis to identify potential issues
- **Test**: Comprehensive test suite with coverage reporting
- **CodeQL**: Security analysis to detect vulnerabilities
- **Docs**: Deploys Github Pages website for documentation, built off of sphinx docs.

These checks ensure that all contributions maintain code quality and don't introduce regressions.

Status badges at the top of this README reflect the current state of our CI pipelines.

### Development

FedFred uses standard Python packaging tools:

- **Poetry**: For dependency management and package building
- **pytest**: For testing
- **Sphinx**: For documentation generation

To set up the development environment:

```sh
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/nikhilxsunder/fedfred.git
cd fedfred

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

### Testing

The project uses pytest as its testing framework. Tests are located in the `tests/` directory.

To run the complete test suite:

```sh
poetry run pytest
```

For running tests with coverage reports:

```sh
poetry run pytest --cov=fedfred tests/
```

To run a specific test file:

```sh
poetry run pytest tests/specific_module_test.py
```

#### Test Coverage

We aim to maintain a minimum of 80% code coverage across the codebase. This includes:

- Core functionality: 90%+ coverage
- Edge cases and error handling: 80%+ coverage
- Utility functions: 75%+ coverage

Continuous integration automatically runs tests on all pull requests and commits to the main branch.

#### Test Policy

FedFred requires tests for all new functionality. When contributing:

- All new features must include appropriate tests
- Bug fixes should include tests that verify the fix
- Tests should be added to the automated test suite in the `tests/` directory

## Security

For information about reporting security vulnerabilities in FedFred, please see our [Security Policy](https://github.com/nikhilxsunder/fedfred/blob/main/SECURITY.md).

### Contributing

Contributions are welcome! Please open an issue or submit a pull request.

### Citation

If you use fedfred in your research, projects, or publications, please cite it as follows:

**Plain Text**:

```
Sunder, Nikhil. (2025). fedfred: A Python client for the Federal Reserve Economic Database (FRED) API.
Version 3.0.0. Available at: https://github.com/nikhilxsunder/fedfred
```

**BibTeX**:

```bibtex
@software{fedfred,
  author       = {Nikhil Sunder},
  title        = {fedfred: A Python client for the Federal Reserve Economic Database (FRED) API},
  year         = {2026},
  publisher    = {GitHub},
  version      = {3.0.0},
  doi          = {10.5281/zenodo.17635942},
  url          = {https://github.com/nikhilxsunder/fedfred},
  orcid        = {https://orcid.org/0009-0007-3323-1760}
}
```

You can also download a ready-made citation file from the GitHub repository

### License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/nikhilxsunder/fedfred/blob/main/LICENSE) file for details.
