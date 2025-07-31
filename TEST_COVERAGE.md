# Test Coverage Report

Last updated: 2025-07-31

## Coverage Summary

Overall coverage: 100%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.11.13, pytest-8.4.1, pluggy-1.6.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: cov-6.2.1, asyncio-1.0.0, anyio-4.9.0, hypothesis-6.135.26, mock-3.14.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 240 items

tests/clients_test.py .................................................. [ 20%]
........................................................................ [ 50%]
..............................                                           [ 63%]
tests/helpers_test.py ..........................................         [ 80%]
tests/objects_property_based_test.py .........                           [ 84%]
tests/objects_test.py .....................................              [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.13-final-0 _______________

Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__about__.py       7      0   100%
src/fedfred/__init__.py       11      0   100%
src/fedfred/clients.py      1912      0   100%
src/fedfred/helpers.py       600      0   100%
src/fedfred/objects.py       195      0   100%
----------------------------------------------
TOTAL                       2725      0   100%
Coverage XML written to file coverage.xml
====================== 240 passed, 15 warnings in 50.11s =======================
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
