import pytest
from unittest.mock import MagicMock, patch
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.cli.calculator_cli import CalculatorCLI

_TS = "2026-01-01T00:00:00"


def _make_cli():
    service = MagicMock()
    return CalculatorCLI(service), service


class TestRunCommand:
    def test_prints_result(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, execution_time_ms=0, timestamp=_TS)
        cli.run_command("add", 3, 5)
        assert "8" in capsys.readouterr().out

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

    def test_square_via_command(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 5, 0, 25, execution_time_ms=0, timestamp=_TS)
        cli.run_command("square", 5, 0)
        assert "25" in capsys.readouterr().out

    def test_sqrt_via_command(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 16, 0, 4.0, execution_time_ms=0, timestamp=_TS)
        cli.run_command("sqrt", 16, 0)
        assert "4" in capsys.readouterr().out

    def test_power_via_command(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 3, 8, execution_time_ms=0, timestamp=_TS)
        cli.run_command("power", 2, 3)
        assert "8" in capsys.readouterr().out

    def test_modulo_via_command(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, execution_time_ms=0, timestamp=_TS)
        cli.run_command("modulo", 10, 3)
        assert "1" in capsys.readouterr().out

    def test_sqrt_negative_exits(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative number")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -1, 0)
        assert "Square root of negative number" in capsys.readouterr().err

    def test_modulo_by_zero_exits(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero")
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 5, 0)
        assert "Modulo by zero" in capsys.readouterr().err

    def test_menu_includes_new_operations(self):
        cli, _ = _make_cli()
        menu_operations = [op for op, _ in cli._MENU]
        assert Operation.SQUARE in menu_operations
        assert Operation.SQRT in menu_operations
        assert Operation.POWER in menu_operations
        assert Operation.MODULO in menu_operations


class TestRunInteractive:
    def test_exit_choice(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["10"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, execution_time_ms=0, timestamp=_TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "10"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "10"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "10"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["9", "10"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = [
            CalculationResult("add", 1, 2, 3, execution_time_ms=0, timestamp=_TS),
        ]
        with patch("builtins.input", side_effect=["9", "10"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out
