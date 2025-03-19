# Test Coverage Report

Last updated: 2025-03-19

## Coverage Summary

Overall coverage: 40%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: asyncio-0.15.1, hypothesis-6.129.4, cov-6.0.0, anyio-4.9.0, mock-3.14.0
collected 71 items

tests/fedfred_test.py .................................................. [ 70%]
............                                                             [ 87%]
tests/fred_data_test.py .........                                        [100%]

---------- coverage: platform linux, python 3.10.16-final-0 ----------
Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__init__.py        3      0   100%
src/fedfred/fedfred.py      1508    999    34%
src/fedfred/fred_data.py     184     17    91%
----------------------------------------------
TOTAL                       1695   1016    40%


============================== 71 passed in 3.78s ==============================
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
