# Test Coverage Report

Last updated: 2025-06-12

## Coverage Summary

Overall coverage: 16%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.11.12, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: mock-3.14.0, anyio-4.9.0, cov-6.1.1, asyncio-0.26.0, hypothesis-6.131.9
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 18 items

tests/objects_test.py ..................                                 [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.12-final-0 _______________

Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__about__.py       7      0   100%
src/fedfred/__init__.py       11      0   100%
src/fedfred/clients.py      1880   1725     8%
src/fedfred/helpers.py       613    537    12%
src/fedfred/objects.py       195     20    90%
----------------------------------------------
TOTAL                       2706   2282    16%
Coverage XML written to file coverage.xml
======================== 18 passed, 1 warning in 3.63s =========================
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
