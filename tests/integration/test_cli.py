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
        assert "Doc-Intelligence" in result.output

    def test_cli_version(self, cli_runner: CliRunner):
        """Test --version flag."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output

    def test_export_command_no_docs(self, cli_runner: CliRunner, temp_repo: Path):
        """Test export command when no docs exist."""
        with cli_runner.isolated_filesystem(temp_dir=temp_repo):
            result = cli_runner.invoke(export, ["cursor", "--docs-dir", str(temp_repo / ".memdocs" / "docs")])
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
                    "--docs-dir", str(docs_dir),
                    "--output", str(temp_repo / ".cursorrules"),
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
                    "--docs-dir", str(docs_dir),
                    "--output", str(temp_repo / ".claude-context.md"),
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
                    "--docs-dir", str(docs_dir),
                    "--output", str(temp_repo / ".cursorrules"),
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
                    "--docs-dir", str(docs_dir),
                    "--output", str(temp_repo / ".cursorrules"),
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
