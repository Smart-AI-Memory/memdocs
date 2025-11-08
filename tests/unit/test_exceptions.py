"""
Unit tests for custom exceptions.
"""

import os
from pathlib import Path

import pytest

from memdocs.exceptions import (
    APIError,
    ConfigurationError,
    DependencyError,
    EmbeddingError,
    ExtractionError,
    FileNotFoundError,
    IndexingError,
    MCPServerError,
    MemDocsError,
    SecurityError,
    SummarizationError,
    ValidationError,
    require_api_key,
    validate_config_version,
    validate_file_path,
)


class TestMemDocsError:
    """Test base exception class."""

    def test_basic_error(self):
        """Test basic error without suggestion."""
        error = MemDocsError("Something went wrong")
        assert "Something went wrong" in str(error)
        assert "Suggestion" not in str(error)

    def test_error_with_suggestion(self):
        """Test error with suggestion."""
        error = MemDocsError("Something went wrong", "Try this fix")
        assert "Something went wrong" in str(error)
        assert "💡 Suggestion: Try this fix" in str(error)


class TestConfigurationError:
    """Test configuration errors."""

    def test_without_path(self):
        """Test configuration error without path."""
        error = ConfigurationError("Invalid config")
        assert "Invalid config" in str(error)
        assert "memdocs init" in str(error)

    def test_with_path(self):
        """Test configuration error with path."""
        config_path = Path(".memdocs.yml")
        error = ConfigurationError("Invalid config", config_path)
        assert "Invalid config" in str(error)
        assert str(config_path) in str(error)


class TestAPIError:
    """Test API errors."""

    def test_401_unauthorized(self):
        """Test 401 error suggests API key check."""
        error = APIError("Unauthorized", "Anthropic", 401)
        assert "Unauthorized" in str(error)
        assert "ANTHROPIC_API_KEY" in str(error)
        assert error.provider == "Anthropic"
        assert error.status_code == 401

    def test_429_rate_limit(self):
        """Test 429 error suggests waiting."""
        error = APIError("Rate limited", "Anthropic", 429)
        assert "Rate limited" in str(error)
        assert "Rate limit" in str(error)
        assert "wait" in str(error).lower()

    def test_500_server_error(self):
        """Test 500 error suggests retry."""
        error = APIError("Server error", "Anthropic", 500)
        assert "Server error" in str(error)
        assert "Try again" in str(error)

    def test_without_status_code(self):
        """Test API error without status code."""
        error = APIError("Connection failed", "Anthropic")
        assert "Connection failed" in str(error)
        assert "API key" in str(error)


class TestFileNotFoundError:
    """Test file not found errors."""

    def test_file_not_found(self):
        """Test file not found error."""
        path = Path("missing.py")
        error = FileNotFoundError(path)
        assert str(path) in str(error)
        assert "not found" in str(error)

    def test_with_context(self):
        """Test with additional context."""
        path = Path("missing.py")
        error = FileNotFoundError(path, context="While processing review")
        assert str(path) in str(error)
        assert "While processing review" in str(error)


class TestValidationError:
    """Test validation errors."""

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("scope", "invalid", "Must be file|module|repo")
        assert "scope" in str(error)
        assert "invalid" in str(error)
        assert "Must be file|module|repo" in str(error)


class TestExtractionError:
    """Test extraction errors."""

    def test_extraction_error(self):
        """Test extraction error."""
        path = Path("bad_code.py")
        error = ExtractionError(path, "Syntax error at line 10")
        assert str(path) in str(error)
        assert "Syntax error at line 10" in str(error)


class TestSummarizationError:
    """Test summarization errors."""

    def test_summarization_error(self):
        """Test summarization error."""
        error = SummarizationError("API timeout")
        assert "API timeout" in str(error)
        assert "summary" in str(error).lower()


class TestIndexingError:
    """Test indexing errors."""

    def test_indexing_error(self):
        """Test indexing error."""
        error = IndexingError("add_document", "Index corrupted")
        assert "add_document" in str(error)
        assert "Index corrupted" in str(error)


class TestEmbeddingError:
    """Test embedding errors."""

    def test_embedding_error(self):
        """Test embedding error."""
        error = EmbeddingError("Model not found")
        assert "Model not found" in str(error)
        assert "embeddings" in str(error)


class TestMCPServerError:
    """Test MCP server errors."""

    def test_mcp_error(self):
        """Test MCP server error."""
        error = MCPServerError("tool_call", "Invalid parameters")
        assert "tool_call" in str(error)
        assert "Invalid parameters" in str(error)


class TestSecurityError:
    """Test security errors."""

    def test_security_error(self):
        """Test security error."""
        path = Path("../../etc/passwd")
        error = SecurityError("Path traversal detected", path)
        assert "Path traversal" in str(error)
        assert str(path) in str(error)


class TestDependencyError:
    """Test dependency errors."""

    def test_dependency_error(self):
        """Test dependency error."""
        error = DependencyError("sentence-transformers", "embeddings")
        assert "sentence-transformers" in str(error)
        assert "embeddings" in str(error)
        assert "pip install" in str(error)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_require_api_key_missing(self):
        """Test require_api_key raises when key missing."""
        # Save original
        original = os.environ.get("ANTHROPIC_API_KEY")

        try:
            # Remove key
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            with pytest.raises(APIError, match="API key required"):
                require_api_key("Anthropic")

        finally:
            # Restore
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original

    def test_require_api_key_present(self):
        """Test require_api_key succeeds when key present."""
        # Save original
        original = os.environ.get("ANTHROPIC_API_KEY")

        try:
            # Set key
            os.environ["ANTHROPIC_API_KEY"] = "test-key"

            # Should not raise
            require_api_key("Anthropic")

        finally:
            # Restore
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original
            elif "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

    def test_validate_file_path_exists(self, tmp_path: Path):
        """Test validate_file_path with existing file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Change to tmp_path to make relative path work
        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            # Should not raise
            validate_file_path(test_file)
        finally:
            os.chdir(original_cwd)

    def test_validate_file_path_not_exists(self, tmp_path: Path):
        """Test validate_file_path with non-existent file."""
        test_file = tmp_path / "missing.py"

        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(FileNotFoundError):
                validate_file_path(test_file, must_exist=True)
        finally:
            os.chdir(original_cwd)

    def test_validate_file_path_optional_existence(self, tmp_path: Path):
        """Test validate_file_path with optional existence."""
        test_file = tmp_path / "optional.py"

        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            # Should not raise even though file doesn't exist
            validate_file_path(test_file, must_exist=False)
        finally:
            os.chdir(original_cwd)

    def test_validate_config_version_valid(self):
        """Test validate_config_version with valid version."""
        # Should not raise
        validate_config_version(1, [1, 2])

    def test_validate_config_version_invalid(self):
        """Test validate_config_version with invalid version."""
        with pytest.raises(ConfigurationError, match="Unsupported configuration version"):
            validate_config_version(3, [1, 2])
