"""Tests for update-config command module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from memdocs.cli_modules.commands.update_config_cmd import update_config


class TestUpdateConfigCommand:
    """Tests for update_config CLI command."""

    def test_update_config_not_initialized(self, tmp_path, monkeypatch):
        """Test command fails when MemDocs not initialized."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(update_config, ["--mcp"])
        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()

    def test_update_config_no_target(self, tmp_path, monkeypatch):
        """Test command fails when no update target specified."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")

        runner = CliRunner()
        result = runner.invoke(update_config, [])
        assert result.exit_code != 0
        assert "no update target" in result.output.lower()

    def test_update_config_mcp_new_install(self, tmp_path, monkeypatch):
        """Test updating MCP config when no existing files."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure"
        ) as mock_setup:
            result = runner.invoke(update_config, ["--mcp"])
            assert result.exit_code == 0
            mock_setup.assert_called_once()

    def test_update_config_mcp_existing_files_no_force(self, tmp_path, monkeypatch):
        """Test updating MCP config with existing files, no force, user declines."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")

        runner = CliRunner()
        with patch("memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure"):
            # User says no to overwrite
            result = runner.invoke(update_config, ["--mcp"], input="n\n")
            assert "cancelled" in result.output.lower()

    def test_update_config_mcp_existing_files_user_confirms(self, tmp_path, monkeypatch):
        """Test updating MCP config with existing files, user confirms."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure"
        ) as mock_setup:
            # User says yes to overwrite
            result = runner.invoke(update_config, ["--mcp"], input="y\n")
            assert result.exit_code == 0
            mock_setup.assert_called_once()

    def test_update_config_mcp_with_force(self, tmp_path, monkeypatch):
        """Test updating MCP config with --force flag."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")
        (vscode_dir / "settings.json").write_text("{}")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure"
        ) as mock_setup:
            result = runner.invoke(update_config, ["--mcp", "--force"])
            assert result.exit_code == 0
            mock_setup.assert_called_once()
            assert "updated" in result.output.lower()

    def test_update_config_exception_handling(self, tmp_path, monkeypatch):
        """Test exception handling in update_config."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure",
            side_effect=Exception("Test error"),
        ):
            result = runner.invoke(update_config, ["--mcp", "--force"])
            assert result.exit_code != 0
            assert "failed" in result.output.lower()

    def test_update_config_mcp_both_files_exist(self, tmp_path, monkeypatch):
        """Test warning shows both existing files."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")
        (vscode_dir / "settings.json").write_text("{}")

        runner = CliRunner()
        with patch("memdocs.cli_modules.commands.update_config_cmd._setup_mcp_infrastructure"):
            result = runner.invoke(update_config, ["--mcp"], input="n\n")
            # Normalize output by removing newlines to handle line-wrapping in CI
            normalized_output = result.output.replace("\n", "")
            assert "tasks.json" in normalized_output
            assert "settings.json" in normalized_output
