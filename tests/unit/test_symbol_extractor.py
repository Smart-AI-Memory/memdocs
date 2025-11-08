"""
Unit tests for symbol_extractor module.
"""

from pathlib import Path

import pytest

from memdocs.schemas import SymbolKind
from memdocs.symbol_extractor import (
    Language,
    SymbolExtractor,
    extract_symbols_for_memdocs,
)


class TestSymbolExtractor:
    """Test symbol extraction from source files."""

    @pytest.fixture
    def extractor(self):
        """Create a SymbolExtractor instance."""
        return SymbolExtractor()

    def test_extract_python_function(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extracting Python function."""
        file_path = temp_repo / "test.py"
        code = """
def hello(name: str) -> str:
    '''Say hello.'''
    return f"Hello, {name}"
"""
        file_path.write_text(code)

        symbols = extractor.extract_from_file(file_path)

        assert len(symbols) == 1
        assert symbols[0].name == "hello"
        assert symbols[0].kind == SymbolKind.FUNCTION
        assert "name: str" in symbols[0].signature
        assert "-> str" in symbols[0].signature

    def test_extract_python_class(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extracting Python class with methods."""
        file_path = temp_repo / "test.py"
        code = """
class Calculator:
    '''Simple calculator.'''

    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b
"""
        file_path.write_text(code)

        symbols = extractor.extract_from_file(file_path)

        calc_symbol = next(s for s in symbols if s.kind == SymbolKind.CLASS)
        assert calc_symbol.name == "Calculator"
        assert "add" in calc_symbol.methods
        assert "subtract" in calc_symbol.methods
        assert calc_symbol.doc is not None

    def test_extract_async_function(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extracting async function."""
        file_path = temp_repo / "test.py"
        code = """
async def fetch_data(url: str):
    '''Fetch data asynchronously.'''
    pass
"""
        file_path.write_text(code)

        symbols = extractor.extract_from_file(file_path)

        assert len(symbols) == 1
        assert symbols[0].name == "fetch_data"

    def test_detect_language(self, extractor: SymbolExtractor):
        """Test language detection from file extension."""
        assert extractor._detect_language(Path("test.py")) == Language.PYTHON
        assert extractor._detect_language(Path("test.ts")) == Language.TYPESCRIPT
        assert extractor._detect_language(Path("test.js")) == Language.JAVASCRIPT
        assert extractor._detect_language(Path("test.go")) == Language.GO

    def test_extract_from_code_string(self, extractor: SymbolExtractor):
        """Test extracting symbols from code string."""
        code = """
def greet():
    return "hello"

class Person:
    pass
"""
        symbols = extractor.extract_from_code(code, Language.PYTHON)

        assert len(symbols) == 2
        symbol_names = [s.name for s in symbols]
        assert "greet" in symbol_names
        assert "Person" in symbol_names

    def test_extract_with_decorators(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extracting functions with decorators."""
        file_path = temp_repo / "test.py"
        code = """
@property
def value(self):
    return self._value

@staticmethod
def static_method():
    pass

@classmethod
def class_method(cls):
    pass
"""
        file_path.write_text(code)

        symbols = extractor.extract_from_file(file_path)

        assert len(symbols) == 3

    def test_extract_class_with_inheritance(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extracting class with inheritance."""
        file_path = temp_repo / "test.py"
        code = """
class Base:
    pass

class Derived(Base):
    pass

class Multiple(Base, object):
    pass
"""
        file_path.write_text(code)

        symbols = extractor.extract_from_file(file_path)

        derived = next(s for s in symbols if s.name == "Derived")
        assert "Base" in derived.signature

    def test_extract_symbols_for_memdocs(self, temp_repo: Path):
        """Test convenience function for extracting symbols."""
        file_path = temp_repo / "test.py"
        code = """
def test_func():
    pass
"""
        file_path.write_text(code)

        symbols_output = extract_symbols_for_memdocs(file_path)

        assert len(symbols_output.symbols) == 1
        assert symbols_output.symbols[0].name == "test_func"

    def test_empty_file(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test extraction from empty file."""
        file_path = temp_repo / "empty.py"
        file_path.write_text("")

        symbols = extractor.extract_from_file(file_path)

        assert len(symbols) == 0

    def test_syntax_error_handling(self, extractor: SymbolExtractor, temp_repo: Path):
        """Test handling of syntax errors in Python files."""
        file_path = temp_repo / "bad.py"
        code = """
def incomplete_function(
"""
        file_path.write_text(code)

        # Should not raise, just return empty list
        symbols = extractor.extract_from_file(file_path)
        assert len(symbols) == 0

    def test_nonexistent_file(self, extractor: SymbolExtractor):
        """Test extraction from nonexistent file."""
        symbols = extractor.extract_from_file(Path("/nonexistent/file.py"))
        assert len(symbols) == 0
