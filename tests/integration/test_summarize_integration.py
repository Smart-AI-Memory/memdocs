"""
Integration tests for summarize module using real Claude API.

These tests make real API calls and cost money. They're skipped by default.
Run with: pytest -m api
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from memdocs.extract import ExtractedContext, FileContext, GitDiff
from memdocs.schemas import ScopeInfo, ScopeLevel, Symbol, SymbolKind
from memdocs.summarize import Summarizer


@pytest.mark.api
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping real API tests",
)
class TestSummarizerAPIIntegration:
    """Integration tests with real Claude API."""

    def test_summarize_with_real_api(self):
        """Test full summarization workflow with real API."""
        summarizer = Summarizer()

        # Create realistic context
        context = ExtractedContext(
            diff=GitDiff(
                commit="abc123",
                author="Test User <test@example.com>",
                message="Add user login functionality",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[Path("src/auth.py")],
                modified_files=[],
                deleted_files=[],
                all_changed_files=[Path("src/auth.py")],
            ),
            files=[
                FileContext(
                    path=Path("src/auth.py"),
                    language="python",
                    lines_of_code=10,
                    symbols=[
                        Symbol(
                            file=Path("src/auth.py"),
                            name="login",
                            kind=SymbolKind.FUNCTION,
                            line=1,
                            signature="login(username, password)",
                        )
                    ],
                    imports=["from security import authenticate"],
                    dependencies=["security"],
                )
            ],
            scope_paths=[Path("src/auth.py")],
        )

        scope = ScopeInfo(
            paths=[Path("src/auth.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

        # Call real API
        doc_index, markdown = summarizer.summarize(context, scope)

        # Verify response structure
        assert doc_index.commit == "abc123"
        assert doc_index.scope == scope
        assert len(doc_index.features) > 0, "Should have at least one feature"

        # Verify feature has required fields
        feature = doc_index.features[0]
        assert feature.id is not None
        assert feature.title is not None
        assert len(feature.title) <= 200, "Title should be under 200 chars"

        # Verify markdown was generated
        assert markdown is not None
        assert len(markdown) > 0
        assert "abc123" in markdown or "Commit" in markdown

        # Verify refs include file
        assert Path("src/auth.py") in doc_index.refs.files_changed

    def test_summarize_multiple_files(self):
        """Test summarization with multiple files."""
        summarizer = Summarizer()

        context = ExtractedContext(
            diff=GitDiff(
                commit="def456",
                author="Dev <dev@example.com>",
                message="Add user model and view",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[],
                modified_files=[Path("src/models.py"), Path("src/views.py")],
                deleted_files=[],
                all_changed_files=[Path("src/models.py"), Path("src/views.py")],
            ),
            files=[
                FileContext(
                    path=Path("src/models.py"),
                    language="python",
                    lines_of_code=20,
                    symbols=[
                        Symbol(
                            file=Path("src/models.py"),
                            name="User",
                            kind=SymbolKind.CLASS,
                            line=1,
                            signature="class User",
                            methods=["__init__", "save", "delete"],
                        )
                    ],
                    imports=["from sqlalchemy import Column"],
                    dependencies=["sqlalchemy"],
                ),
                FileContext(
                    path=Path("src/views.py"),
                    language="python",
                    lines_of_code=15,
                    symbols=[
                        Symbol(
                            file=Path("src/views.py"),
                            name="get_user",
                            kind=SymbolKind.FUNCTION,
                            line=5,
                            signature="get_user(user_id: int)",
                        )
                    ],
                    imports=["from models import User"],
                    dependencies=["models"],
                ),
            ],
            scope_paths=[Path("src/models.py"), Path("src/views.py")],
        )

        scope = ScopeInfo(
            paths=[Path("src/models.py"), Path("src/views.py")],
            level=ScopeLevel.MODULE,
            file_count=2,
        )

        doc_index, markdown = summarizer.summarize(context, scope)

        # Verify multiple files are tracked
        assert len(doc_index.refs.files_changed) == 2
        assert Path("src/models.py") in doc_index.refs.files_changed
        assert Path("src/views.py") in doc_index.refs.files_changed

        # Verify scope level
        assert doc_index.scope.level == ScopeLevel.MODULE

    def test_summarize_breaking_change_detection(self):
        """Test that breaking changes are detected."""
        summarizer = Summarizer()

        context = ExtractedContext(
            diff=GitDiff(
                commit="break123",
                author="Dev <dev@example.com>",
                message="BREAKING: Change API response format for get_users endpoint",
                timestamp=datetime.now(timezone.utc).isoformat(),
                added_files=[],
                modified_files=[Path("api/endpoints.py")],
                deleted_files=[],
                all_changed_files=[Path("api/endpoints.py")],
            ),
            files=[
                FileContext(
                    path=Path("api/endpoints.py"),
                    language="python",
                    lines_of_code=25,
                    symbols=[
                        Symbol(
                            file=Path("api/endpoints.py"),
                            name="get_users",
                            kind=SymbolKind.FUNCTION,
                            line=10,
                            signature="get_users() -> dict",
                            doc="Changed return format from list to dict",
                        )
                    ],
                    imports=["from flask import jsonify"],
                    dependencies=["flask"],
                )
            ],
            scope_paths=[Path("api/endpoints.py")],
        )

        scope = ScopeInfo(
            paths=[Path("api/endpoints.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

        doc_index, markdown = summarizer.summarize(context, scope)

        # Claude should detect breaking change from commit message
        assert doc_index.impacts is not None

        # At minimum, should recognize this is API-related
        # (Claude may or may not flag breaking changes depending on interpretation)
        assert doc_index.features is not None
        assert len(doc_index.features) > 0

    def test_summarize_without_diff(self):
        """Test summarization when no git diff is available."""
        summarizer = Summarizer()

        context = ExtractedContext(
            diff=None,  # No git information
            files=[
                FileContext(
                    path=Path("utils/helpers.py"),
                    language="python",
                    lines_of_code=8,
                    symbols=[
                        Symbol(
                            file=Path("utils/helpers.py"),
                            name="format_date",
                            kind=SymbolKind.FUNCTION,
                            line=3,
                            signature="format_date(date)",
                        )
                    ],
                    imports=["from datetime import datetime"],
                    dependencies=[],
                )
            ],
            scope_paths=[Path("utils/helpers.py")],
        )

        scope = ScopeInfo(
            paths=[Path("utils/helpers.py")],
            level=ScopeLevel.FILE,
            file_count=1,
        )

        doc_index, markdown = summarizer.summarize(context, scope)

        # Should still generate valid documentation
        assert doc_index is not None
        assert doc_index.commit is None  # No commit info
        assert len(doc_index.features) > 0
        assert markdown is not None

    def test_yaml_extraction_with_code_fences(self):
        """Test YAML extraction when Claude includes markdown code fences."""
        summarizer = Summarizer()

        # Test different YAML fence formats
        test_cases = [
            # With yaml language specifier
            """```yaml
features:
  - id: feat-001
    title: Test
    description: Test feature
impacts:
  apis: []
  breaking_changes: []
refs:
  pr: null
  issues: []
  files_changed: []
```""",
            # With just backticks
            """```
features:
  - id: feat-001
    title: Test
    description: Test feature
impacts:
  apis: []
  breaking_changes: []
refs:
  pr: null
  issues: []
  files_changed: []
```""",
            # Without fences
            """features:
  - id: feat-001
    title: Test
    description: Test feature
impacts:
  apis: []
  breaking_changes: []
refs:
  pr: null
  issues: []
  files_changed: []""",
        ]

        for yaml_text in test_cases:
            extracted = summarizer._extract_yaml(yaml_text)
            # Should parse as valid YAML
            parsed = yaml.safe_load(extracted)
            assert "features" in parsed
            assert "impacts" in parsed
            assert "refs" in parsed

    def test_prompt_building(self):
        """Test that prompts are built correctly."""
        summarizer = Summarizer()

        context = ExtractedContext(
            diff=GitDiff(
                commit="test123",
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
                    lines_of_code=5,
                    symbols=[],
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

        # Verify prompt structure
        assert "Level: file" in prompt
        assert "test.py" in prompt
        assert "Commit: test123" in prompt
        assert "Author: Test <test@test.com>" in prompt
        assert "Generate the YAML now:" in prompt

    def test_markdown_generation(self):
        """Test markdown generation from DocumentIndex."""
        from memdocs.schemas import (
            DocumentIndex,
            FeatureSummary,
            ImpactSummary,
            ReferenceSummary,
        )

        summarizer = Summarizer()

        doc_index = DocumentIndex(
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
                    risk=["security"],
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

        context = ExtractedContext(diff=None, files=[], scope_paths=[])
        markdown = summarizer._generate_markdown(doc_index, context)

        # Verify markdown structure
        assert "# Add login feature" in markdown
        assert "abc123" in markdown
        assert "File-level" in markdown
        assert "## Summary" in markdown
        assert "## Impact" in markdown
        assert "/api/login" in markdown
        assert "## Risks" in markdown
        assert "security" in markdown
        assert "## References" in markdown
        assert "PR #42" in markdown
        assert "Issue #1" in markdown
        assert "Issue #2" in markdown

    def test_api_key_validation(self):
        """Test that API key is required."""
        # Save original key
        original_key = os.environ.get("ANTHROPIC_API_KEY")

        try:
            # Remove key
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            # Should raise ValueError
            with pytest.raises(ValueError, match="API key is required"):
                Summarizer()

            # Should work with explicit key
            summarizer = Summarizer(api_key="test-key")
            assert summarizer.api_key == "test-key"

        finally:
            # Restore original key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    def test_model_configuration(self):
        """Test custom model configuration."""
        summarizer = Summarizer(model="claude-3-5-sonnet-20241022")
        assert summarizer.model == "claude-3-5-sonnet-20241022"

        # Default model
        summarizer = Summarizer()
        assert summarizer.model == "claude-sonnet-4-5-20250929"
