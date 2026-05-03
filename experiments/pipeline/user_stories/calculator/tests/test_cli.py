import pytest
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.models.memory_entry import MemoryEntry
from src.cli.calculator_cli import CalculatorCLI

_TS = "2026-01-01T00:00:00"


def _make_cli():
    service = MagicMock()
    stats_service = MagicMock()
    import_export_service = MagicMock()
    return CalculatorCLI(service, stats_service, import_export_service), service


class TestRunCommand:
    def test_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("add", 3, 5, 8, None, None, _TS)
        cli.run_command("add", 3, 5)
        assert "8" in capsys.readouterr().out

    def test_invalid_operation_exits(self):
        cli, _ = _make_cli()
        with pytest.raises(SystemExit):
            cli.run_command("invalid_op", 3, 5)

    def test_service_error_exits(self):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("divide", 5, 0, None, "Division by zero", "ZeroDivisionError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)

    def test_error_goes_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("divide", 5, 0, None, "Division by zero", "ZeroDivisionError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)
        assert "Division by zero" in capsys.readouterr().err

    # ====== Square Command Tests ======
    def test_square_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("square", 5, 0, 25, None, None, _TS)
        cli.run_command("square", 5, 0)
        assert "25" in capsys.readouterr().out

    def test_square_negative_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("square", -3, 0, 9, None, None, _TS)
        cli.run_command("square", -3, 0)
        assert "9" in capsys.readouterr().out

    # ====== Square Root Command Tests ======
    def test_sqrt_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("sqrt", 16, 0, 4, None, None, _TS)
        cli.run_command("sqrt", 16, 0)
        assert "4" in capsys.readouterr().out

    def test_sqrt_negative_error_exits(self):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("sqrt", -1, 0, None, "Cannot take square root of negative number", "ValueError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -1, 0)

    def test_sqrt_negative_error_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("sqrt", -5, 0, None, "Cannot take square root of negative number", "ValueError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -5, 0)
        assert "Cannot take square root of negative number" in capsys.readouterr().err

    # ====== Power Command Tests ======
    def test_power_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("power", 2, 5, 32, None, None, _TS)
        cli.run_command("power", 2, 5)
        assert "32" in capsys.readouterr().out

    def test_power_negative_exponent_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("power", 2, -1, 0.5, None, None, _TS)
        cli.run_command("power", 2, -1)
        assert "0.5" in capsys.readouterr().out

    # ====== Modulo Command Tests ======
    def test_modulo_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("modulo", 10, 3, 1, None, None, _TS)
        cli.run_command("modulo", 10, 3)
        assert "1" in capsys.readouterr().out

    def test_modulo_by_zero_error_exits(self):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("modulo", 10, 0, None, "Modulo by zero is not allowed", "ZeroDivisionError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)

    def test_modulo_by_zero_error_to_stderr(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("modulo", 10, 0, None, "Modulo by zero is not allowed", "ZeroDivisionError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)
        assert "Modulo by zero is not allowed" in capsys.readouterr().err


class TestRunInteractive:
    def test_exit_choice(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["14"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("add", 3, 5, 8, None, None, _TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "14"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "14"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "14"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["9", "14"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = [
            MemoryEntry("add", 1, 2, 3, None, None, _TS),
        ]
        with patch("builtins.input", side_effect=["9", "14"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out

    # ====== Interactive Square Tests ======
    def test_square_operation_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("square", 5, 0, 25, None, None, _TS)
        with patch("builtins.input", side_effect=["5", "5", "0", "14"]):
            cli.run_interactive()
        assert "25" in capsys.readouterr().out

    # ====== Interactive Square Root Tests ======
    def test_sqrt_operation_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("sqrt", 16, 0, 4, None, None, _TS)
        with patch("builtins.input", side_effect=["6", "16", "0", "14"]):
            cli.run_interactive()
        assert "4" in capsys.readouterr().out

    def test_sqrt_negative_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("sqrt", -1, 0, None, "Cannot take square root of negative number", "ValueError", _TS)
        with patch("builtins.input", side_effect=["6", "-1", "0", "14"]):
            cli.run_interactive()
        assert "Cannot take square root of negative number" in capsys.readouterr().out

    # ====== Interactive Power Tests ======
    def test_power_operation_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("power", 2, 5, 32, None, None, _TS)
        with patch("builtins.input", side_effect=["7", "2", "5", "14"]):
            cli.run_interactive()
        assert "32" in capsys.readouterr().out

    # ====== Interactive Modulo Tests ======
    def test_modulo_operation_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("modulo", 10, 3, 1, None, None, _TS)
        with patch("builtins.input", side_effect=["8", "10", "3", "14"]):
            cli.run_interactive()
        assert "1" in capsys.readouterr().out

    def test_modulo_by_zero_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = MemoryEntry("modulo", 10, 0, None, "Modulo by zero is not allowed", "ZeroDivisionError", _TS)
        with patch("builtins.input", side_effect=["8", "10", "0", "14"]):
            cli.run_interactive()
        assert "Modulo by zero is not allowed" in capsys.readouterr().out
