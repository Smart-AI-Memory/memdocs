"""
Integration tests for CLI module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from memdocs.cli import export, main


class TestCLI:
    """Test command-line interface."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_cli_help(self, cli_runner: CliRunner):
        """Test --help flag."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "MemDocs" in result.output

    def test_cli_version(self, cli_runner: CliRunner):
        """Test --version flag."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output

    def test_export_command_no_docs(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export command when no docs exist."""
        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                export, ["cursor", "--docs-dir", str(temp_repo / ".memdocs" / "docs")]
            )
            assert result.exit_code != 0  # Should fail (exit code 1 or 2)
            assert "not found" in result.output.lower()

    def test_export_command_cursor(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export to Cursor format."""
        # Create minimal docs structure
        docs_dir = temp_repo / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "summary.md").write_text("# Test Summary\n\nThis is a test.")

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                export,
                [
                    "cursor",
                    "--docs-dir",
                    str(docs_dir),
                    "--output",
                    str(temp_repo / ".cursorrules"),
                ],
            )
            assert result.exit_code == 0
            assert "Exported" in result.output

            # Check output file was created
            output_file = temp_repo / ".cursorrules"
            assert output_file.exists()
            content = output_file.read_text()
            assert "Test Summary" in content
            assert "doc-intelligence" in content

    def test_export_command_claude(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export to Claude format."""
        docs_dir = temp_repo / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "summary.md").write_text("# Claude Test\n\nClaude context.")

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                export,
                [
                    "claude",
                    "--docs-dir",
                    str(docs_dir),
                    "--output",
                    str(temp_repo / ".claude-context.md"),
                ],
            )
            assert result.exit_code == 0

            output_file = temp_repo / ".claude-context.md"
            assert output_file.exists()
            content = output_file.read_text()
            assert "Claude context" in content

    def test_export_with_symbols(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export including symbols."""
        docs_dir = temp_repo / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "summary.md").write_text("# Summary")

        # Create symbols.yaml
        import yaml

        symbols_data = {
            "symbols": [
                {
                    "file": "test.py",
                    "kind": "function",
                    "name": "test_func",
                    "line": 10,
                    "signature": "def test_func()",
                }
            ]
        }
        with open(docs_dir / "symbols.yaml", "w") as f:
            yaml.dump(symbols_data, f)

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                export,
                [
                    "cursor",
                    "--docs-dir",
                    str(docs_dir),
                    "--output",
                    str(temp_repo / ".cursorrules"),
                    "--include-symbols",
                ],
            )
            assert result.exit_code == 0
            assert "1 code symbols" in result.output

            output_file = temp_repo / ".cursorrules"
            content = output_file.read_text()
            assert "test_func" in content
            assert "Code Map" in content

    def test_export_without_symbols(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export excluding symbols."""
        docs_dir = temp_repo / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "summary.md").write_text("# Summary")

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                export,
                [
                    "cursor",
                    "--docs-dir",
                    str(docs_dir),
                    "--output",
                    str(temp_repo / ".cursorrules"),
                    "--no-symbols",
                ],
            )
            assert result.exit_code == 0

            output_file = temp_repo / ".cursorrules"
            content = output_file.read_text()
            assert "Code Map" not in content

    @patch("memdocs.cli.MemoryIndexer")
    def test_query_command_no_index(self, mock_indexer, cli_runner: CliRunner, temp_repo: Path):
        """Test query command when index doesn't exist."""
        from memdocs.cli import query

        # Mock indexer with no entries
        mock_instance = MagicMock()
        mock_instance.get_stats.return_value = {"total": 0, "active": 0}
        mock_indexer.return_value = mock_instance

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                query,
                ["test query", "--memory-dir", str(temp_repo / ".memdocs" / "memory")],
            )
            assert result.exit_code != 0  # Should fail (exit code 1 or 2)
            assert "empty" in result.output.lower()

    def test_cleanup_command(self, cli_runner: CliRunner, temp_repo: Path):
        """Test cleanup command (placeholder implementation)."""
        from memdocs.cli import cleanup

        memory_dir = temp_repo / ".memdocs" / "memory"
        memory_dir.mkdir(parents=True)

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                cleanup,
                ["--older-than", "90d", "--memory-dir", str(memory_dir), "--dry-run"],
            )
            # Currently just a placeholder, should not error
            assert result.exit_code == 0
            assert "not yet implemented" in result.output

    def test_init_command(self, cli_runner: CliRunner, temp_repo: Path):
        """Test init command creates config and directories."""
        from memdocs.cli import init

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(init, [])

            assert result.exit_code == 0
            assert "Initialization Complete" in result.output

            # Check created files (in current directory after isolated_filesystem)
            assert Path(".memdocs.yml").exists()
            assert Path(".memdocs/docs").exists()
            assert Path(".memdocs/memory").exists()

            # Check config content
            config_content = Path(".memdocs.yml").read_text()
            assert "version: 1" in config_content
            assert "claude-sonnet-4-5-20250929" in config_content

    def test_init_command_already_initialized(self, cli_runner: CliRunner, temp_repo: Path):
        """Test init command when already initialized."""
        from memdocs.cli import init

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            # First init
            result1 = cli_runner.invoke(init, [])
            assert result1.exit_code == 0

            # Second init without force
            result2 = cli_runner.invoke(init, [])
            assert result2.exit_code == 0
            assert "already initialized" in result2.output.lower()

    def test_init_command_force(self, cli_runner: CliRunner, temp_repo: Path):
        """Test init command with --force flag."""
        from memdocs.cli import init

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            # First init
            result1 = cli_runner.invoke(init, [])
            assert result1.exit_code == 0

            # Second init with force
            result2 = cli_runner.invoke(init, ["--force"])
            assert result2.exit_code == 0
            assert "Initialization Complete" in result2.output

    def test_stats_command_no_data(self, cli_runner: CliRunner, temp_repo: Path):
        """Test stats command when no data exists."""
        from memdocs.cli import stats

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                stats,
                [
                    "--docs-dir",
                    str(temp_repo / ".memdocs/docs"),
                    "--memory-dir",
                    str(temp_repo / ".memdocs/memory"),
                ],
            )
            assert result.exit_code == 0
            assert "Statistics" in result.output

    def test_stats_command_with_data(self, cli_runner: CliRunner, temp_repo: Path):
        """Test stats command with existing data."""
        from memdocs.cli import stats

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            # Create data structure
            docs_dir = Path(".memdocs/docs")
            memory_dir = Path(".memdocs/memory")
            docs_dir.mkdir(parents=True)
            memory_dir.mkdir(parents=True)

            (docs_dir / "index.json").write_text('{"test": "data"}')
            (docs_dir / "summary.md").write_text("# Test")
            (memory_dir / "graph.json").write_text('{"test": "data"}')

            result = cli_runner.invoke(
                stats,
                [
                    "--docs-dir",
                    str(docs_dir),
                    "--memory-dir",
                    str(memory_dir),
                ],
            )
            assert result.exit_code == 0
            assert "Documentation" in result.output
            assert "Memory" in result.output

    def test_stats_command_json_format(self, cli_runner: CliRunner, temp_repo: Path):
        """Test stats command with JSON output."""
        from memdocs.cli import stats

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            docs_dir = Path(".memdocs/docs")
            memory_dir = Path(".memdocs/memory")
            docs_dir.mkdir(parents=True)
            memory_dir.mkdir(parents=True)

            result = cli_runner.invoke(
                stats,
                [
                    "--docs-dir",
                    str(docs_dir),
                    "--memory-dir",
                    str(memory_dir),
                    "--format",
                    "json",
                ],
            )
            assert result.exit_code == 0
            # Should have JSON output
            assert "{" in result.output

    @patch("memdocs.cli.Summarizer")
    @patch("memdocs.cli.Extractor")
    def test_review_command_no_path(
        self, mock_extractor, mock_summarizer, cli_runner: CliRunner, temp_repo: Path
    ):
        """Test review command without path."""
        from memdocs.cli import review

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            # Create config so we get past config validation
            Path(".memdocs.yml").write_text("version: 1")

            result = cli_runner.invoke(review, [])
            assert result.exit_code != 0
            assert "Must specify" in result.output

    @patch("memdocs.cli.Summarizer")
    @patch("memdocs.cli.Extractor")
    @patch("memdocs.cli.PolicyEngine")
    def test_review_command_with_path_mock(
        self,
        mock_policy_class,
        mock_extractor_class,
        mock_summarizer_class,
        cli_runner: CliRunner,
        temp_repo: Path
    ):
        """Test review command with mocked dependencies."""
        from datetime import datetime, timezone
        from memdocs.cli import review
        from memdocs.extract import ExtractedContext, FileContext, GitDiff
        from memdocs.schemas import (
            DocumentIndex,
            FeatureSummary,
            ImpactSummary,
            ReferenceSummary,
            ScopeInfo,
            ScopeLevel,
        )

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            # Create test file
            Path("test.py").write_text("def test(): pass")

            # Create config
            Path(".memdocs.yml").write_text(
                """version: 1
policies:
  default_scope: file
outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown
ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
privacy:
  phi_mode: "off"
  scrub: []
"""
            )

            # Mock extractor
            mock_extractor = MagicMock()
            mock_context = ExtractedContext(
                diff=GitDiff(
                    commit="test123",
                    author="Test User <test@example.com>",
                    message="Test commit",
                    timestamp="2025-01-08T00:00:00Z",
                    added_files=[Path("test.py")],
                    modified_files=[],
                    deleted_files=[],
                    all_changed_files=[Path("test.py")],
                ),
                files=[
                    FileContext(
                        path=Path("test.py"),
                        language="python",
                        lines_of_code=1,
                        symbols=[],
                        imports=[],
                        dependencies=[],
                    )
                ],
                scope_paths=[Path("test.py")],
            )
            mock_extractor.extract_context.return_value = mock_context
            mock_extractor_class.return_value = mock_extractor

            # Mock policy engine
            mock_policy = MagicMock()
            mock_scope = ScopeInfo(
                paths=[Path("test.py")],
                level=ScopeLevel.FILE,
                file_count=1,
                escalated=False,
            )
            mock_policy.determine_scope.return_value = mock_scope
            mock_policy.validate_scope.return_value = []  # No warnings
            mock_policy_class.return_value = mock_policy

            # Mock summarizer
            mock_summarizer = MagicMock()
            mock_doc_index = DocumentIndex(
                commit="test123",
                timestamp=datetime.now(timezone.utc),
                scope=mock_scope,
                features=[
                    FeatureSummary(
                        id="feat-1",
                        title="Test Feature",
                        summary="A test feature",
                        category="feature",
                        impact="low",
                    )
                ],
                impacts=ImpactSummary(
                    apis=[],
                    breaking_changes=[],
                    tests_added=0,
                    tests_modified=0,
                    migration_required=False,
                ),
                refs=ReferenceSummary(
                    pr=None,
                    issues=[],
                    files_changed=[Path("test.py")],
                    commits=["test123"],
                ),
            )
            mock_summarizer.summarize.return_value = (mock_doc_index, "# Test Summary")
            mock_summarizer_class.return_value = mock_summarizer

            result = cli_runner.invoke(
                review,
                [
                    "--path",
                    "test.py",
                    "--config",
                    ".memdocs.yml",
                ],
            )

            # Should succeed
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Review Complete" in result.output

            # Check outputs were created
            docs_dir = Path(".memdocs/docs")
            assert docs_dir.exists(), "Docs directory was not created"
            assert (docs_dir / "index.json").exists(), "index.json was not created"
            assert (docs_dir / "summary.md").exists(), "summary.md was not created"
            assert (docs_dir / "symbols.yaml").exists(), "symbols.yaml was not created"

            # Verify mocks were called correctly
            mock_extractor.extract_context.assert_called_once()
            mock_policy.determine_scope.assert_called_once()
            mock_summarizer.summarize.assert_called_once()

    @patch("memdocs.cli.MemoryIndexer")
    def test_query_command_with_results(
        self, mock_indexer_class, cli_runner: CliRunner, temp_repo: Path
    ):
        """Test query command with results."""
        from memdocs.cli import query

        # Mock indexer with results
        mock_indexer = MagicMock()
        mock_indexer.use_embeddings = True
        mock_indexer.get_stats.return_value = {"total": 5, "active": 5, "dimensions": 384}
        mock_indexer.query_memory.return_value = [
            {
                "score": 0.95,
                "metadata": {
                    "features": ["Test Feature"],
                    "file_paths": ["test.py"],
                    "chunk_text": "This is a test chunk",
                },
            }
        ]
        mock_indexer_class.return_value = mock_indexer

        memory_dir = temp_repo / ".memdocs/memory"
        memory_dir.mkdir(parents=True)

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(
                query, ["test query", "--memory-dir", str(memory_dir), "--k", "5"]
            )

            assert result.exit_code == 0
            assert "Search Results" in result.output or "Found" in result.output

    @patch("memdocs.cli.MemoryIndexer")
    def test_query_command_no_embeddings(
        self, mock_indexer_class, cli_runner: CliRunner, temp_repo: Path
    ):
        """Test query command when embeddings not available."""
        from memdocs.cli import query

        # Mock indexer without embeddings
        mock_indexer = MagicMock()
        mock_indexer.use_embeddings = False
        mock_indexer_class.return_value = mock_indexer

        memory_dir = temp_repo / ".memdocs/memory"
        memory_dir.mkdir(parents=True)

        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(query, ["test", "--memory-dir", str(memory_dir)])

            assert result.exit_code != 0
            assert "not available" in result.output.lower()
