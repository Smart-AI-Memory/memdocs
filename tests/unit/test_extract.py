"""
Unit tests for extract module.
"""

from pathlib import Path

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

    def test_parse_requirements_txt(self, temp_repo: Path):
        """Test parsing requirements.txt."""
        req_file = temp_repo / "requirements.txt"
        content = """
# Core dependencies
anthropic>=0.34.0
click>=8.1.0

# Data processing
pydantic>=2.0.0
pyyaml>=6.0

# Comments and empty lines should be ignored
"""
        req_file.write_text(content)

        # Create a Python file to trigger dependency parsing
        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        assert "anthropic>=0.34.0" in context.dependencies
        assert "click>=8.1.0" in context.dependencies
        assert "pydantic>=2.0.0" in context.dependencies
        assert "pyyaml>=6.0" in context.dependencies
        # Should not include comments or empty lines
        assert len([d for d in context.dependencies if d.startswith("#")]) == 0

    def test_parse_requirements_txt_with_flags(self, temp_repo: Path):
        """Test parsing requirements.txt with special flags."""
        req_file = temp_repo / "requirements.txt"
        content = """
-e git+https://github.com/user/repo.git#egg=package
--index-url https://pypi.org/simple
requests>=2.28.0
-r other-requirements.txt
numpy>=1.24.0
"""
        req_file.write_text(content)

        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        # Should include regular dependencies
        assert "requests>=2.28.0" in context.dependencies
        assert "numpy>=1.24.0" in context.dependencies
        # Should skip flags and special directives
        assert not any(d.startswith("-") for d in context.dependencies)

    def test_parse_pyproject_toml_pep621(self, temp_repo: Path):
        """Test parsing pyproject.toml with PEP 621 format."""
        toml_file = temp_repo / "pyproject.toml"
        content = """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "anthropic>=0.34.0",
    "click>=8.1.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=24.0.0",
]
"""
        toml_file.write_text(content)

        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        assert "anthropic>=0.34.0" in context.dependencies
        assert "click>=8.1.0" in context.dependencies
        assert "pydantic>=2.0.0" in context.dependencies

    def test_parse_pyproject_toml_poetry(self, temp_repo: Path):
        """Test parsing pyproject.toml with Poetry format."""
        toml_file = temp_repo / "pyproject.toml"
        content = """
[tool.poetry]
name = "test-project"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.10"
anthropic = ">=0.34.0"
click = "^8.1.0"
pydantic = {version = "^2.0.0", extras = ["email"]}

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
"""
        toml_file.write_text(content)

        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        # Should include dependencies but not the python version
        assert any("anthropic" in d for d in context.dependencies)
        assert any("click" in d for d in context.dependencies)
        assert any("pydantic" in d for d in context.dependencies)
        assert not any(
            "python" in d.lower() and d.startswith("python") for d in context.dependencies
        )

    def test_parse_package_json(self, temp_repo: Path):
        """Test parsing package.json."""
        pkg_file = temp_repo / "package.json"
        content = """
{
  "name": "test-project",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.0.0",
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
"""
        pkg_file.write_text(content)

        # Create a JavaScript file to trigger dependency parsing
        js_file = temp_repo / "test.js"
        js_file.write_text("console.log('hello');")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.js"))

        assert context is not None
        assert "react@^18.0.0" in context.dependencies
        assert "express@^4.18.0" in context.dependencies
        assert "lodash@^4.17.21" in context.dependencies
        assert "typescript@^5.0.0" in context.dependencies
        assert "jest@^29.0.0" in context.dependencies

    def test_parse_package_json_typescript(self, temp_repo: Path):
        """Test parsing package.json for TypeScript files."""
        pkg_file = temp_repo / "package.json"
        content = """
{
  "name": "test-project",
  "dependencies": {
    "@types/node": "^20.0.0",
    "axios": "^1.4.0"
  }
}
"""
        pkg_file.write_text(content)

        ts_file = temp_repo / "test.ts"
        ts_file.write_text("const x: number = 42;")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.ts"))

        assert context is not None
        assert "@types/node@^20.0.0" in context.dependencies
        assert "axios@^1.4.0" in context.dependencies

    def test_parse_dependencies_no_files(self, temp_repo: Path):
        """Test dependency parsing when no package files exist."""
        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        assert context.dependencies == []

    def test_parse_dependencies_invalid_json(self, temp_repo: Path):
        """Test dependency parsing with invalid JSON."""
        pkg_file = temp_repo / "package.json"
        pkg_file.write_text("{ invalid json }")

        js_file = temp_repo / "test.js"
        js_file.write_text("console.log('hello');")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.js"))

        # Should handle error gracefully
        assert context is not None
        assert context.dependencies == []

    def test_parse_dependencies_invalid_toml(self, temp_repo: Path):
        """Test dependency parsing with invalid TOML."""
        toml_file = temp_repo / "pyproject.toml"
        toml_file.write_text("[invalid toml without closing bracket")

        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        # Should handle error gracefully
        assert context is not None
        assert context.dependencies == []

    def test_parse_dependencies_both_sources(self, temp_repo: Path):
        """Test dependency parsing with both requirements.txt and pyproject.toml."""
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests>=2.28.0\n")

        toml_file = temp_repo / "pyproject.toml"
        content = """
[project]
dependencies = [
    "anthropic>=0.34.0",
]
"""
        toml_file.write_text(content)

        py_file = temp_repo / "test.py"
        py_file.write_text("print('hello')")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.py"))

        assert context is not None
        # Should include dependencies from both files
        assert "requests>=2.28.0" in context.dependencies
        assert "anthropic>=0.34.0" in context.dependencies
        # Should deduplicate if the same dependency appears in both
        assert len(context.dependencies) == len(set(context.dependencies))

    def test_parse_dependencies_unknown_language(self, temp_repo: Path):
        """Test dependency parsing for unknown language."""
        txt_file = temp_repo / "test.txt"
        txt_file.write_text("Just some text")

        extractor = Extractor(repo_path=temp_repo)
        context = extractor.extract_file_context(Path("test.txt"))

        assert context is not None
        assert context.dependencies == []
