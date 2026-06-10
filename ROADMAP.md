### Roadmap

#### v4 Release (Current Focus)

The v4 branch represents a major backend rewrite with focus on:

- Complete internal refactor: `_core` and `_internals` subpackage architecture
- Unified endpoint resolution across FRED, ALFRED, GeoFRED, FRASER
- Sync/async parity throughout the public surface
- Full 100% test coverage and Codecov compliance
- Comprehensive documentation with endpoint coverage and advanced workflows

#### Post-v4 Stability Phase (12+ Months)

After v4 stabilizes, expansions are limited to three targeted areas:

1. **Low-Latency Revisions**
   - Runtime optimization for high-frequency API workflows
   - Improved rate-limit handling and request batching
   - Connection pooling and request pipelining enhancements

2. **Exception Hierarchy Revisions**
   - Structured exception taxonomy for FRED/ALFRED/GeoFRED/FRASER-specific errors
   - Enhanced error context and recovery guidance
   - Backwards-compatible exception handling improvements

3. **GPU and Machine Learning Framework Support**
   - cuDF integration for large-scale data operations
   - PyTorch tensor conversion and streaming support
   - Efficient data pipelines for ML workflows

This roadmap prioritizes stability and proven integration patterns over speculative expansions. Changes are subject to community feedback and usage patterns that emerge during v4 adoption.
