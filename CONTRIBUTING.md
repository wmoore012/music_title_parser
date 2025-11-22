<!-- SPDX-License-Identifier: MIT
Copyright (c) 2025 Perday Labs -->

# Contributing to Music Title Parser

Thank you for your interest in contributing! This document provides guidelines for contributing to the music title parser project.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/wmoore012/music-title-parser.git
   cd music-title-parser
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Quality Standards

### Code Quality
- **Complexity**: Functions must have McCabe complexity ≤10 (enforced by Ruff C901)
- **Length**: Functions should be ≤50 lines of code
- **Type Safety**: 100% type coverage required (mypy strict mode)
- **Test Coverage**: >90% coverage for new code

### Code Style
- **Formatter**: Ruff (line length: 100)
- **Linter**: Ruff with comprehensive rule set
- **Import sorting**: Automatic via Ruff
- **Type checking**: mypy with strict configuration

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=music_title_parser --cov-report=html

# Run specific test categories
pytest -m "not slow"           # Skip slow tests
pytest -m benchmark           # Run benchmarks only
pytest tests/test_policy_engine.py  # Specific module
```

### Test Categories
- **Unit tests**: Fast, isolated component tests
- **Integration tests**: Multi-component interaction tests
- **Benchmark tests**: Performance regression tests
- **Property tests**: Hypothesis-based testing (if applicable)

### Writing Tests
- Use descriptive test names: `test_garbage_detection_blocks_known_patterns`
- Follow AAA pattern: Arrange, Act, Assert
- Test edge cases and error conditions
- Include performance tests for critical paths

## Making Changes

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for new OAC pattern detection
fix: resolve regex timeout in garbage detection
docs: update API documentation for ParsedTitle
test: add comprehensive benchmarks for policy engine
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes following quality standards**
   - Write tests first (TDD approach recommended)
   - Ensure all quality gates pass locally
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   # Linting and formatting
   ruff check src tests
   ruff format src tests

   # Type checking
   mypy src

   # Tests
   pytest

   # Benchmarks
   python -m music_title_parser.benchmarks
   ```

4. **Submit pull request**
   - Use descriptive title and description
   - Reference any related issues
   - Include test results and benchmark data
   - Request review from maintainers

## Policy Configuration

### Adding Allowlist Entries
```json
{
  "pattern_or_mapping": {
    "channel_name": "New Artist - Topic",
    "artist_name": "New Artist"
  },
  "type": "youtube_oac",
  "confidence_boost": 0.15,
  "owner": "your-github-username",
  "created_at": "2025-09-23",
  "expires_at": "2025-12-22",
  "notes": "Verified YouTube Official Artist Channel"
}
```

### Adding Denylist Patterns
```json
{
  "pattern_or_mapping": {
    "regex": "new\\s+garbage\\s+pattern",
    "description": "Description of what this blocks"
  },
  "type": "garbage_pattern",
  "action": "reject",
  "owner": "your-github-username",
  "created_at": "2025-09-23",
  "expires_at": "2025-12-22",
  "notes": "Explanation of why this pattern is garbage"
}
```

## Performance Guidelines

### Optimization Targets
- **Latency**: <10ms P99 for single title parsing
- **Throughput**: >10,000 titles/second on standard hardware
- **Memory**: <1MB for 10,000 titles in memory
- **Complexity**: O(1) for most operations, O(n) acceptable for batch

### Benchmarking
Always benchmark performance-critical changes:

```python
# Add benchmark tests
def test_new_feature_performance(benchmark):
    def run_feature():
        # Your performance-critical code here
        pass

    result = benchmark(run_feature)
    assert result.stats.mean < 0.001  # <1ms mean
```

## Documentation

### API Documentation
- All public functions must have comprehensive docstrings
- Include examples in docstrings
- Document parameter types and return values
- Explain any side effects or exceptions

### Architecture Changes
- Update ARCHITECTURE.md for significant design changes
- Include diagrams for complex interactions
- Document performance implications
- Explain backwards compatibility impact

## Release Process

### Version Bumping
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` and `__init__.py`
- Update CHANGELOG.md with new version

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
- [ ] Performance benchmarks run
- [ ] Security scan passes

## Getting Help

### Communication Channels
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Security**: Email security@perday.com for security issues

### Code Review
- Maintainers will review PRs within 48 hours
- Address feedback promptly
- Be open to suggestions and improvements
- Ask questions if requirements are unclear

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- Release notes for major features

Thank you for contributing to making music title parsing better for everyone!
