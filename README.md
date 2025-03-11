# fedfred
## A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED

<div align="center">
    <img src="https://raw.githubusercontent.com/nikhilxsunder/fedfred/main/docs/images/fedfred-logo.png" width="30%" alt="FedFred Logo">
</div>

<div align="center">
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg" alt="Build and test GitHub"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml/badge.svg" alt="Analyze Status"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml/badge.svg" alt="Test Status"></a>
    <a href="https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml"><img src="https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
    <a href="https://pypi.org/project/fedfred/"><img src="https://img.shields.io/pypi/v/fedfred.svg" alt="PyPI version"></a>
    <a href="https://pepy.tech/projects/fedfred"><img src="https://static.pepy.tech/badge/fedfred" alt="PyPI Downloads"></a>
    <a href="https://pypistats.org/packages/fedfred"><img src="https://img.shields.io/pypi/dm/fedfred" alt="PyPI Monthly Downloads"></a>
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
https://github.com/nikhilxsunder/fedfred/tree/main/docs/fedfred.pdf

Here is a simple example of how to use the package:

```python
# FredAPI
import fedfred as fd

api_key = 'your_api_key'
fred = fd.FredAPI(api_key)

# Get Series: GDP
gdp = fred.get_series('GDP')
gdp.head()
```

### Important Notes

- OpenSSF Badge in progress.
- Store your API keys and secrets in environment variables or secure storage solutions.
- Do not hardcode your API keys and secrets in your scripts.
- XML filetype (file_type='xml') is currently not supported but will be in a future update

### Contributing

Contributions are welcome! Please open an issue or submit a pull request.

### License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
