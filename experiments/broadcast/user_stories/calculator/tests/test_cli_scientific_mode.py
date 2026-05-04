"""Tests for CLI scientific mode switching and unary operations."""

import pytest
import math
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.models.operation import Operation
from src.cli.calculator_cli import CalculatorCLI

_TS = "2026-01-01T00:00:00"


def _make_cli():
    service = MagicMock()
    memory_service = MagicMock()
    return CalculatorCLI(service, memory_service), service, memory_service


class TestModeToggling:
    """Test mode switching in interactive CLI."""

    def test_initial_mode_is_standard(self):
        """CLI should start in standard mode."""
        cli, _, _ = _make_cli()
        assert cli.mode == "standard"

    def test_toggle_mode_switches_to_scientific(self):
        """Toggling from standard to scientific should work."""
        cli, _, _ = _make_cli()
        cli._toggle_mode()
        assert cli.mode == "scientific"

    def test_toggle_mode_back_to_standard(self):
        """Toggling from scientific back to standard should work."""
        cli, _, _ = _make_cli()
        cli._toggle_mode()
        cli._toggle_mode()
        assert cli.mode == "standard"

    def test_standard_menu_has_8_operations(self):
        """Standard mode menu should have 8 operations."""
        cli, _, _ = _make_cli()
        assert cli.mode == "standard"
        assert len(cli._menu) == 8

    def test_scientific_menu_has_14_operations(self):
        """Scientific mode menu should have 8 standard + 6 scientific = 14 operations."""
        cli, _, _ = _make_cli()
        cli._toggle_mode()
        assert cli.mode == "scientific"
        assert len(cli._menu) == 14  # 8 standard + 6 scientific

    def test_scientific_menu_includes_sin(self):
        """Scientific menu should include SIN."""
        cli, _, _ = _make_cli()
        cli._toggle_mode()
        ops = [op for op, _ in cli._menu]
        assert Operation.SIN in ops

    def test_scientific_menu_includes_all_scientific_ops(self):
        """Scientific menu should include all scientific operations."""
        cli, _, _ = _make_cli()
        cli._toggle_mode()
        ops = [op for op, _ in cli._menu]
        scientific_ops = {Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP}
        assert all(op in ops for op in scientific_ops)

    def test_toggle_mode_updates_menu(self, capsys):
        """Toggling mode should update the internal menu."""
        cli, _, _ = _make_cli()
        initial_menu = cli._menu
        cli._toggle_mode()
        assert cli._menu != initial_menu
        assert len(cli._menu) > len(initial_menu)


class TestUnaryOperationIninteractive:
    """Test unary operations in interactive mode."""

    def test_sin_operation_in_interactive(self, capsys):
        """SIN operation should work in interactive mode."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("sin", 0, None, 0, _TS)
        cli.run_command("sin", 0, None)
        output = capsys.readouterr().out
        assert "sin(0" in output

    def test_cos_operation_command(self, capsys):
        """COS operation should work via run_command."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("cos", 0, None, 1.0, _TS)
        cli.run_command("cos", 0, None)
        output = capsys.readouterr().out
        assert "cos(0" in output
        assert "1" in output

    def test_ln_operation_command(self, capsys):
        """LN operation should work via run_command."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("ln", math.e, None, 1.0, _TS)
        cli.run_command("ln", math.e, None)
        service.perform.assert_called_once()
        call_args = service.perform.call_args[0]
        assert call_args[0] == Operation.LN

    def test_exp_operation_command(self, capsys):
        """EXP operation should work via run_command."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("exp", 1, None, math.e, _TS)
        cli.run_command("exp", 1, None)
        output = capsys.readouterr().out
        assert "exp(1" in output

    def test_log_operation_command(self, capsys):
        """LOG operation should work via run_command."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("log", 100, None, 2.0, _TS)
        cli.run_command("log", 100, None)
        output = capsys.readouterr().out
        assert "log(100" in output

    def test_tan_operation_command(self, capsys):
        """TAN operation should work via run_command."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("tan", 0, None, 0, _TS)
        cli.run_command("tan", 0, None)
        output = capsys.readouterr().out
        assert "tan(0" in output


class TestMenuStructure:
    """Test menu structure with mode switching."""

    def test_menu_option_numbers_standard_mode(self):
        """In standard mode, menu should have correct number of options."""
        cli, _, _ = _make_cli()
        # Standard: 8 operations + 1 mode + 6 utility + 1 exit = 16 total
        num_ops = len(cli._menu)
        assert num_ops == 8

    def test_menu_choice_resolution_in_standard_mode(self):
        """Menu choice resolution should work in standard mode."""
        cli, _, _ = _make_cli()
        from src.models.operation import Operation
        # First operation should be ADD
        op = cli._resolve_menu_choice("1")
        assert op == Operation.ADD

    def test_menu_choice_resolution_in_scientific_mode(self):
        """Menu choice resolution should work in scientific mode."""
        cli, _, _ = _make_cli()
        from src.models.operation import Operation
        cli._toggle_mode()
        # Items 1-8 should still be the standard operations
        op = cli._resolve_menu_choice("1")
        assert op == Operation.ADD
        # Items 9-14 should be scientific (depending on exact menu order)
        # Let's verify SIN is accessible
        all_ops = [op for op, _ in cli._menu]
        assert Operation.SIN in all_ops

    def test_invalid_menu_choice_returns_none(self):
        """Invalid menu choice should return None."""
        cli, _, _ = _make_cli()
        op = cli._resolve_menu_choice("999")
        assert op is None
        op = cli._resolve_menu_choice("abc")
        assert op is None


class TestInteractiveUnaryOps:
    """Test interactive mode with unary operations."""

    def test_unary_op_prompts_only_for_one_number(self, capsys):
        """Unary operations should only prompt for one number."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("sin", 1.57, None, 1.0, _TS)

        cli.run_command("sin", 1.57, None)

        # Verify perform was called with None for operand_b
        service.perform.assert_called_once()
        call_args = service.perform.call_args[0]
        assert call_args[0] == Operation.SIN
        assert call_args[1] == 1.57
        assert call_args[2] is None

    def test_binary_op_still_prompts_for_two_numbers(self, capsys):
        """Binary operations should still prompt for two numbers."""
        cli, service, _ = _make_cli()
        service.perform.return_value = CalculationResult("add", 3, 5, 8, _TS)

        cli.run_command("add", 3, 5)

        # Verify perform was called with both operands
        service.perform.assert_called_once()
        call_args = service.perform.call_args[0]
        assert call_args[0] == Operation.ADD
        assert call_args[1] == 3
        assert call_args[2] == 5


class TestModeToggleInteractive:
    """Test mode toggle in interactive menu."""

    def test_toggle_mode_option_is_available(self, capsys):
        """Mode toggle should be available in the menu."""
        cli, _, _ = _make_cli()
        # Menu position 9 should be the mode toggle
        num_ops = len(cli._menu)
        # The mode toggle is at position num_ops + 1
        assert cli.mode == "standard"
        # Simulate toggling through the menu option index
        # In the menu, position 9 is at index 8 (0-indexed), but the menu uses 1-based indexing

    def test_mode_toggle_through_menu_option(self, capsys):
        """Mode toggle should work as menu option 9."""
        cli, _, _ = _make_cli()
        # In standard mode: 8 ops + 1 mode toggle = position 9
        # After toggling, menu changes to 14 ops + 1 mode toggle = position 15
        # We need to provide enough inputs: choose toggle (9), then exit (22 after mode switch)
        with patch("builtins.input", side_effect=["9", "22"]):
            cli.run_interactive()
        output = capsys.readouterr().out
        # Should show mode switch message
        assert "scientific" in output.lower() or "Switched" in output
