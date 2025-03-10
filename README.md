# fedfred
## A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED

![Alt text](docs/images/fedfred-logo)

[![Build and test GitHub](https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml)
[![Analyze Status](https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml)
[![Test Status](https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml)
[![CodeQL](https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml)
[![PyPI version](https://img.shields.io/pypi/v/fedfred.svg)](https://pypi.org/project/fedfred/)
[![PyPI Downloads](https://static.pepy.tech/badge/fedfred)](https://pepy.tech/projects/fedfred)

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
