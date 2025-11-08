# MemDocs Test Suite

Comprehensive test suite for MemDocs v2.0.0.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual modules
│   ├── test_schemas.py      # Pydantic schema validation tests
│   ├── test_extract.py      # Code extraction and parsing tests
│   ├── test_policy.py       # Scope and escalation policy tests
│   ├── test_guard.py        # PII/PHI detection and redaction tests
│   └── test_symbol_extractor.py  # Symbol extraction tests
├── integration/             # Integration tests
│   └── test_cli.py          # CLI command tests
└── fixtures/                # Test data and fixtures
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=memdocs --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_schemas.py
```

### Run specific test
```bash
pytest tests/unit/test_schemas.py::TestSchemas::test_symbol_validation
```

### Run with verbose output
```bash
pytest -v
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

## Test Coverage

Current test coverage includes:

- **Schemas**: Full validation testing for all Pydantic models
- **Extract**: Symbol extraction, file parsing, and language detection
- **Policy**: Scope determination and escalation rules
- **Guard**: PII/PHI detection and redaction (all patterns)
- **Symbol Extractor**: Python AST parsing and symbol extraction
- **CLI**: Command-line interface integration tests

## Test Fixtures

Common fixtures available in `conftest.py`:

- `temp_repo`: Temporary repository directory
- `sample_python_file`: Sample Python file with functions and classes
- `sample_typescript_file`: Sample TypeScript file
- `memdocs_dir`: `.memdocs/` directory structure
- `mock_anthropic_key`: Mock API key for testing

## Writing New Tests

### Example Unit Test

```python
import pytest
from memdocs.schemas import Symbol, SymbolKind
from pathlib import Path

def test_symbol_creation():
    """Test creating a Symbol."""
    symbol = Symbol(
        file=Path("test.py"),
        kind=SymbolKind.FUNCTION,
        name="test_func",
        line=10,
    )
    assert symbol.name == "test_func"
    assert symbol.kind == SymbolKind.FUNCTION
```

### Example Integration Test

```python
from click.testing import CliRunner
from memdocs.cli import main

def test_cli_command():
    """Test CLI command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Nightly builds

## Test Dependencies

Install test dependencies:
```bash
pip install -e ".[dev]"
```

This includes:
- pytest
- pytest-cov
- pytest-asyncio
- black (code formatting)
- ruff (linting)
- mypy (type checking)

## Notes

- Tests use `tmp_path` fixture for isolated file operations
- Mock Anthropic API calls to avoid charges during testing
- Integration tests use Click's `CliRunner` for CLI testing
- All tests should be independent and order-agnostic
