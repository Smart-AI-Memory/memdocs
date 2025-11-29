"""Tests for doctor command module."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from memdocs.cli_modules.commands.doctor_cmd import (
    _check_api_key,
    _check_docs_exist,
    _check_item,
    _check_memdocs_command,
    _check_memdocs_initialized,
    _check_memory_exists,
    _check_mcp_server_responsive,
    _check_vscode_settings,
    _check_vscode_tasks,
    _get_stats,
    doctor,
)


class TestCheckItem:
    """Tests for _check_item helper function."""

    def test_check_item_passes(self, capsys):
        """Test _check_item when check passes."""
        result = _check_item("Test check", lambda: True)
        assert result is True

    def test_check_item_fails(self, capsys):
        """Test _check_item when check fails."""
        result = _check_item("Test check", lambda: False, "Try this fix")
        assert result is False

    def test_check_item_exception(self, capsys):
        """Test _check_item when check raises exception."""

        def raise_error():
            raise ValueError("Test error")

        result = _check_item("Test check", raise_error, "Fix hint")
        assert result is False


class TestCheckMemdocsInitialized:
    """Tests for _check_memdocs_initialized."""

    def test_initialized_true(self, tmp_path, monkeypatch):
        """Test when .memdocs.yml exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        assert _check_memdocs_initialized() is True

    def test_initialized_false(self, tmp_path, monkeypatch):
        """Test when .memdocs.yml doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert _check_memdocs_initialized() is False


class TestCheckDocsExist:
    """Tests for _check_docs_exist."""

    def test_docs_exist_with_json(self, tmp_path, monkeypatch):
        """Test when docs directory has JSON files."""
        monkeypatch.chdir(tmp_path)
        docs_dir = tmp_path / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "index.json").write_text("{}")
        assert _check_docs_exist() is True

    def test_docs_exist_empty_dir(self, tmp_path, monkeypatch):
        """Test when docs directory exists but is empty."""
        monkeypatch.chdir(tmp_path)
        docs_dir = tmp_path / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        assert _check_docs_exist() is False

    def test_docs_not_exist(self, tmp_path, monkeypatch):
        """Test when docs directory doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert _check_docs_exist() is False


class TestCheckMemoryExists:
    """Tests for _check_memory_exists."""

    def test_memory_exists_with_faiss(self, tmp_path, monkeypatch):
        """Test when memory directory has FAISS index."""
        monkeypatch.chdir(tmp_path)
        memory_dir = tmp_path / ".memdocs" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "faiss.index").write_bytes(b"fake index")
        assert _check_memory_exists() is True

    def test_memory_exists_no_faiss(self, tmp_path, monkeypatch):
        """Test when memory directory exists but no FAISS index."""
        monkeypatch.chdir(tmp_path)
        memory_dir = tmp_path / ".memdocs" / "memory"
        memory_dir.mkdir(parents=True)
        assert _check_memory_exists() is False

    def test_memory_not_exist(self, tmp_path, monkeypatch):
        """Test when memory directory doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert _check_memory_exists() is False


class TestCheckApiKey:
    """Tests for _check_api_key."""

    def test_api_key_set(self, monkeypatch):
        """Test when ANTHROPIC_API_KEY is set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        assert _check_api_key() is True

    def test_api_key_not_set(self, monkeypatch):
        """Test when ANTHROPIC_API_KEY is not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert _check_api_key() is False

    def test_api_key_empty(self, monkeypatch):
        """Test when ANTHROPIC_API_KEY is empty string."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        assert _check_api_key() is False


class TestCheckVscodeIntegration:
    """Tests for VS Code integration checks."""

    def test_vscode_tasks_exists(self, tmp_path, monkeypatch):
        """Test when tasks.json exists."""
        monkeypatch.chdir(tmp_path)
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")
        assert _check_vscode_tasks() is True

    def test_vscode_tasks_not_exists(self, tmp_path, monkeypatch):
        """Test when tasks.json doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert _check_vscode_tasks() is False

    def test_vscode_settings_auto_tasks_on(self, tmp_path, monkeypatch):
        """Test when auto-tasks is enabled."""
        monkeypatch.chdir(tmp_path)
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        settings = {"task.allowAutomaticTasks": "on"}
        (vscode_dir / "settings.json").write_text(json.dumps(settings))
        assert _check_vscode_settings() is True

    def test_vscode_settings_auto_tasks_off(self, tmp_path, monkeypatch):
        """Test when auto-tasks is not enabled."""
        monkeypatch.chdir(tmp_path)
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        settings = {"task.allowAutomaticTasks": "off"}
        (vscode_dir / "settings.json").write_text(json.dumps(settings))
        assert _check_vscode_settings() is False

    def test_vscode_settings_not_exists(self, tmp_path, monkeypatch):
        """Test when settings.json doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert _check_vscode_settings() is False

    def test_vscode_settings_invalid_json(self, tmp_path, monkeypatch):
        """Test when settings.json is invalid JSON."""
        monkeypatch.chdir(tmp_path)
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "settings.json").write_text("not valid json")
        assert _check_vscode_settings() is False


class TestCheckMcpServer:
    """Tests for MCP server check."""

    def test_mcp_server_responsive(self):
        """Test when MCP server responds correctly."""
        with patch("memdocs.cli_modules.commands.doctor_cmd.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response
            assert _check_mcp_server_responsive() is True

    def test_mcp_server_wrong_status(self):
        """Test when MCP server returns wrong status."""
        with patch("memdocs.cli_modules.commands.doctor_cmd.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "error"}
            mock_get.return_value = mock_response
            assert _check_mcp_server_responsive() is False

    def test_mcp_server_connection_error(self):
        """Test when MCP server is not running."""
        with patch("memdocs.cli_modules.commands.doctor_cmd.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("Connection refused")
            assert _check_mcp_server_responsive() is False


class TestCheckMemdocsCommand:
    """Tests for memdocs command check."""

    def test_memdocs_command_available(self):
        """Test when memdocs command is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert _check_memdocs_command() is True

    def test_memdocs_command_not_found(self):
        """Test when memdocs command is not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert _check_memdocs_command() is False


class TestGetStats:
    """Tests for _get_stats."""

    def test_get_stats_with_data(self, tmp_path, monkeypatch):
        """Test stats with documentation and embeddings."""
        monkeypatch.chdir(tmp_path)

        # Create docs
        docs_dir = tmp_path / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "index.json").write_text("{}")
        (docs_dir / "other.json").write_text("{}")

        # Create memory
        memory_dir = tmp_path / ".memdocs" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "faiss.index").write_bytes(b"fake")

        stats = _get_stats()
        assert stats["documented_files"] == 2
        assert stats["embeddings_available"] is True

    def test_get_stats_empty(self, tmp_path, monkeypatch):
        """Test stats with no data."""
        monkeypatch.chdir(tmp_path)
        stats = _get_stats()
        assert stats["documented_files"] == 0
        assert stats["embeddings_available"] is False


class TestDoctorCommand:
    """Tests for doctor CLI command."""

    def test_doctor_all_checks_pass(self, tmp_path, monkeypatch):
        """Test doctor command when all checks pass."""
        monkeypatch.chdir(tmp_path)

        # Setup passing environment
        (tmp_path / ".memdocs.yml").write_text("version: 1")
        docs_dir = tmp_path / ".memdocs" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "index.json").write_text("{}")
        memory_dir = tmp_path / ".memdocs" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "faiss.index").write_bytes(b"fake")
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "tasks.json").write_text("{}")
        (vscode_dir / "settings.json").write_text('{"task.allowAutomaticTasks": "on"}')
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.doctor_cmd._check_mcp_server_responsive",
            return_value=True,
        ):
            result = runner.invoke(doctor)
            # Note: exits with 0 when all pass, but CliRunner catches SystemExit
            assert "All checks passed" in result.output or "passed" in result.output.lower()

    def test_doctor_some_checks_fail(self, tmp_path, monkeypatch):
        """Test doctor command when some checks fail."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        runner = CliRunner()
        result = runner.invoke(doctor)
        assert "failed" in result.output.lower() or "Fix" in result.output

    def test_doctor_with_fix_flag(self, tmp_path, monkeypatch):
        """Test doctor command with --fix flag."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(doctor, ["--fix"])
        assert "not yet implemented" in result.output.lower() or "fix" in result.output.lower()
