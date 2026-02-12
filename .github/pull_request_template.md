## Summary

<!-- Describe what this PR does and why. Focus on the user-visible behavior in fedfred. -->

## Related Issues / Discussions

<!-- e.g. Closes #123, Related to #456 -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update
- [ ] Refactor / internal change
- [ ] CI / tooling / packaging

## Public API Impact

- [ ] No public API changes
- [ ] Adds new public API (functions, classes, arguments, or return types)
- [ ] Changes existing public API
- [ ] Removes or deprecates public API

If there **are** API changes, describe them clearly (including any breaking changes):

<!-- e.g. "FredAPI.get_series now returns SeriesObservations instead of raw dict" -->

## How to Test

<!-- Provide concrete steps / commands for reviewers. -->

```bash
# examples
pytest
# or specific tests:
pytest tests/test_clients.py -k "async"
# docs (if relevant)
cd docs && make html
```

## Checklist

- [ ] Tests added/updated and pass locally
- [ ] Docs updated (docstrings and/or Sphinx docs) if behavior or API changed
- [ ] Examples updated if relevant
- [ ] Type hints kept accurate and CI/linting pass (if applicable)
- [ ] No unexpected changes to generated files (e.g. docs build artifacts, cache, etc.)

## Additional Context

<!-- Any context, design notes, tradeoffs, or follow-up work for reviewers. -->