"""
Unit tests for extract module.
"""
from pathlib import Path

import pytest

from memdocs.extract import Extractor
from memdocs.schemas import SymbolKind


class TestExtractor:
    """Test code extraction functionality."""

    def test_extractor_initialization(self, temp_repo: Path):
        """Test Extractor initialization."""
        extractor = Extractor(repo_path=temp_repo)
        assert extractor.repo_path == temp_repo

    def test_extract_python_symbols(self, temp_repo: Path, sample_python_file: Path):
        """Test Python symbol extraction."""
        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(sample_python_file.relative_to(temp_repo))

        assert context is not None
        assert "Python" in context.language  # Accept "Python" or "Python 3"
        assert context.lines_of_code > 0

        # Check symbols
        symbol_names = [s.name for s in context.symbols]
        assert "hello_world" in symbol_names
        assert "Calculator" in symbol_names

        # Check function symbol
        hello_func = next(s for s in context.symbols if s.name == "hello_world")
        assert hello_func.kind == SymbolKind.FUNCTION
        assert "hello_world" in hello_func.signature

        # Check class symbol
        calc_class = next(s for s in context.symbols if s.name == "Calculator")
        assert calc_class.kind == SymbolKind.CLASS
        assert "add" in calc_class.methods
        assert "subtract" in calc_class.methods

    def test_extract_python_imports(self, temp_repo: Path):
        """Test Python import extraction."""
        # Create file with imports
        file_path = temp_repo / "imports.py"
        content = """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        file_path.write_text(content)

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("imports.py"))

        assert context is not None
        assert "os" in context.imports
        assert "sys" in context.imports
        assert "pathlib" in context.imports
        assert "typing" in context.imports

    def test_extract_nonexistent_file(self, temp_repo: Path):
        """Test extraction of nonexistent file returns None."""
        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("nonexistent.py"))
        assert context is None

    def test_extract_context_multiple_files(self, temp_repo: Path, sample_python_file: Path):
        """Test extracting context for multiple files."""
        # Create another file
        file2 = temp_repo / "module2.py"
        file2.write_text("def another_func(): pass")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_context(
            [
                sample_python_file.relative_to(temp_repo),
                file2.relative_to(temp_repo),
            ]
        )

        assert len(context.files) == 2
        assert context.scope_paths

    def test_expand_directory_path(self, temp_repo: Path):
        """Test path expansion for directories."""
        # Create directory with multiple Python files
        subdir = temp_repo / "src"
        subdir.mkdir()
        (subdir / "module1.py").write_text("def func1(): pass")
        (subdir / "module2.py").write_text("def func2(): pass")
        (subdir / "data.txt").write_text("not a python file")

        extractor = Extractor(repo_path=temp_repo)
        files = extractor._expand_paths([Path("src")])

        # Should only include .py files
        assert len(files) == 2
        assert all(f.suffix == ".py" for f in files)

    def test_extract_class_methods(self, temp_repo: Path):
        """Test extraction of class methods."""
        file_path = temp_repo / "classes.py"
        content = """
class MyClass:
    def __init__(self):
        pass

    def method1(self, x):
        return x * 2

    def method2(self):
        pass

    @property
    def value(self):
        return 42
"""
        file_path.write_text(content)

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("classes.py"))

        my_class = next(s for s in context.symbols if s.name == "MyClass")
        assert "__init__" in my_class.methods
        assert "method1" in my_class.methods
        assert "method2" in my_class.methods
        assert "value" in my_class.methods

    def test_detect_language_from_extension(self, temp_repo: Path):
        """Test language detection from file extension."""
        extractor = Extractor(repo_path=temp_repo)

        # Python
        py_file = temp_repo / "test.py"
        py_file.write_text("# python")
        context = extractor.extract_file_context(Path("test.py"))
        assert "Python" in context.language

        # TypeScript
        ts_file = temp_repo / "test.ts"
        ts_file.write_text("// typescript")
        context = extractor.extract_file_context(Path("test.ts"))
        assert context is not None

    def test_extract_with_unicode_file(self, temp_repo: Path):
        """Test extraction handles Unicode content."""
        file_path = temp_repo / "unicode.py"
        content = """
def greet():
    '''Say hello in multiple languages.'''
    return "Hello, 你好, こんにちは, مرحبا"
"""
        file_path.write_text(content, encoding="utf-8")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("unicode.py"))

        assert context is not None
        assert len(context.symbols) > 0

    def test_extract_empty_file(self, temp_repo: Path):
        """Test extraction of empty file."""
        file_path = temp_repo / "empty.py"
        file_path.write_text("")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("empty.py"))

        assert context is not None
        assert context.lines_of_code == 0
        assert len(context.symbols) == 0
