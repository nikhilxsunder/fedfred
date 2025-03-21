# Contributing to FedFred

Thank you for your interest in contributing to FedFred! We welcome contributions of all kinds, including bug reports, feature requests, documentation improvements, and code contributions. This document provides guidelines and instructions to help you get started.

## Table of Contents

- [How to Contribute](#how-to-contribute)
  - [Reporting Issues](#reporting-issues)
- [Static Analysis](#static-analysis)
- [Submitting Code Changes](#submitting-code-changes)
- [Coding Standards](#coding-standards)
- [Code Quality and Warnings](#code-quality-and-warnings)
- [Testing](#testing)
  - [Testing with Assertions](#testing-with-assertions)
- [Documentation](#documentation)
- [License](#license)
- [Contact](#contact)
- [Security Vulnerability Reporting](#security-vulnerability-reporting)
- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Continuous Integration](#continuous-integration)
- [Dynamic Analysis](#dynamic-analysis)
  - [Property-Based Testing with Hypothesis](#property-based-testing-with-hypothesis)
  - [Running Dynamic Analysis Tests](#running-dynamic-analysis-tests)
- [Release Process](#release-process)

## How to Contribute

### Reporting Issues

Before opening a new issue:

- Search the issue tracker to verify the issue hasn't already been reported
- Use our issue templates where available for bugs, features, or documentation
- Provide a clear and descriptive title
- Include detailed information:
  - Steps to reproduce the issue
  - Expected behavior vs. actual behavior
  - Environment details (OS, Python version, etc.)
  - Relevant logs, screenshots, or error messages
- Tag the issue appropriately (bug, enhancement, documentation, etc.)

## Static Analysis

Before major releases, all code undergoes static analysis using multiple tools:

- **pylint**: General code quality and adherence to PEP 8

  - Configured with strict settings (9.0+ score required)
  - `poetry run pylint src/fedfred/`

- **mypy**: Static type checking

  - Configured with strict type checking rules
  - `poetry run mypy src/fedfred/`

- **bandit**: Security-focused static analysis
  - Identifies common security issues in Python code
  - `poetry run bandit -r src/fedfred/`

These checks are automated through:

- Pre-commit hooks (for developers)
- GitHub Actions workflows (for all PRs and releases)
- Required status checks (PRs cannot be merged if static analysis fails)

All identified issues must be addressed before release, either by fixing the code or documenting exceptions with clear justifications.

### Submitting Code Changes

Follow these steps when contributing code:

1. **Fork the Repository**

   - Create your own fork of the repository on GitHub
   - Clone your fork locally

2. **Create a Branch**

   - Create a new branch from `main` with a descriptive name
   - Use a prefix like `feature/`, `fix/`, or `docs/` (e.g., `feature/add-logging`)

3. **Make Your Changes**

   - Follow the coding standards outlined below
   - Write clear commit messages explaining your changes
   - Keep commits focused and logical

4. **Submit a Pull Request**
   - Ensure all tests pass locally
   - Create a PR against the `main` branch
   - Use the PR template to describe your changes
   - Reference related issues (e.g., "Fixes #42")
   - Keep PRs focused on a single objective

### Coding Standards

All code must adhere to these standards:

- Follow [PEP 8](https://peps.python.org/pep-0008/) coding style guidelines
- Use [type hints](https://peps.python.org/pep-0484/) for all function parameters and return values
- Write [PEP 257](https://peps.python.org/pep-0257/) compliant docstrings
  - Include parameter descriptions, return values, and examples
  - Document exceptions raised
- Use meaningful variable and function names that describe their purpose
- Keep functions focused and concise (aim for < 50 lines per function)
- Avoid unnecessary complexity and nested code blocks
- Include comments for complex logic or non-obvious behavior

### Code Quality and Warnings

We strive to maintain a codebase with minimal linting warnings:

- All new code should pass pylint, mypy, and bandit checks without warnings
- Existing warnings are being addressed incrementally
- False positive warnings must be explicitly suppressed with a comment explaining why
- We use the strict settings for all linters:
  - Pylint: 9.0+ score required
  - Mypy: Strict type checking with most error flags enabled
  - Bandit: All security checks enabled

Run the following to check for warnings before submitting a PR:

```bash
poetry run pylint src/fedfred/
poetry run mypy src/fedfred/
poetry run bandit -r src/fedfred/
```

### Testing

We take testing seriously to maintain code quality:

- **Test Policy**: All new functionality must be accompanied by appropriate tests in the automated test suite
- Write tests for all new functionality and bug fixes
- Aim for high test coverage (minimum 80%)
- Test structure:
  - Unit tests for individual functions
  - Integration tests for component interactions
  - End-to-end tests for complete workflows
- Run the full test suite before submitting:
  ```bash
  poetry run pytest tests/
  ```
- Include edge cases and error conditions in your tests
- PRs without adequate test coverage will not be merged

When adding tests:

- Place tests in the `tests/` directory
- Name test files with a `test_` prefix
- Follow the existing test patterns
- Test both success and error conditions
- Include comments explaining complex test scenarios

#### Testing with Assertions

We use Python assertions extensively in our testing suite to verify assumptions and catch edge cases:

- **Development and testing**: Assertions are enabled by default
- **Production**: Users may run with the `-O` flag to disable assertions for performance

When writing tests, include assertions to validate:

- Input validation logic
- Expected data transformations
- Error handling
- Edge case behavior

Run tests with assertions explicitly enabled:

```bash
# Run with assertions explicitly enabled (default)
python -B -m pytest tests/

# To simulate production environment (assertions disabled)
python -O -m pytest tests/
```

### Documentation

Good documentation is essential:

- Update relevant documentation when modifying code
- Document all public APIs, classes, and functions
- Include examples for non-trivial functionality
- Use clear and concise language
- For README and other markdown files:
  - Follow consistent heading hierarchy
  - Include appropriate links and references
  - Use code blocks with language specification

### License

- By contributing to FedFred, you agree that your contributions will be licensed under the same license as the project (GNU Affero General Public License v3.0).

### Contact

- If you have any questions, feel free to open a discussion or reach out via GitHub Issues.

### Security Vulnerability Reporting

We take security vulnerabilities seriously. Please do not report security vulnerabilities through public GitHub issues.

Instead:

- Email nsunder724@gmail.com directly
- Provide a detailed description of the vulnerability
- Include steps to reproduce if possible
- Allow time for us to address the vulnerability before public disclosure

We will acknowledge receipt within 48 hours and provide a more detailed response within 72 hours, including next steps and timeline for resolution.

### Code of Conduct

This project adheres to our [CODE_OF_CONDUCT](https://github.com/nikhilxsunder/fedfred/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to nsunder724@gmail.com.

### Development Setup

To set up your development environment:

1. **Prerequisites**

   - Python 3.9+
   - Poetry (for dependency management)
   - Git

2. **Installation with Poetry**

   ```bash
   # Clone the repository
   git clone https://github.com/nikhilxsunder/fedfred.git
   cd fedfred

   # Install dependencies (including dev dependencies and type stubs)
   poetry install

   # If you want to install with explicit type stubs
   poetry install --extras "types"

   # Set up pre-commit hooks
   poetry run pre-commit install
   ```

3. **Installation with Conda**

   ```bash
   # Clone the repository
   git clone https://github.com/nikhilxsunder/fedfred.git
   cd fedfred

   # Create conda environment
   conda create -n fedfred-dev python=3.9
   conda activate fedfred-dev

   # Option 1: Install from the author's Anaconda channel
   conda install -c conda-forge fedfred

   # Option 2: Install in development mode with all dependencies
   pip install -e ".[dev,types]"

   # Set up pre-commit hooks
   pre-commit install
   ```

4. **Environment Configuration**
   - Create a `.env` file based on `.env.example` if needed
   - Configure any necessary environment variables

### Pull Request Process

1. **Submission**

   - Create a PR against the `main` branch
   - Fill out the PR template completely
   - Link any related issues

2. **Review Process**

   - At least one maintainer will review your PR
   - Expect initial feedback within 1-2 weeks
   - Address any requested changes and push updates
   - Once approved, a maintainer will merge your PR

3. **After Merging**
   - Your contribution will be included in the next release
   - You'll be added to the contributors list (if not already there)

### Continuous Integration

Static code analysis is performed automatically:

- **On every commit**: Pre-commit hooks run locally for developers
- **On every push and PR**: GitHub Actions workflows run all static analysis tools
- **Daily scheduled runs**: Automated analysis runs daily to catch issues with dependencies
- **Before releases**: Full comprehensive analysis with stricter settings

This ensures code quality issues are caught early and consistently throughout the development process.

All PRs are automatically tested with:

- Unit and integration tests (pytest)
- Code style checks (pylint)
- Type checking (mypy)
- Test coverage (coverage.py)

CI checks must pass before a PR can be merged. You can run these checks locally:

```bash
# Lint code
poetry run pylint

# Type check
poetry run mypy .

# Run tests with coverage
poetry run pytest --cov=fedfred tests/
```

### Dynamic Analysis

Before major releases, we perform dynamic analysis to verify robustness:

#### Property-Based Testing with Hypothesis

FedFred uses [Hypothesis](https://hypothesis.readthedocs.io/), a powerful property-based testing tool that automatically generates test cases to find edge cases in our code.

Property-based testing differs from traditional unit testing:

- **Unit tests**: Test specific inputs and expected outputs
- **Property-based tests**: Define properties that should always hold true regardless of input

Our property-based tests:

- Generate thousands of diverse inputs automatically
- Test boundary conditions and edge cases
- Explore combinations of parameters that manual tests might miss
- Automatically shrink failing examples to minimal reproducible cases

#### Running Dynamic Analysis Tests

To run property-based tests locally:

```bash
# Install hypothesis
poetry add --group dev hypothesis

# Run property-based tests with assertions enabled (default)
python -B -m pytest tests/test_property_based.py -v

# Show detailed statistics from hypothesis tests
python -B -m pytest tests/test_property_based.py -v --hypothesis-show-statistics

# Run with coverage measurement
python -B -m pytest tests/test_property_based.py --cov=fedfred
```

### Release Process

FedFred follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward-compatible manner
- **PATCH** version for backward-compatible bug fixes
- **MAJOR.MINOR.PATCH**

Release Procedure:

1. Create a PR with version bump and CHANGELOG updates
2. Label the PR as "release-candidate" to trigger dynamic analysis
3. Review test results including property-based tests
4. After merging, tag the release and publish to PyPI
