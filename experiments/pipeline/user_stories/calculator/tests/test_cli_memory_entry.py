import pytest
from unittest.mock import MagicMock, patch
from src.models.operation import Operation
from src.models.memory_entry import MemoryEntry
from src.cli.calculator_cli import CalculatorCLI

_TS = "2026-05-03T14:30:00"
_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _make_cli():
    service = MagicMock()
    stats_service = MagicMock()
    return CalculatorCLI(service, stats_service), service


class TestRunCommandWithMemoryEntry:
    """Test run_command with MemoryEntry results."""

    def test_prints_successful_result(self, capsys):
        """Successful result is printed."""
        cli, service = _make_cli()
        entry = MemoryEntry("add", 3, 5, 8, None, None, timestamp=_TS, uuid=_UUID)
        service.perform.return_value = entry
        cli.run_command("add", 3, 5)
        assert "8" in capsys.readouterr().out

    def test_successful_result_no_exit(self, capsys):
        """Successful result does not exit."""
        cli, service = _make_cli()
        entry = MemoryEntry("add", 3, 5, 8, None, None, timestamp=_TS, uuid=_UUID)
        service.perform.return_value = entry
        cli.run_command("add", 3, 5)
        # No SystemExit should be raised

    def test_error_result_exits(self):
        """Error result causes exit."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "divide", 5, 0, None, "Division by zero is not allowed", "ValueError", timestamp=_TS, uuid=_UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)

    def test_error_result_prints_to_stderr(self, capsys):
        """Error message is printed to stderr."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "divide", 5, 0, None, "Division by zero is not allowed", "ValueError", timestamp=_TS, uuid=_UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)
        assert "Division by zero is not allowed" in capsys.readouterr().err

    def test_error_result_uses_error_field(self, capsys):
        """Uses error field from MemoryEntry, not exception."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "sqrt", -1, 0, None, "Cannot take square root of negative number", "ValueError", _TS, _UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -1, 0)
        output = capsys.readouterr()
        assert "Cannot take square root of negative number" in output.err

    def test_divide_by_zero_error_handling(self, capsys):
        """Specific error handling for division by zero."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "divide", 10, 0, None, "Division by zero is not allowed", "ValueError", _TS, _UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("divide", 10, 0)
        assert "Division by zero" in capsys.readouterr().err

    def test_sqrt_negative_error_handling(self, capsys):
        """Specific error handling for negative sqrt."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "sqrt", -5, 0, None, "Cannot take square root of negative number", "ValueError", _TS, _UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -5, 0)
        assert "Cannot take square root of negative number" in capsys.readouterr().err

    def test_modulo_by_zero_error_handling(self, capsys):
        """Specific error handling for modulo by zero."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "modulo", 10, 0, None, "Modulo by zero is not allowed", "ValueError", _TS, _UUID
        )
        service.perform.return_value = entry
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)
        assert "Modulo by zero" in capsys.readouterr().err

    def test_multiple_operations_success(self, capsys):
        """Multiple successful operations."""
        cli, service = _make_cli()

        # Add
        entry1 = MemoryEntry("add", 1, 2, 3, None, None, timestamp=_TS, uuid="uuid1")
        service.perform.return_value = entry1
        cli.run_command("add", 1, 2)
        assert "3" in capsys.readouterr().out

        # Multiply
        capsys.readouterr()  # Clear output
        entry2 = MemoryEntry("multiply", 3, 4, 12, None, None, timestamp=_TS, uuid="uuid2")
        service.perform.return_value = entry2
        cli.run_command("multiply", 3, 4)
        assert "12" in capsys.readouterr().out

    def test_invalid_operation_still_exits(self):
        """Invalid operation exits (doesn't depend on MemoryEntry)."""
        cli, _ = _make_cli()
        with pytest.raises(SystemExit):
            cli.run_command("invalid_op", 3, 5)

    @pytest.mark.parametrize("op,a,b,expected_result", [
        ("add", 1, 2, "3"),
        ("subtract", 5, 3, "2"),
        ("multiply", 4, 5, "20"),
        ("divide", 10, 2, "5"),
        ("square", 5, 0, "25"),
        ("sqrt", 16, 0, "4"),
        ("power", 2, 3, "8"),
        ("modulo", 10, 3, "1"),
    ])
    def test_all_operations_success(self, capsys, op, a, b, expected_result):
        """All operations print results correctly."""
        cli, service = _make_cli()
        entry = MemoryEntry(op, a, b, float(expected_result), None, None, timestamp=_TS, uuid=_UUID)
        service.perform.return_value = entry
        cli.run_command(op, a, b)
        assert expected_result in capsys.readouterr().out


class TestRunInteractiveWithMemoryEntry:
    """Test run_interactive with MemoryEntry results."""

    def test_successful_operation_displayed(self, capsys):
        """Successful operation result is displayed."""
        cli, service = _make_cli()
        entry = MemoryEntry("add", 3, 5, 8, None, None, timestamp=_TS, uuid=_UUID)
        service.perform.return_value = entry
        with patch("builtins.input", side_effect=["1", "3", "5", "12"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        assert "8" in output or "Result" in output

    def test_error_operation_displays_error(self, capsys):
        """Error operation displays error message."""
        cli, service = _make_cli()
        entry = MemoryEntry(
            "divide", 5, 0, None, "Division by zero is not allowed", "ValueError", timestamp=_TS, uuid=_UUID
        )
        service.perform.return_value = entry
        with patch("builtins.input", side_effect=["2", "5", "0", "12"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        assert "Error" in output and "Division by zero" in output

    def test_error_operation_continues_interactive(self, capsys):
        """Error doesn't exit interactive mode."""
        cli, service = _make_cli()
        # First operation: error
        error_entry = MemoryEntry(
            "divide", 5, 0, None, "Division by zero is not allowed", "ValueError", _TS, "uuid1"
        )
        # Second operation: success
        success_entry = MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid2")
        service.perform.side_effect = [error_entry, success_entry]

        with patch("builtins.input", side_effect=["2", "5", "0", "1", "1", "2", "12"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "Division by zero" in output
        assert "3" in output

    def test_history_shows_error_entries(self, capsys):
        """History display shows error entries."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1"),
            MemoryEntry("divide", 5, 0, None, "Division by zero", "ValueError", timestamp=_TS, uuid="uuid2"),
        ]
        service.get_history.return_value = entries
        with patch("builtins.input", side_effect=["9", "12"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        assert "ERROR" in output and "Division by zero" in output

    def test_history_shows_success_entries(self, capsys):
        """History display shows successful entries."""
        cli, service = _make_cli()
        entries = [MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1")]
        service.get_history.return_value = entries
        with patch("builtins.input", side_effect=["9", "12"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        assert "1 + 2 = 3" in output

    def test_mixed_success_and_error_operations(self, capsys):
        """Multiple operations with mix of success and error."""
        cli, service = _make_cli()
        success1 = MemoryEntry("add", 1, 1, 2, None, None, timestamp=_TS, uuid="uuid1")
        error1 = MemoryEntry("sqrt", -1, 0, None, "Cannot take square root", "ValueError", timestamp=_TS, uuid="uuid2")
        success2 = MemoryEntry("multiply", 3, 3, 9, None, None, timestamp=_TS, uuid="uuid3")

        service.perform.side_effect = [success1, error1, success2]

        with patch("builtins.input", side_effect=[
            "1", "1", "1",  # Add
            "6", "-1", "0",  # Sqrt (error)
            "3", "3", "3",  # Multiply
            "12"  # Exit
        ]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "2" in output
        assert "Cannot take square root" in output
        assert "9" in output

    @pytest.mark.parametrize("op_choice,op_name,a,b,result", [
        ("1", "add", 5, 3, 8),
        ("2", "subtract", 5, 3, 2),
        ("3", "multiply", 4, 5, 20),
        ("4", "divide", 10, 2, 5),
        ("5", "square", 5, 0, 25),
        ("6", "sqrt", 16, 0, 4),
        ("7", "power", 2, 3, 8),
        ("8", "modulo", 10, 3, 1),
    ])
    def test_all_interactive_operations(self, capsys, op_choice, op_name, a, b, result):
        """All operations work in interactive mode."""
        cli, service = _make_cli()
        entry = MemoryEntry(op_name, a, b, float(result), None, None, timestamp=_TS, uuid=_UUID)
        service.perform.return_value = entry
        with patch("builtins.input", side_effect=[op_choice, str(a), str(b), "12"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        assert str(result) in output


class TestShowHistoryWithMemoryEntry:
    """Test _show_history with MemoryEntry results."""

    def test_show_history_empty(self, capsys):
        """Empty history message."""
        cli, service = _make_cli()
        service.get_history.return_value = []
        cli._show_history()
        assert "No calculations" in capsys.readouterr().out

    def test_show_history_success(self, capsys):
        """Display successful entries."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, timestamp="2026-05-03T14:30:00", uuid="uuid1"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        assert "1 + 2 = 3" in output
        assert "2026-05-03T14:30:00" in output

    def test_show_history_error(self, capsys):
        """Display error entries."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("divide", 5, 0, None, "Division by zero is not allowed", "ValueError", _TS, "uuid1"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        assert "ERROR" in output
        assert "Division by zero" in output

    def test_show_history_mixed(self, capsys):
        """Display mixed success and error entries."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, timestamp=_TS, uuid="uuid1"),
            MemoryEntry("divide", 5, 0, None, "Division by zero is not allowed", "ValueError", timestamp=_TS, uuid="uuid2"),
            MemoryEntry("multiply", 3, 4, 12, None, None, timestamp=_TS, uuid="uuid3"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        assert "1 + 2 = 3" in output
        assert "ERROR" in output and "Division by zero" in output
        assert "3 × 4 = 12" in output

    def test_show_history_numbered(self, capsys):
        """History entries are numbered."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1"),
            MemoryEntry("subtract", 5, 3, 2, None, None, _TS, "uuid2"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        assert "1." in output
        assert "2." in output

    def test_show_history_error_without_timestamp(self, capsys):
        """Error entries show error info without timestamp."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("sqrt", -5, 0, None, "Cannot take square root of negative number", "ValueError", timestamp=_TS, uuid="uuid1"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        # Error format shows just the error, not timestamp
        assert "ERROR" in output
        assert "Cannot take square root" in output

    def test_show_history_success_with_timestamp(self, capsys):
        """Success entries show timestamp."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, timestamp="2026-05-03T14:30:00", uuid="uuid1"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        assert "2026-05-03T14:30:00" in output

    def test_show_history_multiple_same_operation(self, capsys):
        """Multiple entries of same operation type."""
        cli, service = _make_cli()
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1"),
            MemoryEntry("add", 5, 5, 10, None, None, _TS, "uuid2"),
            MemoryEntry("add", -1, 1, 0, None, None, _TS, "uuid3"),
        ]
        service.get_history.return_value = entries
        cli._show_history()
        output = capsys.readouterr().out
        # Check for the "+" symbol (used for add in display) appears at least 3 times
        assert output.count("+") >= 3
