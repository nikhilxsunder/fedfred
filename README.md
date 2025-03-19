# fedfred

## A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED

<div align="center">
    <img src="https://raw.githubusercontent.com/nikhilxsunder/fedfred/main/docs/source/_static/fedfred-logo.png" width="30%" alt="FedFred Logo">
</div>

<div align="center">
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg" alt="Build and test GitHub"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml/badge.svg" alt="Analyze Status"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml/badge.svg" alt="Test Status"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
    <a href="https://pypi.org/project/fedfred/"><img src="https://img.shields.io/pypi/v/fedfred.svg" alt="PyPI version"></a>
    <a href="https://pepy.tech/projects/fedfred"><img src="https://static.pepy.tech/badge/fedfred" alt="PyPI Downloads"></a>
    <a href="https://www.bestpractices.dev/projects/10158"><img src="https://www.bestpractices.dev/projects/10158/badge"></a>
</div>

### Features

- Pandas/Polars DataFrame outputs.
- Native support for asynchronous requests (async).
- All method outputs are mapped to dataclasses for better usability.
- Local cacheing for easier data access and faster execution times.
- Built-in rate limiter that doesn't exceed 120 calls per minute (ignores local caching).
- GeoPandas outputs for geographical data (FRED-Maps/GeoFRED)
- MyPy compatible type stubs.

### Installation

You can install the package using pip:

```sh
pip install fedfred
```

### Rest API Usage

I recommend consulting the documentation at:
https://nikhilxsunder.github.io/fedfred/

Here is a simple example of how to use the package:

```python
# FredAPI
import fedfred as fd
api_key = 'your_api_key'
fred = fd.FredAPI(api_key)

# Get Series Observations as a pandas DataFrame
gdp = fred.get_series_observations('GDP')
gdp.head()

# Get Series Observations as a pandas DataFrame (async)
import asyncio
async def main():
    fred = fd.FredAPI(api_key).Async
    gdp = fred.get_series_observations('GNPCA')
    print(observations.head())
asyncio.run(main())
```

### Important Notes

- OpenSSF Badge in progress.
- Store your API keys and secrets in environment variables or secure storage solutions.
- Do not hardcode your API keys and secrets in your scripts.
- XML filetype (file_type='xml') is currently not supported but will be in a future update

### Continuous Integration

FedFred uses GitHub Actions for continuous integration. The following workflows run automatically:

- **Build and Test**: Triggered on every push and pull request to verify the codebase builds and tests pass
- **Analyze**: Runs static code analysis to identify potential issues
- **Test**: Comprehensive test suite with coverage reporting
- **CodeQL**: Security analysis to detect vulnerabilities

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
poetry run pytest tests/test_specific_module.py
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

### License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](https://github.com/nikhilxsunder/fedfred/blob/main/LICENSE) file for details.
