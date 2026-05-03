import pytest
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.models.memory_entry import ResultEntry, ErrorEntry
from src.cli.calculator_cli import CalculatorCLI

_TS = "2026-01-01T00:00:00"


def _make_cli():
    service = MagicMock()
    memory_service = MagicMock()
    return CalculatorCLI(service, memory_service), service, memory_service


class TestRunCommand:
    def test_prints_result(self, capsys):
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        cli.run_command("add", 3, 5)
        assert "8" in capsys.readouterr().out

    def test_invalid_operation_exits(self):
        cli, _, _ = _make_cli()
        with pytest.raises(SystemExit):
            cli.run_command("invalid_op", 3, 5)

    def test_service_error_exits(self):
        cli, service, _ = _make_cli()
        service.perform.side_effect = ValueError("Division by zero")
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)

    def test_error_goes_to_stderr(self, capsys):
        cli, service, _ = _make_cli()
        service.perform.side_effect = ValueError("Division by zero")
        with pytest.raises(SystemExit):
            cli.run_command("divide", 5, 0)
        assert "Division by zero" in capsys.readouterr().err


class TestRunInteractive:
    def test_exit_choice(self, capsys):
        cli, _, _ = _make_cli()
        with patch("builtins.input", side_effect=["15"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "15"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "15"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "15"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service, _ = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["10", "15"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service, _ = _make_cli()
        service.get_history.return_value = [
            CalculationResult("add", 1, 2, 3, _TS),
        ]
        with patch("builtins.input", side_effect=["10", "15"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out


class TestMemoryServiceCommands:
    def test_memory_retrieve_empty(self, capsys):
        cli, _, memory_service = _make_cli()
        memory_service.retrieve.return_value = []
        cli.memory_retrieve_command()
        assert "No memory entries" in capsys.readouterr().out

    def test_memory_retrieve_shows_entries(self, capsys):
        cli, _, memory_service = _make_cli()
        memory_service.retrieve.return_value = [
            ResultEntry(operation="add", operands=[1, 2], result=3),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero"),
        ]
        cli.memory_retrieve_command()
        output = capsys.readouterr().out
        assert "Retrieved 2 memory entries" in output
        assert "add" in output
        assert "divide" in output

    def test_memory_store_result_entry(self, capsys):
        cli, _, memory_service = _make_cli()
        cli.memory_store_command("add", [1, 2], result=3)
        memory_service.store.assert_called_once()
        stored_entry = memory_service.store.call_args[0][0]
        assert isinstance(stored_entry, ResultEntry)
        assert stored_entry.operation == "add"
        assert stored_entry.operands == [1, 2]
        assert stored_entry.result == 3

    def test_memory_store_error_entry(self, capsys):
        cli, _, memory_service = _make_cli()
        cli.memory_store_command("divide", [5, 0], error="Division by zero is not allowed")
        memory_service.store.assert_called_once()
        stored_entry = memory_service.store.call_args[0][0]
        assert isinstance(stored_entry, ErrorEntry)
        assert stored_entry.operation == "divide"
        assert stored_entry.operands == [5, 0]
        assert stored_entry.error_message == "Division by zero is not allowed"

    def test_memory_store_result_required(self, capsys):
        cli, _, _ = _make_cli()
        with pytest.raises(SystemExit):
            cli.memory_store_command("add", [1, 2], result=None, error=None)
        assert "result required" in capsys.readouterr().err
