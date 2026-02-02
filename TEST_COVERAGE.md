# Test Coverage Report

Last updated: 2026-02-02

## Coverage Summary

Overall coverage: 100%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: anyio-4.10.0, asyncio-1.2.0, hypothesis-6.138.15, cov-7.0.0, mock-3.15.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 292 items

tests/clients_test.py .................................................. [ 17%]
........................................................................ [ 41%]
..............................                                           [ 52%]
tests/config_test.py ...                                                 [ 53%]
tests/helpers_test.py .................................................. [ 70%]
.............................                                            [ 80%]
tests/objects_test.py .................................................. [ 97%]
........                                                                 [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.14-final-0 _______________

Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
src/fedfred/__about__.py       9      0   100%
src/fedfred/__init__.py        9      0   100%
src/fedfred/clients.py      1970      0   100%
src/fedfred/config.py         28      0   100%
src/fedfred/helpers.py       666      0   100%
src/fedfred/objects.py       307      0   100%
--------------------------------------------------------
TOTAL                       2989      0   100%
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
====================== 292 passed, 14 warnings in 45.05s =======================
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
