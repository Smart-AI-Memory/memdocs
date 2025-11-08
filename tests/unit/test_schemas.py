"""
Unit tests for schemas module.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from memdocs.schemas import (
    AIConfig,
    DocIntConfig,
    DocumentIndex,
    FeatureSummary,
    ImpactSummary,
    PHIMode,
    PolicyConfig,
    PrivacyConfig,
    ReferenceSummary,
    ScopeInfo,
    ScopeLevel,
    Symbol,
    SymbolKind,
)


class TestSchemas:
    """Test schema validation and serialization."""

    def test_symbol_validation(self):
        """Test Symbol schema validation."""
        symbol = Symbol(
            file=Path("test.py"),
            kind=SymbolKind.FUNCTION,
            name="test_func",
            line=10,
            signature="def test_func(x: int) -> str",
            doc="Test function",
        )
        assert symbol.name == "test_func"
        assert symbol.kind == SymbolKind.FUNCTION
        assert symbol.line == 10

    def test_symbol_invalid_line(self):
        """Test Symbol validation fails for invalid line number."""
        with pytest.raises(ValidationError):
            Symbol(
                file=Path("test.py"),
                kind=SymbolKind.FUNCTION,
                name="test_func",
                line=0,  # Line must be >= 1
            )

    def test_feature_summary_id_pattern(self):
        """Test FeatureSummary ID pattern validation."""
        # Valid ID
        feature = FeatureSummary(
            id="feat-001",
            title="Test feature",
        )
        assert feature.id == "feat-001"

        # Invalid ID pattern
        with pytest.raises(ValidationError):
            FeatureSummary(
                id="invalid-id",
                title="Test feature",
            )

    def test_feature_summary_title_length(self):
        """Test FeatureSummary title length validation."""
        # Valid title
        feature = FeatureSummary(
            id="feat-001",
            title="Short title",
        )
        assert len(feature.title) <= 200

        # Title too long
        with pytest.raises(ValidationError):
            FeatureSummary(
                id="feat-001",
                title="x" * 201,
            )

    def test_scope_info(self):
        """Test ScopeInfo schema."""
        scope = ScopeInfo(
            paths=[Path("src/module.py")],
            level=ScopeLevel.FILE,
            file_count=1,
            escalated=False,
        )
        assert scope.level == ScopeLevel.FILE
        assert scope.file_count == 1
        assert not scope.escalated

    def test_document_index_serialization(self):
        """Test DocumentIndex JSON serialization."""
        doc_index = DocumentIndex(
            commit="abc123",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            scope=ScopeInfo(
                paths=[Path("test.py")],
                level=ScopeLevel.FILE,
                file_count=1,
            ),
            features=[
                FeatureSummary(
                    id="feat-001",
                    title="Test feature",
                    description="Test description",
                )
            ],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(
                files_changed=[Path("test.py")],
            ),
        )

        # Test serialization to dict
        data = doc_index.model_dump(mode="json")
        assert data["commit"] == "abc123"
        assert data["scope"]["level"] == "file"
        assert len(data["features"]) == 1

    def test_policy_config_defaults(self):
        """Test PolicyConfig default values."""
        policy = PolicyConfig()
        assert policy.default_scope == ScopeLevel.FILE
        assert policy.max_files_without_force == 150
        assert "cross_module_changes" in policy.escalate_on

    def test_privacy_config(self):
        """Test PrivacyConfig."""
        privacy = PrivacyConfig(
            phi_mode=PHIMode.STRICT,
            scrub=["email", "ssn"],
            audit_redactions=True,
        )
        assert privacy.phi_mode == PHIMode.STRICT
        assert "email" in privacy.scrub
        assert privacy.audit_redactions

    def test_ai_config_defaults(self):
        """Test AIConfig default values."""
        ai_config = AIConfig()
        assert ai_config.provider == "anthropic"
        assert ai_config.model == "claude-sonnet-4-5-20250929"
        assert ai_config.max_tokens == 4096

    def test_ai_config_validation(self):
        """Test AIConfig max_tokens validation."""
        # Valid range
        ai_config = AIConfig(max_tokens=2048)
        assert ai_config.max_tokens == 2048

        # Below minimum
        with pytest.raises(ValidationError):
            AIConfig(max_tokens=512)

        # Above maximum
        with pytest.raises(ValidationError):
            AIConfig(max_tokens=300000)

    def test_docint_config(self):
        """Test DocIntConfig composition."""
        config = DocIntConfig()
        assert config.version == 1
        assert isinstance(config.policies, PolicyConfig)
        assert isinstance(config.privacy, PrivacyConfig)
        assert isinstance(config.ai, AIConfig)

    def test_docint_config_version_validation(self):
        """Test DocIntConfig version validation."""
        with pytest.raises(ValidationError):
            DocIntConfig(version=2)  # Only version 1 is supported

    def test_impact_summary(self):
        """Test ImpactSummary schema."""
        impact = ImpactSummary(
            apis=["/api/users", "/api/posts"],
            breaking_changes=["Removed old endpoint"],
            tests_added=5,
            tests_modified=3,
            migration_required=True,
        )
        assert len(impact.apis) == 2
        assert impact.tests_added == 5
        assert impact.migration_required

    def test_reference_summary(self):
        """Test ReferenceSummary schema."""
        refs = ReferenceSummary(
            pr=123,
            issues=[456, 789],
            files_changed=[Path("src/main.py"), Path("tests/test_main.py")],
            commits=["abc123", "def456"],
        )
        assert refs.pr == 123
        assert len(refs.issues) == 2
        assert len(refs.files_changed) == 2
