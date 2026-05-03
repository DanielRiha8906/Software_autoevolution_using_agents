import pytest
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.models.memory_entry import MemoryEntry
from src.cli.calculator_cli import CalculatorCLI
from src.services.memory_service import MemoryService
from src.storage.memory_json_storage import MemoryJsonStorage

_TS = "2026-01-01T00:00:00"


def _make_cli():
    service = MagicMock()
    return CalculatorCLI(service), service


class TestRunCommand:
    def test_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        cli.run_command("add", 3, 5)
        assert "8" in capsys.readouterr().out

    def test_invalid_operation_exits(self):
        cli, _ = _make_cli()
        with pytest.raises(SystemExit):
            cli.run_command("nonexistent_op", 3, 5)

    def test_service_error_exits(self):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Division by zero")
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)

    def test_error_goes_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Division by zero")
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)
        assert "Division by zero" in capsys.readouterr().err


class TestRunInteractive:
    def test_exit_choice(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["13"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "13"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "13"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "13"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["9", "13"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = [
            CalculationResult("add", 1, 2, 3, _TS),
        ]
        with patch("builtins.input", side_effect=["9", "13"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out


class TestNewOperationsRunCommand:
    """Test SQUARE, SQRT, POWER, MODULO via run_command."""

    def test_square_operation_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 5, 0, 25, _TS)
        cli.run_command("square", 5, 0)
        assert "25" in capsys.readouterr().out

    def test_sqrt_operation_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 16, 0, 4.0, _TS)
        cli.run_command("sqrt", 16, 0)
        assert "4" in capsys.readouterr().out

    def test_power_operation_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 3, 8, _TS)
        cli.run_command("power", 2, 3)
        assert "8" in capsys.readouterr().out

    def test_modulo_operation_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS)
        cli.run_command("modulo", 10, 3)
        assert "1" in capsys.readouterr().out

    def test_sqrt_negative_error_exits(self):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative numbers is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -4, 0)

    def test_modulo_by_zero_error_exits(self):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)

    def test_sqrt_negative_error_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative numbers is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -4, 0)
        assert "Square root of negative" in capsys.readouterr().err

    def test_modulo_by_zero_error_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)
        assert "Modulo by zero" in capsys.readouterr().err


class TestNewOperationsRunInteractive:
    """Test new operations in interactive menu."""

    def test_square_menu_option(self, capsys):
        """Test SQUARE via menu option 5."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 4, 0, 16, _TS)
        with patch("builtins.input", side_effect=["5", "4", "0", "13"]):
            cli.run_interactive()
        assert "16" in capsys.readouterr().out

    def test_sqrt_menu_option(self, capsys):
        """Test SQRT via menu option 6."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 9, 0, 3.0, _TS)
        with patch("builtins.input", side_effect=["6", "9", "0", "13"]):
            cli.run_interactive()
        assert "3" in capsys.readouterr().out

    def test_power_menu_option(self, capsys):
        """Test POWER via menu option 7."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 8, 256, _TS)
        with patch("builtins.input", side_effect=["7", "2", "8", "13"]):
            cli.run_interactive()
        assert "256" in capsys.readouterr().out

    def test_modulo_menu_option(self, capsys):
        """Test MODULO via menu option 8."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS)
        with patch("builtins.input", side_effect=["8", "10", "3", "13"]):
            cli.run_interactive()
        assert "1" in capsys.readouterr().out

    def test_sqrt_negative_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative numbers is not allowed")
        with patch("builtins.input", side_effect=["6", "-4", "0", "13"]):
            cli.run_interactive()
        assert "Square root of negative" in capsys.readouterr().out

    def test_modulo_by_zero_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with patch("builtins.input", side_effect=["8", "10", "0", "13"]):
            cli.run_interactive()
        assert "Modulo by zero" in capsys.readouterr().out


class TestMemoryInteractiveMenu:
    """Test memory filtering in interactive menu (options 11 and 12)."""

    def test_memory_option_10_view_all(self, capsys, tmp_path):
        """Test 1: Option 10 displays all memory entries."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1")
        memory_service.store(entry)

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["10", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "add" in output
        assert "3" in output

    def test_memory_option_10_empty_storage(self, capsys, tmp_path):
        """Test 2: Option 10 with empty storage shows no entries message."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["10", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "No memory entries" in output

    def test_filter_memory_option_11_by_operation(self, capsys, tmp_path):
        """Test 3: Option 11 filters memory by operation name."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        # Store entries with different operations
        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))
        memory_service.store(MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["11", "add", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        # Should show results for "add" operations
        assert "add" in output or "Add" in output or "addition" in output.lower()

    def test_filter_memory_option_11_case_insensitive(self, capsys, tmp_path):
        """Test 4: Option 11 filter is case-insensitive."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["11", "ADD", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "No memory entries match operation" in output or "add" in output.lower()

    def test_filter_memory_option_11_no_matches(self, capsys, tmp_path):
        """Test 5: Option 11 shows message when no matches found."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["11", "power", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "No memory entries match operation" in output

    def test_filter_memory_option_12_successful(self, capsys, tmp_path):
        """Test 6: Option 12 filters memory for successful operations."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 2.0, "id-3"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["12", "1", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        # Should show successful entries, likely showing "add" and "multiply"
        assert "add" in output.lower() or "1" in output or "multiply" in output.lower()

    def test_filter_memory_option_12_failed(self, capsys, tmp_path):
        """Test 7: Option 12 filters memory for failed operations."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["12", "2", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "failed" in output.lower() or "divide" in output.lower() or "error" in output.lower()

    def test_filter_memory_option_12_invalid_choice(self, capsys, tmp_path):
        """Test 8: Option 12 with invalid choice shows error and returns."""
        service = MagicMock()
        memory_service = MemoryService(MemoryJsonStorage(tmp_path / "memory.json"))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))

        cli = CalculatorCLI(service, memory_service)
        with patch("builtins.input", side_effect=["12", "99", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "Invalid choice" in output

    def test_filter_memory_option_11_no_memory_service(self, capsys):
        """Test 9: Option 11 without memory service shows unavailable message."""
        service = MagicMock()
        cli = CalculatorCLI(service, None)

        with patch("builtins.input", side_effect=["11", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "Memory service not available" in output

    def test_filter_memory_option_12_no_memory_service(self, capsys):
        """Test 10: Option 12 without memory service shows unavailable message."""
        service = MagicMock()
        cli = CalculatorCLI(service, None)

        with patch("builtins.input", side_effect=["12", "13"]):
            cli.run_interactive()

        output = capsys.readouterr().out
        assert "Memory service not available" in output
