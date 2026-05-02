import pytest
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.cli.calculator_cli import CalculatorCLI

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
            cli.run_command("invalid_op", 3, 5)

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
        with patch("builtins.input", side_effect=["6"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "6"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "6"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "6"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["5", "6"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = [
            CalculationResult("add", 1, 2, 3, _TS),
        ]
        with patch("builtins.input", side_effect=["5", "6"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out


class TestRunCommandNewOperations:
    """Test CLI run_command with new mathematical operations."""

    def test_square_prints_result(self, capsys):
        """Test square operation via CLI command."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 5, 0, 25, _TS)
        cli.run_command("square", 5, 0)
        captured = capsys.readouterr()
        assert "25" in captured.out

    def test_sqrt_prints_result(self, capsys):
        """Test sqrt operation via CLI command."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 16, 0, 4, _TS)
        cli.run_command("sqrt", 16, 0)
        captured = capsys.readouterr()
        assert "4" in captured.out

    def test_power_prints_result(self, capsys):
        """Test power operation via CLI command."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 3, 8, _TS)
        cli.run_command("power", 2, 3)
        captured = capsys.readouterr()
        assert "8" in captured.out

    def test_modulo_prints_result(self, capsys):
        """Test modulo operation via CLI command."""
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS)
        cli.run_command("modulo", 10, 3)
        captured = capsys.readouterr()
        assert "1" in captured.out

    def test_sqrt_negative_error_exits(self):
        """Test sqrt with negative number exits with error."""
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Cannot take square root of negative number")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -5, 0)

    def test_sqrt_negative_error_goes_to_stderr(self, capsys):
        """Test sqrt negative error message goes to stderr."""
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Cannot take square root of negative number")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -5, 0)
        assert "Cannot take square root" in capsys.readouterr().err

    def test_modulo_by_zero_error_exits(self):
        """Test modulo by zero exits with error."""
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)

    def test_modulo_by_zero_error_goes_to_stderr(self, capsys):
        """Test modulo by zero error message goes to stderr."""
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("modulo", 10, 0)
        assert "Modulo by zero" in capsys.readouterr().err
