# Test Coverage Report

Last updated: 2025-04-14

## Coverage Summary

Overall coverage: 14%

## Detailed Coverage

```
============================= test session starts ==============================
platform linux -- Python 3.11.11, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/runner/work/fedfred/fedfred
configfile: pyproject.toml
plugins: cov-6.1.1, hypothesis-6.131.0, asyncio-0.26.0, anyio-4.9.0, mock-3.14.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 9 items

tests/objects_test.py .........                                          [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.11-final-0 _______________

Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__about__.py       7      7     0%
src/fedfred/__init__.py        4      0   100%
src/fedfred/clients.py      1879   1725     8%
src/fedfred/helpers.py       534    479    10%
src/fedfred/objects.py       192     32    83%
----------------------------------------------
TOTAL                       2616   2243    14%
Coverage XML written to file coverage.xml
========================= 9 passed, 1 warning in 3.33s =========================
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
