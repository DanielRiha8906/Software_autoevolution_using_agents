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
        with patch("builtins.input", side_effect=["11"]):
            cli.run_interactive()
        assert "Goodbye" in capsys.readouterr().out

    def test_add_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)
        with patch("builtins.input", side_effect=["1", "3", "5", "11"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_invalid_choice_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["99", "11"]):
            cli.run_interactive()
        assert "Invalid choice" in capsys.readouterr().out

    def test_invalid_number_retries(self, capsys):
        cli, _ = _make_cli()
        with patch("builtins.input", side_effect=["1", "abc", "11"]):
            cli.run_interactive()
        assert "Invalid number" in capsys.readouterr().out

    def test_history_empty(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = []
        with patch("builtins.input", side_effect=["9", "11"]):
            cli.run_interactive()
        assert "No calculations" in capsys.readouterr().out

    def test_history_shows_entries(self, capsys):
        cli, service = _make_cli()
        service.get_history.return_value = [
            CalculationResult("add", 1, 2, 3, _TS),
        ]
        with patch("builtins.input", side_effect=["9", "11"]):
            cli.run_interactive()
        assert "1 + 2 = 3" in capsys.readouterr().out


class TestRunCommandNewOps:
    def test_square_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 5, 0, 25, _TS)
        cli.run_command("square", 5, 0)
        assert "25" in capsys.readouterr().out

    def test_sqrt_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 9, 0, 3.0, _TS)
        cli.run_command("sqrt", 9, 0)
        assert "3" in capsys.readouterr().out

    def test_power_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 3, 8, _TS)
        cli.run_command("power", 2, 3)
        assert "8" in capsys.readouterr().out

    def test_modulo_operation(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS)
        cli.run_command("modulo", 10, 3)
        assert "1" in capsys.readouterr().out

    def test_sqrt_negative_error_exits(self):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative numbers is not allowed")
        with pytest.raises(SystemExit):
            cli.run_command("sqrt", -4, 0)

    def test_power_zero_negative_error_exits(self):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Cannot raise zero to a negative power")
        with pytest.raises(SystemExit):
            cli.run_command("power", 0, -1)


class TestRunInteractiveNewOps:
    def test_square_menu_option(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("square", 5, 0, 25, _TS)
        with patch("builtins.input", side_effect=["5", "5", "0", "11"]):
            cli.run_interactive()
        assert "25" in capsys.readouterr().out

    def test_sqrt_menu_option(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("sqrt", 9, 0, 3.0, _TS)
        with patch("builtins.input", side_effect=["6", "9", "0", "11"]):
            cli.run_interactive()
        assert "3" in capsys.readouterr().out

    def test_power_menu_option(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("power", 2, 3, 8, _TS)
        with patch("builtins.input", side_effect=["7", "2", "3", "11"]):
            cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_modulo_menu_option(self, capsys):
        cli, service = _make_cli()
        service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS)
        with patch("builtins.input", side_effect=["8", "10", "3", "11"]):
            cli.run_interactive()
        assert "1" in capsys.readouterr().out

    def test_sqrt_negative_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Square root of negative numbers is not allowed")
        with patch("builtins.input", side_effect=["6", "-4", "0", "11"]):
            cli.run_interactive()
        assert "Square root of negative numbers is not allowed" in capsys.readouterr().out

    def test_modulo_by_zero_error_in_interactive(self, capsys):
        cli, service = _make_cli()
        service.perform.side_effect = ValueError("Modulo by zero is not allowed")
        with patch("builtins.input", side_effect=["8", "10", "0", "11"]):
            cli.run_interactive()
        assert "Modulo by zero is not allowed" in capsys.readouterr().out


class TestShowFilteredMemoryCli:
    def test_show_filtered_memory_no_memory_service(self, capsys):
        cli = CalculatorCLI(MagicMock(), None)
        cli.show_filtered_memory_cli()
        assert "Memory service is not available" in capsys.readouterr().err

    def test_show_filtered_memory_no_entries(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = []
        cli.show_filtered_memory_cli()
        assert "No matching memory entries" in capsys.readouterr().out

    def test_show_filtered_memory_successful_entry(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry]
        cli.show_filtered_memory_cli()
        output = capsys.readouterr().out
        assert "add" in output
        assert "3.0" in output

    def test_show_filtered_memory_failed_entry(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry]
        cli.show_filtered_memory_cli()
        output = capsys.readouterr().out
        assert "divide" in output
        assert "Division by zero" in output

    def test_show_filtered_memory_with_operation_filter(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry]
        cli.show_filtered_memory_cli(operation_name="add")
        cli.memory_service.filter.assert_called_once_with("add", None)

    def test_show_filtered_memory_with_success_filter(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry]
        cli.show_filtered_memory_cli(success=True)
        cli.memory_service.filter.assert_called_once_with(None, True)

    def test_show_filtered_memory_with_both_filters(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry]
        cli.show_filtered_memory_cli(operation_name="add", success=True)
        cli.memory_service.filter.assert_called_once_with("add", True)

    def test_show_filtered_memory_multiple_entries(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, _ = _make_cli()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("add", 5.0, 3.0, 8.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter.return_value = [entry1, entry2]
        cli.show_filtered_memory_cli()
        output = capsys.readouterr().out
        assert "add" in output
        assert output.count("add") >= 2


class TestFlagIntegration:
    def test_help_includes_filter_operation_flag(self, capsys):
        from src.__main__ import main
        with patch("sys.argv", ["python", "--help"]):
            with pytest.raises(SystemExit):
                main()
        output = capsys.readouterr().out
        assert "--filter-operation" in output

    def test_help_includes_filter_success_flag(self, capsys):
        from src.__main__ import main
        with patch("sys.argv", ["python", "--help"]):
            with pytest.raises(SystemExit):
                main()
        output = capsys.readouterr().out
        assert "--filter-success" in output

    def test_help_includes_filter_error_flag(self, capsys):
        from src.__main__ import main
        with patch("sys.argv", ["python", "--help"]):
            with pytest.raises(SystemExit):
                main()
        output = capsys.readouterr().out
        assert "--filter-error" in output

    def test_filter_success_and_error_mutually_exclusive(self, capsys):
        from src.__main__ import main
        with patch("sys.argv", ["python", "--filter-success", "--filter-error"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2
        assert "Cannot use both --filter-success and --filter-error" in capsys.readouterr().err


class TestMemoryFilterSubmenu:
    def test_show_memory_filter_submenu_view_all(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, service = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.get_all_entries.return_value = [entry]
        with patch("builtins.input", side_effect=["1", "5"]):
            cli._show_memory_filter_submenu()
        output = capsys.readouterr().out
        assert "add" in output

    def test_show_memory_filter_submenu_filter_by_operation(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, service = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter_by_operation.return_value = [entry]
        with patch("builtins.input", side_effect=["2", "add", "5"]):
            cli._show_memory_filter_submenu()
        cli.memory_service.filter_by_operation.assert_called_once_with("add")

    def test_show_memory_filter_submenu_filter_by_success(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, service = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli.memory_service = MagicMock()
        cli.memory_service.filter_by_success.return_value = [entry]
        with patch("builtins.input", side_effect=["3", "5"]):
            cli._show_memory_filter_submenu()
        cli.memory_service.filter_by_success.assert_called_once_with(True)

    def test_show_memory_filter_submenu_filter_by_error(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, service = _make_cli()
        entry = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        cli.memory_service = MagicMock()
        cli.memory_service.filter_by_success.return_value = [entry]
        with patch("builtins.input", side_effect=["4", "5"]):
            cli._show_memory_filter_submenu()
        cli.memory_service.filter_by_success.assert_called_once_with(False)

    def test_show_memory_filter_submenu_back_option(self, capsys):
        cli, service = _make_cli()
        cli.memory_service = MagicMock()
        with patch("builtins.input", side_effect=["5"]):
            cli._show_memory_filter_submenu()
        output = capsys.readouterr().out
        assert "Memory Filter Options" in output

    def test_show_memory_filter_submenu_invalid_choice(self, capsys):
        cli, service = _make_cli()
        cli.memory_service = MagicMock()
        cli.memory_service.get_all_entries.return_value = []
        with patch("builtins.input", side_effect=["99", "5"]):
            cli._show_memory_filter_submenu()
        output = capsys.readouterr().out
        assert "Invalid choice" in output

    def test_show_memory_calls_filter_submenu(self, capsys):
        cli, service = _make_cli()
        cli.memory_service = MagicMock()
        with patch.object(cli, "_show_memory_filter_submenu") as mock_submenu:
            cli._show_memory()
            mock_submenu.assert_called_once()

    def test_display_memory_entries_no_entries(self, capsys):
        cli, service = _make_cli()
        cli._display_memory_entries([])
        output = capsys.readouterr().out
        assert "No matching memory entries" in output

    def test_display_memory_entries_with_entries(self, capsys):
        from src.models.memory_entry import MemoryEntry
        cli, service = _make_cli()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        cli._display_memory_entries([entry])
        output = capsys.readouterr().out
        assert "add" in output
        assert "3.0" in output
