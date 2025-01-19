# fedfred
## A simple python wrapper for interacting with the US Federal Reserve database: FRED
## This package is still in beta please try it out and please report any comments, concerns, and issues.

[![Build and test GitHub](https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg)](https://github.com/nikhilxsunder/fedfred/actions)
[![PyPI version](https://img.shields.io/pypi/v/fedfred.svg)](https://pypi.org/project/fedfred/)
[![Downloads](https://img.shields.io/pypi/dm/fedfred.svg)](https://pypi.org/project/fedfred/)

### Installation

You can install the package using pip:

```sh
pip install fedfred
```

### Rest API Usage

I recommend consulting the offical FRED API documentation at: 
https://fred.stlouisfed.org/docs/api/fred
Here is a simple example of how to use the package:

```python
from fedfred import FredAPI

api_key = 'your_api_key'
client = FredAPI(api_key)

# Get Series: GDP

gdp = fred.get_series('GDP')
print(gdp)
```

### Important Notes

- Currently all all responses are either JSON or XML depending on what is specified in the file_type arg (defalt value = 'json').
- Store your API keys and secrets in environment variables or secure storage solutions.
- Do not hardcode your API keys and secrets in your scripts.

### Features

- Get Economic Data
- Easy to use

## Next Update 

- ALFRED
    - Vintage Dates

### Planned Updates

- Output data to pandas or polars
- FRED Maps API
    - CartoPy outputs
- ALFRED

### Contributing

Contributions are welcome! Please open an issue or submit a pull request.

### License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
