"""
Pytest configuration and shared fixtures.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository directory."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    return repo_dir


@pytest.fixture
def sample_python_file(temp_repo: Path) -> Path:
    """Create a sample Python file for testing."""
    file_path = temp_repo / "sample.py"
    content = '''"""
Sample module for testing.
"""

def hello_world():
    """Print hello world."""
    return "Hello, World!"


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b
'''
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_typescript_file(temp_repo: Path) -> Path:
    """Create a sample TypeScript file for testing."""
    file_path = temp_repo / "sample.ts"
    content = """
export function greet(name: string): string {
    return `Hello, ${name}!`;
}

export class User {
    constructor(public name: string, public age: number) {}

    greet(): string {
        return `Hi, I'm ${this.name}`;
    }
}
"""
    file_path.write_text(content)
    return file_path


@pytest.fixture
def memdocs_dir(temp_repo: Path) -> Path:
    """Create .memdocs directory structure."""
    memdocs = temp_repo / ".memdocs"
    (memdocs / "docs").mkdir(parents=True)
    (memdocs / "memory").mkdir(parents=True)
    return memdocs


@pytest.fixture
def mock_anthropic_key() -> Generator[None, None, None]:
    """Mock Anthropic API key in environment."""
    original = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-12345"
    yield
    if original:
        os.environ["ANTHROPIC_API_KEY"] = original
    else:
        os.environ.pop("ANTHROPIC_API_KEY", None)
