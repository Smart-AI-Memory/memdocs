"""
Unit tests for cli_output module.
"""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from memdocs import cli_output


class TestStatusMessages:
    """Test status message functions."""

    @patch.object(cli_output.console, "print")
    def test_success(self, mock_print):
        """Test success message."""
        cli_output.success("Operation completed")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "✓" in args[0]
        assert "Operation completed" in args[0]
        assert "bold green" in args[0]

    @patch.object(cli_output.console, "print")
    def test_error(self, mock_print):
        """Test error message."""
        cli_output.error("Operation failed")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "✗" in args[0]
        assert "Operation failed" in args[0]
        assert "bold red" in args[0]
        kwargs = mock_print.call_args[1]
        assert kwargs.get("style") == "red"

    @patch.object(cli_output.console, "print")
    def test_warning(self, mock_print):
        """Test warning message."""
        cli_output.warning("This is a warning")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "⚠" in args[0]
        assert "This is a warning" in args[0]
        assert "bold yellow" in args[0]
        kwargs = mock_print.call_args[1]
        assert kwargs.get("style") == "yellow"

    @patch.object(cli_output.console, "print")
    def test_info(self, mock_print):
        """Test info message."""
        cli_output.info("Information message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "ℹ" in args[0]
        assert "Information message" in args[0]
        assert "bold blue" in args[0]

    @patch.object(cli_output.console, "print")
    def test_step(self, mock_print):
        """Test step message."""
        cli_output.step("Next step")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "→" in args[0]
        assert "Next step" in args[0]
        assert "bold cyan" in args[0]

    @patch.object(cli_output.console, "print")
    def test_empty_message(self, mock_print):
        """Test empty message handling."""
        cli_output.success("")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "✓" in args[0]

    @patch.object(cli_output.console, "print")
    def test_long_message(self, mock_print):
        """Test very long message."""
        long_msg = "x" * 1000
        cli_output.info(long_msg)
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert long_msg in args[0]

    @patch.object(cli_output.console, "print")
    def test_special_characters(self, mock_print):
        """Test message with special characters."""
        special_msg = "Test with <angle> [brackets] & {braces}"
        cli_output.success(special_msg)
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert special_msg in args[0]


class TestPanels:
    """Test panel output functions."""

    @patch.object(cli_output.console, "print")
    def test_panel_minimal(self, mock_print):
        """Test panel with minimal arguments."""
        cli_output.panel("Panel content")
        mock_print.assert_called_once()
        # Verify Panel was created
        from rich.panel import Panel

        panel_obj = mock_print.call_args[0][0]
        assert isinstance(panel_obj, Panel)

    @patch.object(cli_output.console, "print")
    def test_panel_with_title(self, mock_print):
        """Test panel with title."""
        cli_output.panel("Content here", title="My Title")
        mock_print.assert_called_once()
        panel_obj = mock_print.call_args[0][0]
        from rich.panel import Panel

        assert isinstance(panel_obj, Panel)

    @patch.object(cli_output.console, "print")
    def test_panel_with_style(self, mock_print):
        """Test panel with custom style."""
        cli_output.panel("Content", style="red")
        mock_print.assert_called_once()

    @patch.object(cli_output.console, "print")
    def test_panel_with_subtitle(self, mock_print):
        """Test panel with subtitle."""
        cli_output.panel("Content", title="Title", subtitle="Subtitle")
        mock_print.assert_called_once()

    @patch.object(cli_output.console, "print")
    def test_panel_all_options(self, mock_print):
        """Test panel with all options."""
        cli_output.panel(
            "Full content",
            title="Main Title",
            style="green",
            subtitle="Sub Title",
        )
        mock_print.assert_called_once()


class TestProgressBars:
    """Test progress bar context managers."""

    def test_progress_bar_context(self):
        """Test progress_bar context manager."""
        with cli_output.progress_bar("Testing") as progress:
            assert progress is not None
            task = progress.add_task("Task", total=10)
            progress.update(task, advance=5)
            # Context manager should work without errors

    def test_progress_bar_default_description(self):
        """Test progress_bar with default description."""
        with cli_output.progress_bar() as progress:
            assert progress is not None

    def test_progress_bar_custom_description(self):
        """Test progress_bar with custom description."""
        with cli_output.progress_bar("Custom description") as progress:
            assert progress is not None

    def test_spinner_context(self):
        """Test spinner context manager."""
        with cli_output.spinner("Working") as (progress, task):
            assert progress is not None
            assert task is not None

    def test_spinner_default_description(self):
        """Test spinner with default description."""
        with cli_output.spinner() as (progress, task):
            assert progress is not None
            assert task is not None

    def test_progress_bar_exception_handling(self):
        """Test progress_bar handles exceptions properly."""
        with pytest.raises(ValueError):
            with cli_output.progress_bar("Test") as progress:
                raise ValueError("Test error")

    def test_spinner_exception_handling(self):
        """Test spinner handles exceptions properly."""
        with pytest.raises(ValueError):
            with cli_output.spinner("Test") as (progress, task):
                raise ValueError("Test error")


class TestTables:
    """Test table creation and printing functions."""

    def test_create_table_minimal(self):
        """Test create_table with minimal arguments."""
        table = cli_output.create_table()
        assert isinstance(table, Table)

    def test_create_table_with_title(self):
        """Test create_table with title."""
        table = cli_output.create_table(title="My Table")
        assert isinstance(table, Table)

    def test_create_table_no_header(self):
        """Test create_table without header."""
        table = cli_output.create_table(show_header=False)
        assert isinstance(table, Table)

    def test_create_table_with_lines(self):
        """Test create_table with lines between rows."""
        table = cli_output.create_table(show_lines=True)
        assert isinstance(table, Table)

    def test_create_table_all_options(self):
        """Test create_table with all options."""
        table = cli_output.create_table(
            title="Full Table",
            show_header=True,
            show_lines=True,
        )
        assert isinstance(table, Table)

    @patch.object(cli_output.console, "print")
    def test_print_table(self, mock_print):
        """Test print_table function."""
        table = cli_output.create_table()
        table.add_column("Column 1")
        table.add_column("Column 2")
        table.add_row("A", "B")

        cli_output.print_table(table)
        mock_print.assert_called_once_with(table)

    @patch.object(cli_output.console, "print")
    def test_print_empty_table(self, mock_print):
        """Test print_table with empty table."""
        table = cli_output.create_table()
        cli_output.print_table(table)
        mock_print.assert_called_once()


class TestFileTrees:
    """Test file tree creation and printing functions."""

    def test_create_file_tree_empty(self):
        """Test create_file_tree with empty file list."""
        tree = cli_output.create_file_tree(Path("/root"), [])
        assert isinstance(tree, Tree)

    def test_create_file_tree_single_file_root(self):
        """Test create_file_tree with single file in root."""
        files = [Path("test.py")]
        tree = cli_output.create_file_tree(Path("/root"), files)
        assert isinstance(tree, Tree)

    def test_create_file_tree_single_file_subdir(self):
        """Test create_file_tree with file in subdirectory."""
        files = [Path("src/module.py")]
        tree = cli_output.create_file_tree(Path("/root"), files)
        assert isinstance(tree, Tree)

    def test_create_file_tree_multiple_files(self):
        """Test create_file_tree with multiple files."""
        files = [
            Path("test1.py"),
            Path("test2.py"),
            Path("src/module.py"),
            Path("src/utils.py"),
            Path("tests/test_module.py"),
        ]
        tree = cli_output.create_file_tree(Path("/root"), files)
        assert isinstance(tree, Tree)

    def test_create_file_tree_custom_title(self):
        """Test create_file_tree with custom title."""
        files = [Path("test.py")]
        tree = cli_output.create_file_tree(Path("/root"), files, title="Custom Title")
        assert isinstance(tree, Tree)

    def test_create_file_tree_nested_structure(self):
        """Test create_file_tree with deeply nested structure."""
        files = [
            Path("a/b/c/d/file.py"),
            Path("a/b/other.py"),
            Path("a/file1.py"),
        ]
        tree = cli_output.create_file_tree(Path("/root"), files)
        assert isinstance(tree, Tree)

    @patch.object(cli_output.console, "print")
    def test_print_tree(self, mock_print):
        """Test print_tree function."""
        tree = cli_output.create_file_tree(Path("/root"), [Path("test.py")])
        cli_output.print_tree(tree)
        mock_print.assert_called_once_with(tree)


class TestKeyValueDisplay:
    """Test key-value display functions."""

    @patch.object(cli_output.console, "print")
    def test_print_key_value_default_style(self, mock_print):
        """Test print_key_value with default style."""
        cli_output.print_key_value("Name", "Value")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "Name" in args[0]
        assert "Value" in args[0]
        assert "cyan" in args[0]

    @patch.object(cli_output.console, "print")
    def test_print_key_value_custom_style(self, mock_print):
        """Test print_key_value with custom style."""
        cli_output.print_key_value("Key", "Value", key_style="red")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "red" in args[0]

    @patch.object(cli_output.console, "print")
    def test_print_key_value_numeric(self, mock_print):
        """Test print_key_value with numeric value."""
        cli_output.print_key_value("Count", 42)
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "Count" in args[0]
        assert "42" in args[0]

    @patch.object(cli_output.console, "print")
    def test_print_key_value_boolean(self, mock_print):
        """Test print_key_value with boolean value."""
        cli_output.print_key_value("Enabled", True)
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "Enabled" in args[0]
        assert "True" in args[0]

    @patch.object(cli_output.console, "print")
    def test_print_dict_no_title(self, mock_print):
        """Test print_dict without title."""
        data = {"key1": "value1", "key2": "value2"}
        cli_output.print_dict(data)
        # Should be called for each key-value pair
        assert mock_print.call_count == 2

    @patch.object(cli_output.console, "print")
    def test_print_dict_with_title(self, mock_print):
        """Test print_dict with title."""
        data = {"key1": "value1", "key2": "value2"}
        cli_output.print_dict(data, title="My Data")
        # Should be called for title + each key-value pair
        assert mock_print.call_count == 3
        # First call should be the title
        first_call_args = mock_print.call_args_list[0][0]
        assert "My Data" in first_call_args[0]

    @patch.object(cli_output.console, "print")
    def test_print_dict_empty(self, mock_print):
        """Test print_dict with empty dictionary."""
        cli_output.print_dict({})
        # No key-value pairs to print
        mock_print.assert_not_called()

    @patch.object(cli_output.console, "print")
    def test_print_dict_complex_values(self, mock_print):
        """Test print_dict with complex values."""
        data = {
            "string": "text",
            "number": 123,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        cli_output.print_dict(data)
        assert mock_print.call_count == 4


class TestSummaryOutput:
    """Test summary output functions."""

    @patch.object(cli_output, "panel")
    def test_print_summary_minimal(self, mock_panel):
        """Test print_summary with minimal arguments."""
        items = {"key1": "value1", "key2": "value2"}
        cli_output.print_summary("Summary Title", items)
        mock_panel.assert_called_once()
        args, kwargs = mock_panel.call_args
        assert "key1" in args[0]
        assert "value1" in args[0]
        assert kwargs["title"] == "Summary Title"
        assert kwargs["style"] == "green"

    @patch.object(cli_output, "panel")
    def test_print_summary_custom_style(self, mock_panel):
        """Test print_summary with custom style."""
        items = {"key": "value"}
        cli_output.print_summary("Title", items, style="red")
        mock_panel.assert_called_once()
        args, kwargs = mock_panel.call_args
        assert kwargs["style"] == "red"

    @patch.object(cli_output, "panel")
    def test_print_summary_empty_items(self, mock_panel):
        """Test print_summary with empty items."""
        cli_output.print_summary("Empty Summary", {})
        mock_panel.assert_called_once()
        args, kwargs = mock_panel.call_args
        # Empty content
        assert args[0] == ""

    @patch.object(cli_output, "panel")
    def test_print_summary_multiple_items(self, mock_panel):
        """Test print_summary with multiple items."""
        items = {
            "Files": 10,
            "Lines": 1000,
            "Duration": "5.2s",
            "Status": "Complete",
        }
        cli_output.print_summary("Build Summary", items)
        mock_panel.assert_called_once()
        args, kwargs = mock_panel.call_args
        content = args[0]
        assert "Files" in content
        assert "Lines" in content
        assert "Duration" in content
        assert "Status" in content


class TestDurationFormatting:
    """Test duration formatting function."""

    def test_format_duration_milliseconds(self):
        """Test format_duration for values under 1 second."""
        assert cli_output.format_duration(0) == "0ms"
        assert cli_output.format_duration(500) == "500ms"
        assert cli_output.format_duration(999) == "999ms"

    def test_format_duration_seconds(self):
        """Test format_duration for values under 1 minute."""
        assert cli_output.format_duration(1000) == "1.0s"
        assert cli_output.format_duration(5500) == "5.5s"
        assert cli_output.format_duration(59999) == "60.0s"

    def test_format_duration_minutes(self):
        """Test format_duration for values over 1 minute."""
        assert cli_output.format_duration(60000) == "1m 0s"
        assert cli_output.format_duration(65000) == "1m 5s"
        assert cli_output.format_duration(125000) == "2m 5s"

    def test_format_duration_long_duration(self):
        """Test format_duration for very long durations."""
        assert cli_output.format_duration(3600000) == "60m 0s"
        assert cli_output.format_duration(3665000) == "61m 5s"

    def test_format_duration_fractional_milliseconds(self):
        """Test format_duration with fractional milliseconds."""
        assert cli_output.format_duration(123.456) == "123ms"

    def test_format_duration_fractional_seconds(self):
        """Test format_duration with fractional seconds."""
        result = cli_output.format_duration(1234.5)
        assert result == "1.2s"


class TestSizeFormatting:
    """Test file size formatting function."""

    def test_format_size_bytes(self):
        """Test format_size for values under 1 KB."""
        assert cli_output.format_size(0) == "0.0 B"
        assert cli_output.format_size(500) == "500.0 B"
        assert cli_output.format_size(1023) == "1023.0 B"

    def test_format_size_kilobytes(self):
        """Test format_size for values under 1 MB."""
        assert cli_output.format_size(1024) == "1.0 KB"
        assert cli_output.format_size(5120) == "5.0 KB"
        assert cli_output.format_size(1048575) == "1024.0 KB"

    def test_format_size_megabytes(self):
        """Test format_size for values under 1 GB."""
        assert cli_output.format_size(1048576) == "1.0 MB"
        assert cli_output.format_size(5242880) == "5.0 MB"
        assert cli_output.format_size(1073741823) == "1024.0 MB"

    def test_format_size_gigabytes(self):
        """Test format_size for values under 1 TB."""
        assert cli_output.format_size(1073741824) == "1.0 GB"
        assert cli_output.format_size(5368709120) == "5.0 GB"
        assert cli_output.format_size(1099511627775) == "1024.0 GB"

    def test_format_size_terabytes(self):
        """Test format_size for very large values."""
        assert cli_output.format_size(1099511627776) == "1.0 TB"
        assert cli_output.format_size(5497558138880) == "5.0 TB"

    def test_format_size_precision(self):
        """Test format_size precision."""
        # 1.5 KB
        assert cli_output.format_size(1536) == "1.5 KB"
        # 2.7 MB
        result = cli_output.format_size(2831155)
        assert result.startswith("2.7")


class TestHeaderAndRule:
    """Test header and rule functions."""

    @patch.object(cli_output.console, "print")
    def test_print_header(self, mock_print):
        """Test print_header function."""
        cli_output.print_header("Test Header")
        # Should be called 3 times (top line, text, bottom line)
        assert mock_print.call_count == 3
        # Check that header text is centered
        calls = mock_print.call_args_list
        middle_call = calls[1][0][0]
        assert "Test Header" in middle_call

    @patch.object(cli_output.console, "print")
    def test_print_header_short_text(self, mock_print):
        """Test print_header with short text."""
        cli_output.print_header("Hi")
        assert mock_print.call_count == 3

    @patch.object(cli_output.console, "print")
    def test_print_header_long_text(self, mock_print):
        """Test print_header with long text."""
        long_text = "A" * 100
        cli_output.print_header(long_text)
        assert mock_print.call_count == 3

    @patch.object(cli_output.console, "print")
    def test_print_rule_no_title(self, mock_print):
        """Test print_rule without title."""
        cli_output.print_rule()
        mock_print.assert_called_once()
        from rich.rule import Rule

        rule_obj = mock_print.call_args[0][0]
        assert isinstance(rule_obj, Rule)

    @patch.object(cli_output.console, "print")
    def test_print_rule_with_title(self, mock_print):
        """Test print_rule with title."""
        cli_output.print_rule(title="Section")
        mock_print.assert_called_once()

    @patch.object(cli_output.console, "print")
    def test_print_rule_custom_style(self, mock_print):
        """Test print_rule with custom style."""
        cli_output.print_rule(title="Test", style="red")
        mock_print.assert_called_once()


class TestConsoleInstance:
    """Test console instance and integration."""

    def test_console_is_console(self):
        """Test that console is a Console instance."""
        assert isinstance(cli_output.console, Console)

    def test_console_singleton(self):
        """Test that console is used consistently."""
        # Import in different ways should give same instance
        from memdocs.cli_output import console

        assert console is cli_output.console


class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch.object(cli_output.console, "print")
    def test_unicode_in_messages(self, mock_print):
        """Test handling of unicode characters."""
        cli_output.success("Test with emoji 🎉 and unicode ñ ü")
        mock_print.assert_called_once()

    @patch.object(cli_output.console, "print")
    def test_newlines_in_panel(self, mock_print):
        """Test panel with newlines in content."""
        cli_output.panel("Line 1\nLine 2\nLine 3")
        mock_print.assert_called_once()

    def test_progress_bar_zero_total(self):
        """Test progress bar with zero total."""
        with cli_output.progress_bar("Test") as progress:
            task = progress.add_task("Task", total=0)
            # Should not crash
            assert task is not None

    def test_create_file_tree_dot_files(self):
        """Test create_file_tree with dot files."""
        files = [Path(".gitignore"), Path(".env"), Path("src/.hidden")]
        tree = cli_output.create_file_tree(Path("/root"), files)
        assert isinstance(tree, Tree)

    def test_format_duration_negative(self):
        """Test format_duration with negative value."""
        # Should still work, just show negative
        result = cli_output.format_duration(-1000)
        assert "-" in result

    def test_format_size_negative(self):
        """Test format_size with negative value."""
        # Should handle negative values
        result = cli_output.format_size(-1024)
        assert "-" in result


class TestIntegration:
    """Integration tests for combined functionality."""

    @patch.object(cli_output.console, "print")
    def test_full_workflow_output(self, mock_print):
        """Test a realistic output workflow."""
        # Start with header
        cli_output.print_header("Build Process")

        # Show steps
        cli_output.step("Analyzing files")
        cli_output.info("Found 10 files")

        # Show progress (simplified)
        with cli_output.progress_bar("Processing") as progress:
            task = progress.add_task("Files", total=10)
            progress.update(task, advance=10)

        # Show results
        cli_output.success("Build complete")

        # Show summary
        cli_output.print_summary(
            "Results",
            {
                "Files": 10,
                "Duration": "5.2s",
                "Size": "1.5 MB",
            },
        )

        # Should have made multiple print calls
        assert mock_print.call_count > 0

    def test_table_with_data(self):
        """Test creating and populating a table."""
        table = cli_output.create_table(title="Test Results", show_lines=True)
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        table.add_column("Time", justify="right")

        table.add_row("test_example", "PASS", "0.5s")
        table.add_row("test_another", "PASS", "1.2s")

        assert isinstance(table, Table)

    def test_file_tree_realistic_structure(self):
        """Test file tree with realistic project structure."""
        files = [
            Path("README.md"),
            Path("setup.py"),
            Path("src/__init__.py"),
            Path("src/main.py"),
            Path("src/utils.py"),
            Path("tests/__init__.py"),
            Path("tests/test_main.py"),
            Path("tests/test_utils.py"),
        ]
        tree = cli_output.create_file_tree(Path("/project"), files, title="Project Files")
        assert isinstance(tree, Tree)

    @patch.object(cli_output, "panel")
    def test_nested_formatting_calls(self, mock_panel):
        """Test nested formatting with panel containing formatted text."""
        content_lines = []
        content_lines.append(f"Duration: {cli_output.format_duration(5500)}")
        content_lines.append(f"Size: {cli_output.format_size(1536)}")
        content = "\n".join(content_lines)

        cli_output.panel(content, title="Stats", style="blue")
        mock_panel.assert_called_once()
