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
plugins: anyio-4.8.0, asyncio-0.15.1, cov-3.0.0, hypothesis-6.129.2, mock-3.14.0
collected 71 items

tests/fedfred_test.py ...............................sssssssssssssssssss [ 70%]
ssssssssssss                                                             [ 87%]
tests/fred_data_test.py .........                                        [100%]

=============================== warnings summary ===============================
../../../.cache/pypoetry/virtualenvs/fedfred-zTCfcE3D-py3.10/lib/python3.10/site-packages/pytest_cov/plugin.py:256
  /home/runner/.cache/pypoetry/virtualenvs/fedfred-zTCfcE3D-py3.10/lib/python3.10/site-packages/pytest_cov/plugin.py:256: PytestDeprecationWarning: The hookimpl CovPlugin.pytest_configure_node uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(optionalhook=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    def pytest_configure_node(self, node):

../../../.cache/pypoetry/virtualenvs/fedfred-zTCfcE3D-py3.10/lib/python3.10/site-packages/pytest_cov/plugin.py:265
  /home/runner/.cache/pypoetry/virtualenvs/fedfred-zTCfcE3D-py3.10/lib/python3.10/site-packages/pytest_cov/plugin.py:265: PytestDeprecationWarning: The hookimpl CovPlugin.pytest_testnodedown uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(optionalhook=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    def pytest_testnodedown(self, node, error):

tests/fedfred_test.py: 31 warnings
  /home/runner/.cache/pypoetry/virtualenvs/fedfred-zTCfcE3D-py3.10/lib/python3.10/site-packages/_pytest/python.py:148: PytestUnhandledCoroutineWarning: async def functions are not natively supported and have been skipped.
  You need to install a suitable plugin for your async framework, for example:
    - anyio
    - pytest-asyncio
    - pytest-tornasync
    - pytest-trio
    - pytest-twisted
    warnings.warn(PytestUnhandledCoroutineWarning(msg.format(nodeid)))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------- coverage: platform linux, python 3.10.16-final-0 ----------
Name                       Stmts   Miss  Cover
----------------------------------------------
src/fedfred/__init__.py        3      0   100%
src/fedfred/fedfred.py      1508    999    34%
src/fedfred/fred_data.py     184     17    91%
----------------------------------------------
TOTAL                       1695   1016    40%

================= 40 passed, 31 skipped, 33 warnings in 3.85s ==================
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
