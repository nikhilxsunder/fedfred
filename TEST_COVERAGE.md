# Test Coverage Report

Last updated: 2025-03-21

## Coverage Summary

Overall coverage: 40%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.11.11, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: asyncio-0.15.1, hypothesis-6.129.4, cov-6.0.0, anyio-4.9.0, mock-3.14.0
collected 73 items

tests/fedfred_test.py .................................................. [ 68%]
..............                                                           [ 87%]
tests/fred_data_test.py .........                                        [100%]

---------- coverage: platform linux, python 3.11.11-final-0 ----------
Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__init__.py        3      0   100%
src/fedfred/fedfred.py      1508    992    34%
src/fedfred/fred_data.py     184     17    91%
----------------------------------------------
TOTAL                       1695   1009    40%
Coverage XML written to file coverage.xml


============================== 73 passed in 3.63s ==============================
```

## Running Test Coverage Locally

To run the test suite with coverage:

```bash
pytest --cov=src/fedfred tests/
```

For a detailed HTML report:

```bash
pytest --cov=src/fedfred tests/ --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the report.

## Coverage Goals

- Maintain at least 80% overall coverage
- All public APIs should have 100% coverage
- Focus on testing edge cases and error conditions
