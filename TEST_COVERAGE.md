# Test Coverage for Major Features

This document tracks how our test policy has been implemented for major features.

## Core Features and Their Tests

---------- coverage: platform darwin, python 3.13.1-final-0 ----------
Name Stmts Miss Cover

---

src/fedfred/**init**.py 3 0 100%
src/fedfred/fedfred.py 898 412 54%
src/fedfred/fred_data.py 180 32 82%

---

TOTAL 1081 444 59%

## Recent Features Added in v1.1.0

All major features added in version 1.1.0 included corresponding test implementations:

- Sphinx Documentation Structure: Added with tests for documentation generation and content verification
- Documentation Workflow (GitHub Pages): Tests ensure the workflow runs correctly and publishes the documentation
- Full conversion to poetry: Added with tests for dependency management and build process
- Sign-Release Workflow: Tests verify the signing process and release creation
- OpenSSF Passing: Added with tests for security compliance and best practices adherence
