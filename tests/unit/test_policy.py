"""
Unit tests for policy module.
"""

from pathlib import Path

import pytest

from memdocs.extract import ExtractedContext, FileContext
from memdocs.policy import PolicyEngine
from memdocs.schemas import DocIntConfig, ScopeLevel, Symbol, SymbolKind


class TestPolicyEngine:
    """Test policy engine for scope determination."""

    @pytest.fixture
    def policy_engine(self):
        """Create a PolicyEngine instance."""
        config = DocIntConfig()
        return PolicyEngine(config)

    @pytest.fixture
    def sample_context(self):
        """Create sample extracted context."""
        files = [
            FileContext(
                path=Path("src/main.py"),
                language="Python",
                lines_of_code=100,
                symbols=[
                    Symbol(
                        file=Path("src/main.py"),
                        kind=SymbolKind.FUNCTION,
                        name="main",
                        line=10,
                    )
                ],
                imports=[],
                dependencies=[],
            )
        ]
        return ExtractedContext(
            diff=None,
            files=files,
            scope_paths=[Path("src/main.py")],
        )

    def test_determine_file_scope(self, policy_engine, sample_context):
        """Test file-level scope determination."""
        scope = policy_engine.determine_scope(
            requested_paths=[Path("src/main.py")],
            context=sample_context,
        )
        assert scope.level == ScopeLevel.FILE
        assert scope.file_count == 1
        assert not scope.escalated

    def test_determine_module_scope(self, policy_engine):
        """Test module-level scope determination."""
        context = ExtractedContext(
            diff=None,
            files=[
                FileContext(
                    path=Path("src/module/file1.py"),
                    language="Python",
                    lines_of_code=50,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                ),
                FileContext(
                    path=Path("src/module/file2.py"),
                    language="Python",
                    lines_of_code=50,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                ),
            ],
            scope_paths=[Path("src/module/file1.py"), Path("src/module/file2.py")],
        )

        scope = policy_engine.determine_scope(
            requested_paths=[Path("src/module/file1.py"), Path("src/module/file2.py")],
            context=context,
        )
        # Multiple files in same module should be MODULE level
        assert scope.level == ScopeLevel.MODULE

    def test_file_count_limit_exceeded(self, policy_engine):
        """Test file count limit without force flag."""
        # Create context with too many files
        files = [
            FileContext(
                path=Path(f"file{i}.py"),
                language="Python",
                lines_of_code=10,
                symbols=[],
                imports=[],
                dependencies=[],
            )
            for i in range(200)  # Exceeds default limit of 150
        ]
        context = ExtractedContext(diff=None, files=files, scope_paths=[Path(".")])

        with pytest.raises(ValueError, match="File count .* exceeds limit"):
            policy_engine.determine_scope(
                requested_paths=[Path(".")],
                context=context,
                force=False,
            )

    def test_file_count_limit_with_force(self, policy_engine):
        """Test file count limit with force flag."""
        files = [
            FileContext(
                path=Path(f"file{i}.py"),
                language="Python",
                lines_of_code=10,
                symbols=[],
                imports=[],
                dependencies=[],
            )
            for i in range(200)
        ]
        context = ExtractedContext(diff=None, files=files, scope_paths=[Path(".")])

        # Should not raise with force=True
        scope = policy_engine.determine_scope(
            requested_paths=[Path(".")],
            context=context,
            force=True,
        )
        assert scope.file_count == 200

    def test_escalation_security_paths(self, policy_engine):
        """Test escalation for security-sensitive paths."""
        context = ExtractedContext(
            diff=None,
            files=[
                FileContext(
                    path=Path("src/auth/login.py"),
                    language="Python",
                    lines_of_code=100,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                )
            ],
            scope_paths=[Path("src/auth/login.py")],
        )

        scope = policy_engine.determine_scope(
            requested_paths=[Path("src/auth/login.py")],
            context=context,
        )
        # Should escalate due to security path
        assert scope.escalated
        assert "security" in scope.escalation_reason.lower()

    def test_escalation_cross_module(self, policy_engine):
        """Test escalation for cross-module changes."""
        context = ExtractedContext(
            diff=None,
            files=[
                FileContext(
                    path=Path("module1/file.py"),
                    language="Python",
                    lines_of_code=50,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                ),
                FileContext(
                    path=Path("module2/file.py"),
                    language="Python",
                    lines_of_code=50,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                ),
            ],
            scope_paths=[Path("module1/file.py"), Path("module2/file.py")],
        )

        scope = policy_engine.determine_scope(
            requested_paths=[Path("module1/file.py"), Path("module2/file.py")],
            context=context,
        )
        # Should escalate due to cross-module changes
        assert scope.escalated
        assert "module" in scope.escalation_reason.lower()

    def test_validate_scope_warnings(self, policy_engine):
        """Test scope validation warnings."""
        from memdocs.schemas import ScopeInfo

        # Large repo-level scope should warn
        scope = ScopeInfo(
            paths=[Path(".")],
            level=ScopeLevel.REPO,
            file_count=200,
        )
        warnings = policy_engine.validate_scope(scope)
        assert len(warnings) > 0
        assert any("slow" in w.lower() for w in warnings)

    def test_touches_security_paths(self, policy_engine):
        """Test detection of security-sensitive paths."""
        context = ExtractedContext(
            diff=None,
            files=[
                FileContext(
                    path=Path("src/security/encryption.py"),
                    language="Python",
                    lines_of_code=100,
                    symbols=[],
                    imports=[],
                    dependencies=[],
                )
            ],
            scope_paths=[],
        )

        is_security = policy_engine._touches_security_paths(context)
        assert is_security

    def test_modifies_public_api(self, policy_engine):
        """Test detection of public API modifications."""
        context = ExtractedContext(
            diff=None,
            files=[
                FileContext(
                    path=Path("src/api/routes.py"),
                    language="Python",
                    lines_of_code=100,
                    symbols=[
                        Symbol(
                            file=Path("src/api/routes.py"),
                            kind=SymbolKind.FUNCTION,
                            name="get_users",
                            line=10,
                            signature="export function get_users()",
                        )
                    ],
                    imports=[],
                    dependencies=[],
                )
            ],
            scope_paths=[],
        )

        modifies_api = policy_engine._modifies_public_api(context)
        assert modifies_api
