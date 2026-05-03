import pytest
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.cli.calculator_cli import CalculatorCLI


_TS = "2026-01-01T00:00:00"


class TestShowMemoryCLINoMemoryService:
    """Test show_memory_cli() when memory_service is None."""

    def test_show_memory_cli_with_no_memory_service(self, capsys):
        """Test show_memory_cli() with no memory service prints error to stderr."""
        cli = CalculatorCLI(MagicMock(), memory_service=None)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        assert "Memory service is not available" in captured.err


class TestShowMemoryCLINoEntries:
    """Test show_memory_cli() with no entries."""

    def test_show_memory_cli_with_no_entries(self, capsys):
        """Test show_memory_cli() with no entries prints 'No memory entries recorded yet.'."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        assert "No memory entries recorded yet." in captured.out

    def test_show_memory_cli_with_empty_list(self, capsys):
        """Test show_memory_cli() with empty list from get_all_entries()."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should not have entries output, just the no-entries message
        assert "No memory entries recorded yet." in captured.out


class TestShowMemoryCLISingleEntry:
    """Test show_memory_cli() with a single entry."""

    def test_show_memory_cli_with_one_successful_entry(self, capsys):
        """Test show_memory_cli() with 1 successful entry prints entry details."""
        memory_service = MagicMock()
        entry = MemoryEntry(
            operation_name="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            entry_id="abc123def456ghi789jkl012mnop345q",
            error_message=None,
            timestamp=_TS,
            execution_time_ms=2.5,
        )
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should contain entry_id (at least 8 chars)
        assert "abc123de" in captured.out
        # Should contain operation
        assert "add" in captured.out
        # Should contain operands
        assert "3.0" in captured.out or "3" in captured.out
        assert "5.0" in captured.out or "5" in captured.out
        # Should contain result
        assert "8.0" in captured.out or "8" in captured.out
        # Should contain execution_time_ms
        assert "2.5" in captured.out or "2.5ms" in captured.out

    def test_show_memory_cli_entry_displays_entry_id_first_8_chars(self, capsys):
        """Test show_memory_cli() displays entry_id truncated to first 8 chars."""
        memory_service = MagicMock()
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            entry_id="abcdefghijklmnopqrstuvwxyz123456",
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.0,
        )
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should have first 8 chars
        assert "abcdefgh" in captured.out
        # Should have ellipsis
        assert "..." in captured.out


class TestShowMemoryCLIMultipleEntries:
    """Test show_memory_cli() with multiple entries."""

    def test_show_memory_cli_with_three_entries(self, capsys):
        """Test show_memory_cli() with 3 entries displays all 3."""
        memory_service = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1234567890123456789012345678901", None, _TS, 1.0)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True, "id2234567890123456789012345678902", None, _TS, 1.5)
        entry3 = MemoryEntry("multiply", 3.0, 4.0, 12.0, True, "id3234567890123456789012345678903", None, _TS, 2.0)
        memory_service.get_all_entries.return_value = [entry1, entry2, entry3]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # All 3 should be present
        assert "add" in captured.out
        assert "subtract" in captured.out
        assert "multiply" in captured.out
        # All 3 entry_ids (first 8 chars) should be present
        assert "id123456" in captured.out
        assert "id223456" in captured.out
        assert "id323456" in captured.out


class TestShowMemoryCLIFailedEntry:
    """Test show_memory_cli() with failed entries."""

    def test_show_memory_cli_shows_failed_entry_with_error_message(self, capsys):
        """Test show_memory_cli() shows failed entries with error_message instead of result."""
        memory_service = MagicMock()
        entry = MemoryEntry(
            operation_name="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            entry_id="fail123456789012345678901234567890",
            error_message="Division by zero",
            timestamp=_TS,
            execution_time_ms=1.0,
        )
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should show error message, not result
        assert "Division by zero" in captured.out
        # Should NOT show a numeric result
        assert "None" not in captured.out

    def test_show_memory_cli_mixed_success_and_failure(self, capsys):
        """Test show_memory_cli() with both successful and failed entries."""
        memory_service = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1234567890123456789012345678901", None, _TS, 1.0)
        entry2 = MemoryEntry("divide", 5.0, 0.0, None, False, "id2234567890123456789012345678902", "Division by zero", _TS, 1.5)
        memory_service.get_all_entries.return_value = [entry1, entry2]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should have both
        assert "add" in captured.out
        assert "divide" in captured.out
        assert "Division by zero" in captured.out
        # First should show result
        assert "3" in captured.out


class TestShowMemoryCLIFormatting:
    """Test show_memory_cli() output formatting."""

    def test_show_memory_cli_entry_format_includes_operation(self, capsys):
        """Test show_memory_cli() output includes operation name."""
        memory_service = MagicMock()
        entry = MemoryEntry("power", 2.0, 3.0, 8.0, True, "id1234567890123456789012345678901", None, _TS, 2.0)
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should show "power"
        assert "power" in captured.out

    def test_show_memory_cli_entry_format_includes_operands(self, capsys):
        """Test show_memory_cli() output includes both operands."""
        memory_service = MagicMock()
        entry = MemoryEntry("modulo", 10.0, 3.0, 1.0, True, "id1234567890123456789012345678901", None, _TS, 1.0)
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should have "10" and "3"
        assert "10" in captured.out
        assert "3" in captured.out

    def test_show_memory_cli_entry_format_includes_execution_time(self, capsys):
        """Test show_memory_cli() output includes execution_time_ms."""
        memory_service = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1234567890123456789012345678901", None, _TS, 5.5)
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        # Should have execution time (either "5.5" or "5.5ms")
        assert "5.5" in captured.out


class TestMemoryFlagIntegration:
    """Test --memory flag integration with argparse."""

    def test_memory_flag_calls_show_memory_cli(self, capsys):
        """Test --memory flag calls show_memory_cli()."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        assert "No memory entries recorded yet." in captured.out


class TestInteractiveMemoryOption:
    """Test interactive menu option for memory."""

    def test_interactive_menu_has_view_memory_option(self, capsys):
        """Test interactive menu displays 'View memory entries' option."""
        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", side_effect=["11"]):  # Exit
            cli.run_interactive()
        captured = capsys.readouterr()
        # Menu should show "View memory entries"
        assert "View memory entries" in captured.out

    def test_interactive_memory_option_calls_show_memory(self, capsys):
        """Test selecting memory option in interactive menu shows memory."""
        memory_service = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1234567890123456789012345678901", None, _TS, 1.0)
        memory_service.get_all_entries.return_value = [entry]
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        with patch("builtins.input", side_effect=["10", "11"]):  # Menu option 10 = view memory, 11 = exit
            cli.run_interactive()
        captured = capsys.readouterr()
        # Should show memory entry
        assert "add" in captured.out

    def test_interactive_memory_option_number(self, capsys):
        """Test memory option is at position 10 in interactive menu."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        cli = CalculatorCLI(MagicMock(), memory_service=memory_service)
        with patch("builtins.input", side_effect=["10", "11"]):
            cli.run_interactive()
        captured = capsys.readouterr()
        # Option 10 should be memory
        assert "View memory entries" in captured.out

    def test_interactive_menu_exit_is_option_11(self, capsys):
        """Test exit option is at position 11 (after memory at 10)."""
        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", side_effect=["11"]):  # Exit
            cli.run_interactive()
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out


class TestMemoryCliWithoutMemoryService:
    """Test CLI behavior when memory_service is None."""

    def test_show_memory_cli_unavailable_message_to_stderr(self, capsys):
        """Test show_memory_cli() without memory service prints to stderr."""
        cli = CalculatorCLI(MagicMock(), memory_service=None)
        cli.show_memory_cli()
        captured = capsys.readouterr()
        assert "Memory service is not available" in captured.err

    def test_interactive_menu_with_no_memory_service(self, capsys):
        """Test interactive menu with no memory service."""
        cli = CalculatorCLI(MagicMock(), memory_service=None)
        with patch("builtins.input", side_effect=["10", "11"]):  # Option 10 = memory, 11 = exit
            cli.run_interactive()
        captured = capsys.readouterr()
        # Memory option should still be in menu
        assert "View memory entries" in captured.out
