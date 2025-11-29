"""Tests for setup-hooks command module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from memdocs.cli_modules.commands.setup_hooks_cmd import (
    _create_post_commit_hook,
    _create_pre_commit_hook,
    _create_pre_push_hook,
    _get_git_hooks_dir,
    _is_git_repo,
    setup_hooks,
)


class TestIsGitRepo:
    """Tests for _is_git_repo."""

    def test_is_git_repo_true(self):
        """Test when in a git repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert _is_git_repo() is True

    def test_is_git_repo_false(self):
        """Test when not in a git repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            assert _is_git_repo() is False

    def test_is_git_repo_git_not_found(self):
        """Test when git is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert _is_git_repo() is False


class TestGetGitHooksDir:
    """Tests for _get_git_hooks_dir."""

    def test_get_git_hooks_dir_success(self):
        """Test getting hooks directory from git."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=".git\n")
            result = _get_git_hooks_dir()
            assert result == Path(".git/hooks")

    def test_get_git_hooks_dir_error(self):
        """Test fallback when git command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            result = _get_git_hooks_dir()
            assert result == Path(".git/hooks")


class TestCreatePreCommitHook:
    """Tests for _create_pre_commit_hook."""

    def test_create_pre_commit_hook(self, tmp_path):
        """Test creating pre-commit hook."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        _create_pre_commit_hook(hooks_dir)

        hook_file = hooks_dir / "pre-commit"
        assert hook_file.exists()
        content = hook_file.read_text()
        assert "MemDocs pre-commit hook" in content
        assert "staged files" in content.lower()
        # Check executable permissions
        assert hook_file.stat().st_mode & 0o111  # At least one execute bit


class TestCreatePostCommitHook:
    """Tests for _create_post_commit_hook."""

    def test_create_post_commit_hook(self, tmp_path):
        """Test creating post-commit hook."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        _create_post_commit_hook(hooks_dir)

        hook_file = hooks_dir / "post-commit"
        assert hook_file.exists()
        content = hook_file.read_text()
        assert "MemDocs post-commit hook" in content
        assert "HEAD~1" in content
        # Check executable permissions
        assert hook_file.stat().st_mode & 0o111


class TestCreatePrePushHook:
    """Tests for _create_pre_push_hook."""

    def test_create_pre_push_hook(self, tmp_path):
        """Test creating pre-push hook."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        _create_pre_push_hook(hooks_dir)

        hook_file = hooks_dir / "pre-push"
        assert hook_file.exists()
        content = hook_file.read_text()
        assert "MemDocs pre-push hook" in content
        assert "--changed" in content
        # Check executable permissions
        assert hook_file.stat().st_mode & 0o111


class TestSetupHooksCommand:
    """Tests for setup_hooks CLI command."""

    def test_setup_hooks_not_git_repo(self, tmp_path, monkeypatch):
        """Test command fails when not in git repo."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=False,
        ):
            result = runner.invoke(setup_hooks, ["--all"])
            assert result.exit_code != 0
            assert "not a git repository" in result.output.lower()

    def test_setup_hooks_no_options(self, tmp_path, monkeypatch):
        """Test command fails when no hooks selected."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=tmp_path / ".git" / "hooks",
            ):
                result = runner.invoke(setup_hooks, [])
                assert result.exit_code != 0
                assert "no hooks selected" in result.output.lower()

    def test_setup_hooks_install_all(self, tmp_path, monkeypatch):
        """Test installing all hooks."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--all"])
                assert result.exit_code == 0
                assert "installed" in result.output.lower()

                # Verify all hooks created
                assert (hooks_dir / "pre-commit").exists()
                assert (hooks_dir / "post-commit").exists()
                assert (hooks_dir / "pre-push").exists()

    def test_setup_hooks_install_post_commit_only(self, tmp_path, monkeypatch):
        """Test installing only post-commit hook."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--post-commit"])
                assert result.exit_code == 0
                assert (hooks_dir / "post-commit").exists()
                assert not (hooks_dir / "pre-commit").exists()
                assert not (hooks_dir / "pre-push").exists()

    def test_setup_hooks_install_pre_commit_only(self, tmp_path, monkeypatch):
        """Test installing only pre-commit hook."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--pre-commit"])
                assert result.exit_code == 0
                assert (hooks_dir / "pre-commit").exists()

    def test_setup_hooks_install_pre_push_only(self, tmp_path, monkeypatch):
        """Test installing only pre-push hook."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--pre-push"])
                assert result.exit_code == 0
                assert (hooks_dir / "pre-push").exists()

    def test_setup_hooks_remove(self, tmp_path, monkeypatch):
        """Test removing hooks."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create existing MemDocs hooks
        for hook_name in ["pre-commit", "post-commit", "pre-push"]:
            hook_file = hooks_dir / hook_name
            hook_file.write_text("#!/bin/sh\n# MemDocs hook\necho test")
            hook_file.chmod(0o755)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--remove"])
                assert result.exit_code == 0
                assert "removed" in result.output.lower()

                # Verify hooks removed
                assert not (hooks_dir / "pre-commit").exists()
                assert not (hooks_dir / "post-commit").exists()
                assert not (hooks_dir / "pre-push").exists()

    def test_setup_hooks_remove_no_memdocs_hooks(self, tmp_path, monkeypatch):
        """Test removing when no MemDocs hooks exist."""
        monkeypatch.chdir(tmp_path)
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create non-MemDocs hook
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/sh\necho 'Other hook'")

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                return_value=hooks_dir,
            ):
                result = runner.invoke(setup_hooks, ["--remove"])
                assert result.exit_code == 0
                # Non-MemDocs hook should still exist
                assert (hooks_dir / "pre-commit").exists()

    def test_setup_hooks_exception_handling(self, tmp_path, monkeypatch):
        """Test exception handling in setup_hooks."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        with patch(
            "memdocs.cli_modules.commands.setup_hooks_cmd._is_git_repo",
            return_value=True,
        ):
            with patch(
                "memdocs.cli_modules.commands.setup_hooks_cmd._get_git_hooks_dir",
                side_effect=Exception("Test error"),
            ):
                result = runner.invoke(setup_hooks, ["--all"])
                assert result.exit_code != 0
