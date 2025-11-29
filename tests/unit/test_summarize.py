"""
Unit tests for summarize module.

Tests Summarizer class with mocked Claude API calls.
No real API calls are made - all responses are mocked.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from memdocs.extract import ExtractedContext, FileContext, GitDiff
from memdocs.schemas import (
    DocumentIndex,
    FeatureSummary,
    ImpactSummary,
    ReferenceSummary,
    ScopeInfo,
    ScopeLevel,
    Symbol,
    SymbolKind,
)
from memdocs.summarize import DEFAULT_MAX_TOKENS, Summarizer


# Valid test API key that matches the expected pattern (sk-ant- + 95 chars)
TEST_API_KEY = "sk-ant-" + "a" * 95  # sk-ant-aaa...aaa (95 a's)


# Sample YAML response that Claude might return
SAMPLE_YAML_RESPONSE = """features:
  - id: feat-001
    title: "Add user authentication"
    description: "Implements login functionality with password hashing"
    risk:
      - security
    tags:
      - auth
      - user

impacts:
  apis:
    - "/api/login"
    - "/api/logout"
  breaking_changes: []
  tests_added: 5
  tests_modified: 0
  migration_required: false

refs:
  pr: 42
  issues:
    - 123
  files_changed:
    - "src/auth.py"
  commits:
    - "abc123"
"""


class TestSummarizerInit:
    """Tests for Summarizer initialization."""

    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        summarizer = Summarizer(api_key=TEST_API_KEY)
        assert summarizer.api_key == TEST_API_KEY
        assert summarizer.model == "claude-sonnet-4-5-20250929"
        assert summarizer.max_tokens == DEFAULT_MAX_TOKENS

    def test_init_with_env_api_key(self):
        """Test initialization with environment variable API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": TEST_API_KEY}):
            summarizer = Summarizer()
            assert summarizer.api_key == TEST_API_KEY

    def test_init_without_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY if it exists
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ValueError, match="API key is required"):
                Summarizer()

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        summarizer = Summarizer(api_key=TEST_API_KEY, model="claude-3-5-sonnet-20241022")
        assert summarizer.model == "claude-3-5-sonnet-20241022"

    def test_init_with_custom_max_tokens(self):
        """Test initialization with custom max_tokens."""
        summarizer = Summarizer(api_key=TEST_API_KEY, max_tokens=8192)
        assert summarizer.max_tokens == 8192

    def test_init_with_invalid_model_raises(self):
        """Test that invalid model name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model name"):
            Summarizer(api_key=TEST_API_KEY, model="invalid; DROP TABLE")

    def test_init_creates_rate_limiter(self):
        """Test that rate limiter is created."""
        summarizer = Summarizer(api_key=TEST_API_KEY)
        assert summarizer.rate_limiter is not None
        assert summarizer.rate_limiter.max_calls == 50

    def test_init_creates_anthropic_client(self):
        """Test that Anthropic client is created."""
        summarizer = Summarizer(api_key=TEST_API_KEY)
        assert summarizer.client is not None


class TestSummarizerRepr:
    """Tests for Summarizer __repr__."""

    def test_repr_masks_api_key(self):
        """Test that __repr__ masks the API key."""
        summarizer = Summarizer(api_key=TEST_API_KEY)
        repr_str = repr(summarizer)

        # Should not contain full key
        assert TEST_API_KEY not in repr_str
        # Should contain masked version with last 4 chars (last 4 chars are 'aaaa')
        assert "***aaaa" in repr_str
        assert "Summarizer" in repr_str
        assert "claude-sonnet-4-5-20250929" in repr_str

    def test_repr_structure(self):
        """Test __repr__ has correct structure."""
        summarizer = Summarizer(api_key=TEST_API_KEY)
        repr_str = repr(summarizer)
        # Should have proper format
        assert repr_str.startswith("Summarizer(")
        assert "model=" in repr_str
        assert "api_key=" in repr_str


class TestExtractYaml:
    """Tests for YAML extraction from Claude responses."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer for testing."""
        return Summarizer(api_key=TEST_API_KEY)

    def test_extract_yaml_with_yaml_fence(self, summarizer):
        """Test extraction with ```yaml fence."""
        text = """Here's the analysis:

```yaml
features:
  - id: feat-001
    title: Test
```

That's all."""
        result = summarizer._extract_yaml(text)
        parsed = yaml.safe_load(result)
        assert parsed["features"][0]["id"] == "feat-001"

    def test_extract_yaml_with_plain_fence(self, summarizer):
        """Test extraction with plain ``` fence."""
        text = """```
features:
  - id: feat-002
    title: Another Test
```"""
        result = summarizer._extract_yaml(text)
        parsed = yaml.safe_load(result)
        assert parsed["features"][0]["id"] == "feat-002"

    def test_extract_yaml_without_fence(self, summarizer):
        """Test extraction without code fence."""
        text = """features:
  - id: feat-003
    title: Plain YAML"""
        result = summarizer._extract_yaml(text)
        parsed = yaml.safe_load(result)
        assert parsed["features"][0]["id"] == "feat-003"

    def test_extract_yaml_strips_whitespace(self, summarizer):
        """Test that whitespace is stripped."""
        text = """
```yaml
features: []
```
"""
        result = summarizer._extract_yaml(text)
        assert result.startswith("features")


class TestBuildPrompt:
    """Tests for prompt building."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer for testing."""
        return Summarizer(api_key=TEST_API_KEY)

    @pytest.fixture
    def sample_context(self):
        """Create sample context."""
        return ExtractedContext(
            diff=GitDiff(
                commit="abc123",
                author="Test User <test@example.com>",
                message="Add feature X",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[Path("src/feature.py")],
                modified_files=[Path("src/utils.py")],
                deleted_files=[],
                all_changed_files=[Path("src/feature.py"), Path("src/utils.py")],
            ),
            files=[
                FileContext(
                    path=Path("src/feature.py"),
                    language="python",
                    lines_of_code=50,
                    symbols=[
                        Symbol(
                            file=Path("src/feature.py"),
                            name="FeatureClass",
                            kind=SymbolKind.CLASS,
                            line=10,
                            signature="class FeatureClass",
                        )
                    ],
                    imports=["import os"],
                    dependencies=["os"],
                )
            ],
            scope_paths=[Path("src/feature.py")],
        )

    @pytest.fixture
    def sample_scope(self):
        """Create sample scope."""
        return ScopeInfo(
            paths=[Path("src/feature.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

    def test_build_prompt_includes_scope(self, summarizer, sample_context, sample_scope):
        """Test that prompt includes scope information."""
        prompt = summarizer._build_prompt(sample_context, sample_scope)

        assert "Level: file" in prompt
        assert "File count: 1" in prompt
        assert "feature.py" in prompt

    def test_build_prompt_includes_git_info(self, summarizer, sample_context, sample_scope):
        """Test that prompt includes git information."""
        prompt = summarizer._build_prompt(sample_context, sample_scope)

        assert "Commit: abc123" in prompt
        assert "Author: Test User <test@example.com>" in prompt
        assert "Add feature X" in prompt
        assert "Added: src/feature.py" in prompt
        assert "Modified: src/utils.py" in prompt

    def test_build_prompt_includes_file_context(self, summarizer, sample_context, sample_scope):
        """Test that prompt includes file context."""
        prompt = summarizer._build_prompt(sample_context, sample_scope)

        assert "File: src/feature.py" in prompt
        assert "Language: python" in prompt
        assert "LOC: 50" in prompt
        assert "class FeatureClass" in prompt

    def test_build_prompt_without_git_diff(self, summarizer, sample_scope):
        """Test prompt building when no git diff is available."""
        context = ExtractedContext(
            diff=None,
            files=[],
            scope_paths=[],
        )
        prompt = summarizer._build_prompt(context, sample_scope)

        assert "No git information available" in prompt

    def test_build_prompt_limits_files(self, summarizer, sample_scope):
        """Test that prompt limits files to 10."""
        files = [
            FileContext(
                path=Path(f"src/file{i}.py"),
                language="python",
                lines_of_code=10,
                symbols=[],
                imports=[],
                dependencies=[],
            )
            for i in range(15)
        ]
        context = ExtractedContext(
            diff=None,
            files=files,
            scope_paths=[Path("src")],
        )
        prompt = summarizer._build_prompt(context, sample_scope)

        assert "file0.py" in prompt
        assert "file9.py" in prompt
        assert "and 5 more files" in prompt

    def test_build_prompt_includes_yaml_instructions(
        self, summarizer, sample_context, sample_scope
    ):
        """Test that prompt includes YAML instructions."""
        prompt = summarizer._build_prompt(sample_context, sample_scope)

        assert "Generate the YAML now:" in prompt
        assert "features:" in prompt
        assert "impacts:" in prompt
        assert "refs:" in prompt


class TestBuildDocumentIndex:
    """Tests for building DocumentIndex from parsed YAML."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer for testing."""
        return Summarizer(api_key=TEST_API_KEY)

    @pytest.fixture
    def sample_context(self):
        """Create sample context."""
        return ExtractedContext(
            diff=GitDiff(
                commit="abc123",
                author="Test <test@test.com>",
                message="Test commit",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[Path("test.py")],
                modified_files=[],
                deleted_files=[],
                all_changed_files=[Path("test.py")],
            ),
            files=[
                FileContext(
                    path=Path("test.py"),
                    language="python",
                    lines_of_code=10,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                )
            ],
            scope_paths=[Path("test.py")],
        )

    @pytest.fixture
    def sample_scope(self):
        """Create sample scope."""
        return ScopeInfo(
            paths=[Path("test.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

    def test_build_document_index_basic(self, summarizer, sample_context, sample_scope):
        """Test basic document index building."""
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert isinstance(doc_index, DocumentIndex)
        assert doc_index.commit == "abc123"
        assert doc_index.scope == sample_scope

    def test_build_document_index_features(self, summarizer, sample_context, sample_scope):
        """Test that features are parsed correctly."""
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert len(doc_index.features) == 1
        feature = doc_index.features[0]
        assert feature.id == "feat-001"
        assert feature.title == "Add user authentication"
        assert "security" in feature.risk
        assert "auth" in feature.tags

    def test_build_document_index_impacts(self, summarizer, sample_context, sample_scope):
        """Test that impacts are parsed correctly."""
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert "/api/login" in doc_index.impacts.apis
        assert "/api/logout" in doc_index.impacts.apis
        assert doc_index.impacts.tests_added == 5
        assert doc_index.impacts.migration_required is False

    def test_build_document_index_refs(self, summarizer, sample_context, sample_scope):
        """Test that refs are parsed correctly."""
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert doc_index.refs.pr == 42
        assert 123 in doc_index.refs.issues
        assert "abc123" in doc_index.refs.commits

    def test_build_document_index_uses_context_files(
        self, summarizer, sample_context, sample_scope
    ):
        """Test that files_changed comes from context."""
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        # Should use files from context, not from parsed YAML
        assert Path("test.py") in doc_index.refs.files_changed

    def test_build_document_index_empty_features(self, summarizer, sample_context, sample_scope):
        """Test handling of empty features."""
        parsed = {"features": [], "impacts": {}, "refs": {}}
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert doc_index.features == []

    def test_build_document_index_missing_fields(self, summarizer, sample_context, sample_scope):
        """Test handling of missing fields in parsed YAML."""
        parsed = {
            "features": [{"title": "Test"}],  # Missing id, description, etc.
            "impacts": {},
            "refs": {},
        }
        doc_index = summarizer._build_document_index(parsed, sample_context, sample_scope)

        assert len(doc_index.features) == 1
        assert doc_index.features[0].title == "Test"
        assert doc_index.features[0].risk == []

    def test_build_document_index_without_diff(self, summarizer, sample_scope):
        """Test document index when context has no diff."""
        context = ExtractedContext(
            diff=None,
            files=[],
            scope_paths=[],
        )
        parsed = yaml.safe_load(SAMPLE_YAML_RESPONSE)
        doc_index = summarizer._build_document_index(parsed, context, sample_scope)

        assert doc_index.commit is None


class TestGenerateMarkdown:
    """Tests for markdown generation."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer for testing."""
        return Summarizer(api_key=TEST_API_KEY)

    @pytest.fixture
    def sample_doc_index(self):
        """Create sample DocumentIndex."""
        return DocumentIndex(
            commit="abc123",
            timestamp=datetime.now(timezone.utc),
            scope=ScopeInfo(
                paths=[Path("test.py")],
                level=ScopeLevel.FILE,
                file_count=1,
            ),
            features=[
                FeatureSummary(
                    id="feat-001",
                    title="Add login feature",
                    description="Implements user authentication",
                    risk=["security", "breaking"],
                    tags=["auth"],
                )
            ],
            impacts=ImpactSummary(
                apis=["/api/login"],
                breaking_changes=["Changed auth flow"],
                tests_added=5,
                tests_modified=2,
            ),
            refs=ReferenceSummary(
                pr=42,
                issues=[1, 2],
                files_changed=[Path("test.py")],
                commits=["abc123"],
            ),
        )

    @pytest.fixture
    def sample_context_with_diff(self):
        """Create sample context with diff."""
        return ExtractedContext(
            diff=GitDiff(
                commit="abc123",
                author="Test <test@test.com>",
                message="Test",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[Path("new.py")],
                modified_files=[Path("existing.py")],
                deleted_files=[Path("old.py")],
                all_changed_files=[Path("new.py"), Path("existing.py"), Path("old.py")],
            ),
            files=[],
            scope_paths=[],
        )

    def test_generate_markdown_title(self, summarizer, sample_doc_index):
        """Test that title comes from first feature."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "# Add login feature" in markdown

    def test_generate_markdown_metadata(self, summarizer, sample_doc_index):
        """Test that metadata is included."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "**Commit:** abc123" in markdown
        assert "**Scope:** File-level" in markdown
        assert "**Date:**" in markdown

    def test_generate_markdown_summary(self, summarizer, sample_doc_index):
        """Test summary section."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "## Summary" in markdown
        assert "Add login feature" in markdown
        assert "Implements user authentication" in markdown

    def test_generate_markdown_changes(
        self, summarizer, sample_doc_index, sample_context_with_diff
    ):
        """Test changes section with diff."""
        markdown = summarizer._generate_markdown(sample_doc_index, sample_context_with_diff)

        assert "## Changes" in markdown
        assert "**Added:** 1 files" in markdown
        assert "new.py" in markdown
        assert "**Modified:** 1 files" in markdown
        assert "existing.py" in markdown
        assert "**Deleted:** 1 files" in markdown
        assert "old.py" in markdown

    def test_generate_markdown_impact(self, summarizer, sample_doc_index):
        """Test impact section."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "## Impact" in markdown
        assert "/api/login" in markdown
        assert "Changed auth flow" in markdown

    def test_generate_markdown_risks(self, summarizer, sample_doc_index):
        """Test risks section."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "## Risks" in markdown
        assert "security" in markdown

    def test_generate_markdown_references(self, summarizer, sample_doc_index):
        """Test references section."""
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(sample_doc_index, context)

        assert "## References" in markdown
        assert "PR #42" in markdown
        assert "Issue #1" in markdown
        assert "Issue #2" in markdown
        assert "Commit: abc123" in markdown

    def test_generate_markdown_no_features(self, summarizer):
        """Test markdown with no features."""
        doc_index = DocumentIndex(
            commit="abc123",
            timestamp=datetime.now(timezone.utc),
            scope=ScopeInfo(
                paths=[Path("test.py")],
                level=ScopeLevel.FILE,
                file_count=1,
            ),
            features=[],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(files_changed=[]),
        )
        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(doc_index, context)

        assert "# Code Changes Summary" in markdown


class TestSummarize:
    """Tests for the main summarize method with mocked API."""

    @pytest.fixture
    def mock_anthropic_response(self):
        """Create mock Anthropic API response."""
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = SAMPLE_YAML_RESPONSE
        mock_response.content = [mock_content_block]
        return mock_response

    @pytest.fixture
    def sample_context(self):
        """Create sample context."""
        return ExtractedContext(
            diff=GitDiff(
                commit="abc123",
                author="Test <test@test.com>",
                message="Test commit",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[Path("test.py")],
                modified_files=[],
                deleted_files=[],
                all_changed_files=[Path("test.py")],
            ),
            files=[
                FileContext(
                    path=Path("test.py"),
                    language="python",
                    lines_of_code=10,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                )
            ],
            scope_paths=[Path("test.py")],
        )

    @pytest.fixture
    def sample_scope(self):
        """Create sample scope."""
        return ScopeInfo(
            paths=[Path("test.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

    def test_summarize_returns_tuple(self, mock_anthropic_response, sample_context, sample_scope):
        """Test that summarize returns (DocumentIndex, markdown) tuple."""
        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY)
            result = summarizer.summarize(sample_context, sample_scope)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], DocumentIndex)
            assert isinstance(result[1], str)

    def test_summarize_calls_api_correctly(
        self, mock_anthropic_response, sample_context, sample_scope
    ):
        """Test that API is called with correct parameters."""
        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY, max_tokens=8192)
            summarizer.summarize(sample_context, sample_scope)

            # Verify API was called
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]

            assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
            assert call_kwargs["max_tokens"] == 8192
            assert len(call_kwargs["messages"]) == 1
            assert call_kwargs["messages"][0]["role"] == "user"

    def test_summarize_handles_yaml_error(self, sample_context, sample_scope):
        """Test that YAML parsing errors are handled."""
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = "invalid: yaml: content: ["  # Invalid YAML
        mock_response.content = [mock_content_block]

        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY)

            with pytest.raises(ValueError, match="Failed to parse YAML"):
                summarizer.summarize(sample_context, sample_scope)

    def test_summarize_handles_unexpected_content_block(self, sample_context, sample_scope):
        """Test handling of unexpected content block type."""
        mock_response = MagicMock()
        mock_content_block = MagicMock(spec=[])  # No 'text' attribute
        mock_response.content = [mock_content_block]

        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY)

            with pytest.raises(ValueError, match="Unexpected content block type"):
                summarizer.summarize(sample_context, sample_scope)

    def test_summarize_checks_rate_limit(
        self, mock_anthropic_response, sample_context, sample_scope
    ):
        """Test that rate limiter is checked before API call."""
        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY)

            # Mock rate limiter
            summarizer.rate_limiter = MagicMock()
            summarizer.summarize(sample_context, sample_scope)

            # Rate limiter should be checked
            summarizer.rate_limiter.check_rate_limit.assert_called_once()


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    def test_rate_limiter_allows_calls_within_limit(self):
        """Test that calls within rate limit are allowed."""
        with patch("memdocs.summarize.anthropic.Anthropic"):
            summarizer = Summarizer(api_key=TEST_API_KEY)

            # Should allow getting remaining calls
            remaining = summarizer.rate_limiter.get_remaining_calls()
            assert remaining == 50

    def test_rate_limiter_blocks_excess_calls(self):
        """Test that excess calls are blocked."""
        with patch("memdocs.summarize.anthropic.Anthropic"):
            summarizer = Summarizer(api_key=TEST_API_KEY)

            # Exhaust the rate limit
            for _ in range(50):
                summarizer.rate_limiter.check_rate_limit()

            # Next call should raise RuntimeError
            with pytest.raises(RuntimeError, match="Rate limit exceeded"):
                summarizer.rate_limiter.check_rate_limit()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_files_list(self):
        """Test handling of empty files list."""
        with patch("memdocs.summarize.anthropic.Anthropic") as mock_client_class:
            mock_response = MagicMock()
            mock_content_block = MagicMock()
            mock_content_block.text = SAMPLE_YAML_RESPONSE
            mock_response.content = [mock_content_block]
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            summarizer = Summarizer(api_key=TEST_API_KEY)

            context = ExtractedContext(
                diff=None,
                files=[],
                scope_paths=[],
            )
            scope = ScopeInfo(
                paths=[],
                level=ScopeLevel.REPO,
                file_count=0,
            )

            doc_index, markdown = summarizer.summarize(context, scope)
            assert doc_index is not None
            assert markdown is not None

    def test_many_symbols_in_file(self):
        """Test handling of many symbols (should limit to 5)."""
        with patch("memdocs.summarize.anthropic.Anthropic"):
            summarizer = Summarizer(api_key=TEST_API_KEY)

            symbols = [
                Symbol(
                    file=Path("test.py"),
                    name=f"func{i}",
                    kind=SymbolKind.FUNCTION,
                    line=(i + 1) * 10,  # Lines start from 10, 20, 30...
                    signature=f"def func{i}()",
                )
                for i in range(20)
            ]

            context = ExtractedContext(
                diff=None,
                files=[
                    FileContext(
                        path=Path("test.py"),
                        language="python",
                        lines_of_code=200,
                        symbols=symbols,
                        imports=[],
                        dependencies=[],
                    )
                ],
                scope_paths=[Path("test.py")],
            )
            scope = ScopeInfo(
                paths=[Path("test.py")],
                level=ScopeLevel.FILE,
                file_count=1,
            )

            prompt = summarizer._build_prompt(context, scope)

            # Should only include first 5 symbols
            assert "func0" in prompt
            assert "func4" in prompt
            # func19 should not be included
            assert "func19" not in prompt

    def test_special_characters_in_commit_message(self):
        """Test handling of special characters in commit message."""
        with patch("memdocs.summarize.anthropic.Anthropic"):
            summarizer = Summarizer(api_key=TEST_API_KEY)

            context = ExtractedContext(
                diff=GitDiff(
                    commit="abc123",
                    author="Test <test@test.com>",
                    message='Fix bug with `code` and <html> & "quotes"',
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    added_files=[],
                    modified_files=[],
                    deleted_files=[],
                    all_changed_files=[],
                ),
                files=[],
                scope_paths=[],
            )
            scope = ScopeInfo(
                paths=[],
                level=ScopeLevel.FILE,
                file_count=0,
            )

            prompt = summarizer._build_prompt(context, scope)

            # Special characters should be preserved
            assert "`code`" in prompt
            assert "<html>" in prompt
            assert '"quotes"' in prompt
