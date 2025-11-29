# Contributing to MemDocs

Thank you for your interest in contributing to MemDocs! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/memdocs.git
   cd memdocs
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   make install-dev
   # OR manually:
   pip install -e ".[dev,embeddings,all]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   make pre-commit-install
   # OR manually:
   pre-commit install
   ```

5. **Verify setup**:
   ```bash
   make test
   ```

### Development Workflow

1. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-123
   ```

2. **Make your changes** following our code style (see below)

3. **Run tests**:
   ```bash
   make test          # Unit and integration tests
   make lint          # Code quality checks
   make type-check    # Type checking
   ```

4. **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: add new feature X"
   git commit -m "fix: resolve issue #123"
   git commit -m "docs: update installation guide"
   ```

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking

Run before committing:
```bash
make format  # Auto-format code
make lint    # Check code quality
```

### Type Hints

- All public functions must have type hints
- Use modern type syntax (e.g., `list[str]` instead of `List[str]`)
- Use `from __future__ import annotations` for forward references

```python
from __future__ import annotations

def process_files(paths: list[Path], recurse: bool = False) -> dict[str, Any]:
    """Process files and return summary."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def extract_symbols(file_path: Path, language: str) -> list[Symbol]:
    """Extract code symbols from a file.

    Args:
        file_path: Path to the file to analyze
        language: Programming language (python, typescript, etc.)

    Returns:
        List of extracted symbols

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If language is not supported

    Example:
        ```python
        symbols = extract_symbols(Path("main.py"), "python")
        for symbol in symbols:
            print(f"{symbol.kind}: {symbol.name}")
        ```
    """
    ...
```

## Testing

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use pytest fixtures from `tests/conftest.py`
- Aim for >85% code coverage

### Test Structure

```python
class TestFeatureName:
    """Test suite for FeatureName."""

    def test_basic_functionality(self):
        """Test basic use case."""
        ...

    def test_edge_case(self):
        """Test edge case handling."""
        ...

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError, match="Invalid input"):
            ...
```

### API Integration Tests

API tests make real calls to Claude and cost money. They're skipped by default:

```bash
# Skip API tests (default)
pytest

# Run API tests explicitly
pytest -m api

# Or use make
make test-api  # Prompts for confirmation
```

Mark API tests with:
```python
@pytest.mark.api
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
def test_with_real_api():
    ...
```

## Pull Request Process

1. **Update documentation** if you've changed APIs or added features

2. **Add tests** for new functionality:
   - Unit tests for logic
   - Integration tests for workflows
   - Update coverage target if needed

3. **Update CHANGELOG.md** under "Unreleased" section:
   ```markdown
   ## [Unreleased]

   ### Added
   - New feature X (#123)

   ### Fixed
   - Bug in feature Y (#456)
   ```

4. **Ensure CI passes**:
   - All tests pass
   - Coverage ≥ 65% (target: 85%)
   - No linting errors
   - Type checking passes

5. **Request review** from maintainers

6. **Address feedback** and update your PR

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add support for Go language`
- `fix: resolve memory leak in embeddings`
- `docs: update installation instructions`
- `test: add tests for policy engine`
- `refactor: simplify symbol extraction`
- `perf: optimize vector search`
- `chore: update dependencies`

## Project Structure

```
memdocs/
├── memdocs/              # Source code
│   ├── __init__.py
│   ├── cli.py           # CLI interface
│   ├── schemas.py       # Pydantic models
│   ├── extract.py       # Code extraction
│   ├── summarize.py     # Claude integration
│   ├── embeddings.py    # Vector embeddings
│   ├── search.py        # Vector search
│   ├── index.py         # Memory indexing
│   └── empathy_adapter.py  # Empathy Framework integration
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── conftest.py      # Shared fixtures
├── examples/            # Example projects
└── docs/                # Documentation
```

## Areas for Contribution

### High Priority

- [ ] Improve test coverage (current: 65%, target: 85%)
- [ ] Add CLI integration tests
- [ ] Improve error messages and handling
- [ ] Performance optimizations
- [ ] Documentation improvements

### Feature Ideas

- [ ] Support for more programming languages
- [ ] Incremental documentation updates
- [ ] Custom Claude prompt templates
- [ ] Integration with more tools (VS Code, JetBrains)
- [ ] Web dashboard for memory exploration

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/Smart-AI-Memory/memdocs/labels/good%20first%20issue).

## Questions?

- **Discord**: (Coming soon)
- **GitHub Discussions**: Use for questions and ideas
- **Issues**: Use for bug reports and feature requests

## Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Added to AUTHORS file

Thank you for contributing to MemDocs! 🙏
