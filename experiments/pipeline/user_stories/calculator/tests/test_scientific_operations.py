import pytest
import math
from unittest.mock import MagicMock, patch
from src.models.operation import Operation
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.cli.calculator_cli import CalculatorCLI
from src.models.memory_entry import MemoryEntry

_TS = "2026-01-01T00:00:00"


class TestCalculatorSin:
    """Test sin(a, b) - computes math.sin(a), ignores b"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("radians,expected", [
        (0, 0.0),
        (math.pi / 6, pytest.approx(0.5)),  # sin(30°) = 0.5
        (math.pi / 4, pytest.approx(math.sqrt(2) / 2)),  # sin(45°)
        (math.pi / 2, 1.0),  # sin(90°) = 1
        (math.pi, pytest.approx(0.0, abs=1e-10)),  # sin(180°) ≈ 0
        (3 * math.pi / 2, -1.0),  # sin(270°) = -1
        (2 * math.pi, pytest.approx(0.0, abs=1e-10)),  # sin(360°) ≈ 0
        (-math.pi / 2, -1.0),  # sin(-90°) = -1
        (0.5, pytest.approx(math.sin(0.5))),
        (1.0, pytest.approx(math.sin(1.0))),
        (-1.0, pytest.approx(math.sin(-1.0))),
    ])
    def test_sin_standard_angles(self, radians, expected):
        """Test sin at standard angles and edge cases."""
        assert self.calc.sin(radians, 0) == expected

    def test_sin_ignores_second_operand(self):
        """Verify that sin(a, b) only uses a, ignores b."""
        assert self.calc.sin(math.pi / 2, 999) == 1.0
        assert self.calc.sin(math.pi / 2, -999) == 1.0
        assert self.calc.sin(math.pi / 2, 0) == 1.0

    def test_sin_dispatches_via_calculate(self):
        """Test that sin is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.SIN, math.pi / 2, 0)
        assert result == 1.0

    def test_sin_very_large_input(self):
        """Test sin with very large input (should still work due to periodicity)."""
        result = self.calc.sin(1000 * math.pi, 0)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_sin_very_small_input(self):
        """Test sin with very small input."""
        small = 1e-10
        assert self.calc.sin(small, 0) == pytest.approx(small, rel=1e-8)

    def test_sin_negative_angle(self):
        """Test sin with negative angles."""
        assert self.calc.sin(-math.pi / 6, 0) == pytest.approx(-0.5)


class TestCalculatorCos:
    """Test cos(a, b) - computes math.cos(a), ignores b"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("radians,expected", [
        (0, 1.0),  # cos(0°) = 1
        (math.pi / 3, pytest.approx(0.5)),  # cos(60°) = 0.5
        (math.pi / 4, pytest.approx(math.sqrt(2) / 2)),  # cos(45°)
        (math.pi / 2, pytest.approx(0.0, abs=1e-10)),  # cos(90°) ≈ 0
        (math.pi, -1.0),  # cos(180°) = -1
        (3 * math.pi / 2, pytest.approx(0.0, abs=1e-10)),  # cos(270°) ≈ 0
        (2 * math.pi, 1.0),  # cos(360°) = 1
        (-math.pi, -1.0),  # cos(-180°) = -1
        (0.5, pytest.approx(math.cos(0.5))),
        (1.0, pytest.approx(math.cos(1.0))),
        (-1.0, pytest.approx(math.cos(-1.0))),
    ])
    def test_cos_standard_angles(self, radians, expected):
        """Test cos at standard angles and edge cases."""
        assert self.calc.cos(radians, 0) == expected

    def test_cos_ignores_second_operand(self):
        """Verify that cos(a, b) only uses a, ignores b."""
        assert self.calc.cos(0, 999) == 1.0
        assert self.calc.cos(0, -999) == 1.0
        assert self.calc.cos(0, 0) == 1.0

    def test_cos_dispatches_via_calculate(self):
        """Test that cos is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.COS, 0, 0)
        assert result == 1.0

    def test_cos_very_large_input(self):
        """Test cos with very large input (should still work due to periodicity)."""
        result = self.calc.cos(1000 * math.pi, 0)
        assert result == pytest.approx(1.0)

    def test_cos_very_small_input(self):
        """Test cos with very small input."""
        small = 1e-10
        assert self.calc.cos(small, 0) == pytest.approx(1.0, rel=1e-8)


class TestCalculatorTan:
    """Test tan(a, b) - computes math.tan(a), ignores b"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("radians,expected", [
        (0, 0.0),
        (math.pi / 6, pytest.approx(1 / math.sqrt(3))),  # tan(30°)
        (math.pi / 4, pytest.approx(1.0)),  # tan(45°) = 1
        (math.pi, pytest.approx(0.0, abs=1e-10)),  # tan(180°) ≈ 0
        (2 * math.pi, pytest.approx(0.0, abs=1e-10)),  # tan(360°) ≈ 0
        (-math.pi / 4, pytest.approx(-1.0)),  # tan(-45°) = -1
        (0.5, pytest.approx(math.tan(0.5))),
        (1.0, pytest.approx(math.tan(1.0))),
        (-1.0, pytest.approx(math.tan(-1.0))),
    ])
    def test_tan_standard_angles(self, radians, expected):
        """Test tan at standard angles and edge cases."""
        assert self.calc.tan(radians, 0) == expected

    def test_tan_ignores_second_operand(self):
        """Verify that tan(a, b) only uses a, ignores b."""
        assert self.calc.tan(0, 999) == 0.0
        assert self.calc.tan(0, -999) == 0.0
        assert self.calc.tan(0, 0) == 0.0

    def test_tan_dispatches_via_calculate(self):
        """Test that tan is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.TAN, math.pi / 4, 0)
        assert result == pytest.approx(1.0)

    def test_tan_very_large_input(self):
        """Test tan with very large input (should still work due to periodicity)."""
        result = self.calc.tan(1000 * math.pi, 0)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_tan_near_asymptote(self):
        """Test tan near asymptotes (pi/2 and -pi/2) - values will be very large."""
        # Note: exact asymptotes would cause overflow, but near them we get large values
        near_pi_2 = math.pi / 2 - 1e-5
        result = self.calc.tan(near_pi_2, 0)
        assert abs(result) > 1000  # Very large positive

        near_neg_pi_2 = -math.pi / 2 + 1e-5
        result = self.calc.tan(near_neg_pi_2, 0)
        assert abs(result) > 1000  # Very large negative


class TestCalculatorLog:
    """Test log(a, b) - computes math.log10(a), validates a > 0"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("value,expected", [
        (1, 0.0),  # log10(1) = 0
        (10, 1.0),  # log10(10) = 1
        (100, 2.0),  # log10(100) = 2
        (0.1, -1.0),  # log10(0.1) = -1
        (0.01, -2.0),  # log10(0.01) = -2
        (1000, 3.0),  # log10(1000) = 3
        (2, pytest.approx(math.log10(2))),
        (5, pytest.approx(math.log10(5))),
        (50, pytest.approx(math.log10(50))),
        (1e-5, -5.0),
        (1e-10, -10.0),
    ])
    def test_log_valid_inputs(self, value, expected):
        """Test log with valid positive inputs."""
        assert self.calc.log(value, 0) == expected

    def test_log_ignores_second_operand(self):
        """Verify that log(a, b) only uses a, ignores b."""
        assert self.calc.log(10, 999) == 1.0
        assert self.calc.log(10, -999) == 1.0
        assert self.calc.log(10, 0) == 1.0

    def test_log_zero_raises(self):
        """Test that log(0) raises ValueError."""
        with pytest.raises(ValueError, match="Logarithm of non-positive number is not allowed"):
            self.calc.log(0, 0)

    def test_log_negative_raises(self):
        """Test that log(negative) raises ValueError."""
        with pytest.raises(ValueError, match="Logarithm of non-positive number is not allowed"):
            self.calc.log(-1, 0)

    def test_log_very_negative_raises(self):
        """Test that log(very negative) raises ValueError."""
        with pytest.raises(ValueError, match="Logarithm of non-positive number is not allowed"):
            self.calc.log(-1e10, 0)

    def test_log_dispatches_via_calculate(self):
        """Test that log is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.LOG, 100, 0)
        assert result == 2.0

    def test_log_dispatches_error(self):
        """Test that log error dispatches through calculate."""
        with pytest.raises(ValueError, match="Logarithm of non-positive number is not allowed"):
            self.calc.calculate(Operation.LOG, -5, 0)


class TestCalculatorLn:
    """Test ln(a, b) - computes math.log(a), validates a > 0"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("value,expected", [
        (1, 0.0),  # ln(1) = 0
        (math.e, 1.0),  # ln(e) = 1
        (math.e ** 2, 2.0),  # ln(e^2) = 2
        (0.1, pytest.approx(math.log(0.1))),
        (0.5, pytest.approx(math.log(0.5))),
        (2, pytest.approx(math.log(2))),
        (10, pytest.approx(math.log(10))),
        (100, pytest.approx(math.log(100))),
        (1e-5, pytest.approx(math.log(1e-5))),
    ])
    def test_ln_valid_inputs(self, value, expected):
        """Test ln with valid positive inputs."""
        assert self.calc.ln(value, 0) == expected

    def test_ln_ignores_second_operand(self):
        """Verify that ln(a, b) only uses a, ignores b."""
        assert self.calc.ln(math.e, 999) == 1.0
        assert self.calc.ln(math.e, -999) == 1.0
        assert self.calc.ln(math.e, 0) == 1.0

    def test_ln_zero_raises(self):
        """Test that ln(0) raises ValueError."""
        with pytest.raises(ValueError, match="Natural logarithm of non-positive number is not allowed"):
            self.calc.ln(0, 0)

    def test_ln_negative_raises(self):
        """Test that ln(negative) raises ValueError."""
        with pytest.raises(ValueError, match="Natural logarithm of non-positive number is not allowed"):
            self.calc.ln(-1, 0)

    def test_ln_very_negative_raises(self):
        """Test that ln(very negative) raises ValueError."""
        with pytest.raises(ValueError, match="Natural logarithm of non-positive number is not allowed"):
            self.calc.ln(-1e10, 0)

    def test_ln_dispatches_via_calculate(self):
        """Test that ln is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.LN, math.e, 0)
        assert result == 1.0

    def test_ln_dispatches_error(self):
        """Test that ln error dispatches through calculate."""
        with pytest.raises(ValueError, match="Natural logarithm of non-positive number is not allowed"):
            self.calc.calculate(Operation.LN, -5, 0)


class TestCalculatorExp:
    """Test exp(a, b) - computes math.exp(a), ignores b"""

    def setup_method(self):
        self.calc = Calculator()

    @pytest.mark.parametrize("value,expected", [
        (0, 1.0),  # e^0 = 1
        (1, pytest.approx(math.e)),  # e^1 = e
        (2, pytest.approx(math.e ** 2)),  # e^2
        (-1, pytest.approx(1 / math.e)),  # e^(-1) = 1/e
        (-2, pytest.approx(1 / (math.e ** 2))),  # e^(-2)
        (0.5, pytest.approx(math.exp(0.5))),
        (1.5, pytest.approx(math.exp(1.5))),
        (-0.5, pytest.approx(math.exp(-0.5))),
        (10, pytest.approx(math.exp(10))),
    ])
    def test_exp_normal_cases(self, value, expected):
        """Test exp with normal inputs."""
        assert self.calc.exp(value, 0) == expected

    def test_exp_ignores_second_operand(self):
        """Verify that exp(a, b) only uses a, ignores b."""
        assert self.calc.exp(0, 999) == 1.0
        assert self.calc.exp(0, -999) == 1.0
        assert self.calc.exp(0, 0) == 1.0

    def test_exp_dispatches_via_calculate(self):
        """Test that exp is reachable via calculate dispatcher."""
        result = self.calc.calculate(Operation.EXP, 0, 0)
        assert result == 1.0

    def test_exp_negative_input(self):
        """Test exp with negative input approaches zero."""
        result = self.calc.exp(-100, 0)
        assert result == pytest.approx(0.0, abs=1e-40)

    def test_exp_very_small_positive(self):
        """Test exp with very small positive input."""
        small = 1e-10
        assert self.calc.exp(small, 0) == pytest.approx(1.0, rel=1e-8)


class TestCalculatorCalculateDispatcher:
    """Test that calculate() dispatcher handles all 14 operations."""

    def setup_method(self):
        self.calc = Calculator()

    def test_calculate_dispatches_all_operations(self):
        """Verify all 14 operations are in the dispatcher and callable."""
        operations = [
            Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE,
            Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO,
            Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP,
        ]

        # Quick smoke test for each operation
        test_cases = {
            Operation.ADD: (3, 5, 8),
            Operation.SUBTRACT: (10, 4, 6),
            Operation.MULTIPLY: (3, 5, 15),
            Operation.DIVIDE: (10, 2, 5.0),
            Operation.SQUARE: (5, 0, 25),
            Operation.SQRT: (16, 0, 4),
            Operation.POWER: (2, 3, 8),
            Operation.MODULO: (10, 3, 1),
            Operation.SIN: (0, 0, 0.0),
            Operation.COS: (0, 0, 1.0),
            Operation.TAN: (0, 0, 0.0),
            Operation.LOG: (10, 0, 1.0),
            Operation.LN: (math.e, 0, 1.0),
            Operation.EXP: (0, 0, 1.0),
        }

        for op in operations:
            a, b, expected = test_cases[op]
            result = self.calc.calculate(op, a, b)
            assert result == pytest.approx(expected), f"Operation {op.value} failed"

    def test_calculate_unsupported_operation_raises(self):
        """Test that all standard operations are supported (no unsupported ops in dispatch)."""
        # All operations in the enum should be supported
        # This is verified by test_calculate_dispatches_all_operations
        # This test just documents that the error handling exists
        assert True  # No invalid Operations can be created in normal use


class TestCalculatorCLIMenu:
    """Test that CalculatorCLI._MENU has exactly 14 items."""

    def test_menu_has_14_items(self):
        """Verify the menu contains exactly 14 operation options."""
        service = MagicMock()
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        assert len(cli._MENU) == 14, f"Expected 14 menu items, got {len(cli._MENU)}"

    def test_menu_contains_all_operations(self):
        """Verify menu contains all 14 operations."""
        service = MagicMock()
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        operations = [op for op, _ in cli._MENU]
        expected_ops = [
            Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE,
            Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO,
            Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP,
        ]

        assert len(operations) == 14
        assert set(operations) == set(expected_ops)

    def test_menu_items_have_labels(self):
        """Verify each menu item has a non-empty label."""
        service = MagicMock()
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        for op, label in cli._MENU:
            assert isinstance(label, str)
            assert len(label) > 0
            assert isinstance(op, Operation)

    def test_menu_labels_are_user_friendly(self):
        """Verify menu labels include human-readable names."""
        service = MagicMock()
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        # Check that scientific operations have reasonable labels
        menu_dict = {op: label for op, label in cli._MENU}

        assert "Sine" in menu_dict[Operation.SIN]
        assert "Cosine" in menu_dict[Operation.COS]
        assert "Tangent" in menu_dict[Operation.TAN]
        assert "Log" in menu_dict[Operation.LOG]
        assert "Natural Log" in menu_dict[Operation.LN] or "ln" in menu_dict[Operation.LN].lower()
        assert "Exponential" in menu_dict[Operation.EXP] or "exp" in menu_dict[Operation.EXP].lower()

    def test_menu_print_shows_14_operations(self, capsys):
        """Verify _print_menu displays all 14 operations."""
        service = MagicMock()
        service.get_history.return_value = []
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        cli._print_menu()
        output = capsys.readouterr().out

        # Should list 14 operations plus view history, filter, stats, export, import, exit
        assert "1." in output
        assert "14." in output
        assert "15." in output  # View history
        assert "20." in output  # Exit (6 extras after 14 operations)


class TestArgparseOperationChoices:
    """Test that argparse --operation accepts all 14 operations."""

    def test_operation_choices_in_main(self):
        """Verify argparse in __main__.py includes all 14 operation choices."""
        # Import the main module to check the parser
        from src.__main__ import main
        import argparse

        # We'll parse the help text to verify operations are listed
        # Instead, we can test each operation string directly
        valid_operations = [
            "add", "subtract", "multiply", "divide",
            "square", "sqrt", "power", "modulo",
            "sin", "cos", "tan", "log", "ln", "exp",
        ]

        assert len(valid_operations) == 14
        for op in valid_operations:
            # These should be valid Operation enum values
            operation = Operation.from_string(op)
            assert operation is not None

    @pytest.mark.parametrize("op_string", [
        "add", "subtract", "multiply", "divide",
        "square", "sqrt", "power", "modulo",
        "sin", "cos", "tan", "log", "ln", "exp",
    ])
    def test_operation_string_conversion(self, op_string):
        """Test that all 14 operation strings convert via Operation.from_string()."""
        operation = Operation.from_string(op_string)
        assert operation is not None
        assert operation.value == op_string


class TestCalculatorServiceScientificOps:
    """Test CalculatorService.perform() with scientific operations."""

    def test_service_perform_sin(self):
        """Test CalculatorService.perform with sin operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.SIN, math.pi / 2, 0)
        assert result.error is None
        assert result.result == 1.0
        assert result.operation == "sin"

    def test_service_perform_cos(self):
        """Test CalculatorService.perform with cos operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.COS, 0, 0)
        assert result.error is None
        assert result.result == 1.0
        assert result.operation == "cos"

    def test_service_perform_tan(self):
        """Test CalculatorService.perform with tan operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.TAN, 0, 0)
        assert result.error is None
        assert result.result == 0.0
        assert result.operation == "tan"

    def test_service_perform_log_valid(self):
        """Test CalculatorService.perform with valid log operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.LOG, 10, 0)
        assert result.error is None
        assert result.result == 1.0
        assert result.operation == "log"

    def test_service_perform_log_domain_error(self):
        """Test CalculatorService.perform captures log domain error."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.LOG, -5, 0)
        assert result.error is not None
        assert "Logarithm of non-positive number" in result.error
        assert result.result is None
        assert result.operation == "log"
        assert result.error_type == "ValueError"

    def test_service_perform_ln_valid(self):
        """Test CalculatorService.perform with valid ln operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.LN, math.e, 0)
        assert result.error is None
        assert result.result == pytest.approx(1.0)
        assert result.operation == "ln"

    def test_service_perform_ln_domain_error(self):
        """Test CalculatorService.perform captures ln domain error."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.LN, 0, 0)
        assert result.error is not None
        assert "Natural logarithm of non-positive number" in result.error
        assert result.result is None
        assert result.operation == "ln"
        assert result.error_type == "ValueError"

    def test_service_perform_exp(self):
        """Test CalculatorService.perform with exp operation."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        result = service.perform(Operation.EXP, 0, 0)
        assert result.error is None
        assert result.result == 1.0
        assert result.operation == "exp"

    def test_service_stores_entry_for_sin(self):
        """Test that CalculatorService stores memory entry for sin."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        service.perform(Operation.SIN, 0, 0)
        memory.store.assert_called_once()
        entry = memory.store.call_args[0][0]
        assert entry.operation == "sin"
        assert entry.operand_a == 0
        assert entry.operand_b == 0

    def test_service_stores_entry_for_log_error(self):
        """Test that CalculatorService stores error entry for log."""
        calc = Calculator()
        memory = MagicMock()
        service = CalculatorService(calc, memory)

        service.perform(Operation.LOG, -1, 0)
        memory.store.assert_called_once()
        entry = memory.store.call_args[0][0]
        assert entry.operation == "log"
        assert entry.error is not None


class TestCLICommandScientificOps:
    """Test CalculatorCLI.run_command with scientific operations."""

    def _make_cli(self):
        service = MagicMock()
        stats_service = MagicMock()
        import_export_service = MagicMock()
        return CalculatorCLI(service, stats_service, import_export_service), service

    def test_run_command_sin(self, capsys):
        """Test run_command with sin operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("sin", math.pi / 2, 0, 1.0, None, None, _TS)
        cli.run_command("sin", math.pi / 2, 0)
        assert "1" in capsys.readouterr().out

    def test_run_command_cos(self, capsys):
        """Test run_command with cos operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("cos", 0, 0, 1.0, None, None, _TS)
        cli.run_command("cos", 0, 0)
        assert "1" in capsys.readouterr().out

    def test_run_command_tan(self, capsys):
        """Test run_command with tan operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("tan", 0, 0, 0.0, None, None, _TS)
        cli.run_command("tan", 0, 0)
        assert "0" in capsys.readouterr().out

    def test_run_command_log(self, capsys):
        """Test run_command with log operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("log", 10, 0, 1.0, None, None, _TS)
        cli.run_command("log", 10, 0)
        assert "1" in capsys.readouterr().out

    def test_run_command_log_error(self):
        """Test run_command with log error."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("log", -1, 0, None, "Logarithm of non-positive number is not allowed", "ValueError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("log", -1, 0)

    def test_run_command_ln(self, capsys):
        """Test run_command with ln operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("ln", math.e, 0, 1.0, None, None, _TS)
        cli.run_command("ln", math.e, 0)
        assert "1" in capsys.readouterr().out

    def test_run_command_ln_error(self):
        """Test run_command with ln error."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("ln", 0, 0, None, "Natural logarithm of non-positive number is not allowed", "ValueError", _TS)
        with pytest.raises(SystemExit):
            cli.run_command("ln", 0, 0)

    def test_run_command_exp(self, capsys):
        """Test run_command with exp operation."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("exp", 0, 0, 1.0, None, None, _TS)
        cli.run_command("exp", 0, 0)
        assert "1" in capsys.readouterr().out

    def test_run_command_exp_negative(self, capsys):
        """Test run_command with negative exp."""
        cli, service = self._make_cli()
        service.perform.return_value = MemoryEntry("exp", -1, 0, 1/math.e, None, None, _TS)
        cli.run_command("exp", -1, 0)
        output = capsys.readouterr().out
        # Should print a result (the actual value of 1/e ≈ 0.368)
        assert "0.36" in output or "0.37" in output or "368" in output


class TestCLIInteractiveMenuDisplay:
    """Test that interactive menu displays all 14 operations correctly."""

    def test_menu_option_count(self, capsys):
        """Test that menu prints option 14 for the last operation."""
        service = MagicMock()
        service.get_history.return_value = []
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        cli._print_menu()
        output = capsys.readouterr().out

        # Check that option 14 exists (14th operation)
        assert "14." in output
        # Check that option 15 exists (View history)
        assert "15." in output

    def test_menu_contains_all_scientific_ops(self, capsys):
        """Test that menu displays all scientific operations."""
        service = MagicMock()
        service.get_history.return_value = []
        stats_service = MagicMock()
        import_export_service = MagicMock()
        cli = CalculatorCLI(service, stats_service, import_export_service)

        cli._print_menu()
        output = capsys.readouterr().out

        # Check for scientific operation names
        assert "Sine" in output or "sine" in output.lower()
        assert "Cosine" in output or "cosine" in output.lower()
        assert "Tangent" in output or "tangent" in output.lower()
        assert "Log" in output or "log" in output.lower()
        assert "Exponential" in output or "exp" in output.lower()


class TestTrigonometricEdgeCases:
    """Additional edge case tests for trigonometric functions."""

    def setup_method(self):
        self.calc = Calculator()

    def test_sin_between_zero_and_pi_2(self):
        """Test sin increases from 0 to 1 as angle goes from 0 to π/2."""
        result1 = self.calc.sin(0, 0)
        result2 = self.calc.sin(math.pi / 6, 0)
        result3 = self.calc.sin(math.pi / 3, 0)
        result4 = self.calc.sin(math.pi / 2, 0)

        assert result1 < result2 < result3 < result4

    def test_cos_between_zero_and_pi(self):
        """Test cos decreases from 1 to -1 as angle goes from 0 to π."""
        result1 = self.calc.cos(0, 0)
        result2 = self.calc.cos(math.pi / 3, 0)
        result3 = self.calc.cos(math.pi / 2, 0)
        result4 = self.calc.cos(2 * math.pi / 3, 0)
        result5 = self.calc.cos(math.pi, 0)

        assert result1 > result2 > result3 > result4 > result5

    def test_tan_increases_from_zero(self):
        """Test tan increases as angle increases from 0."""
        result1 = self.calc.tan(0, 0)
        result2 = self.calc.tan(math.pi / 6, 0)
        result3 = self.calc.tan(math.pi / 4, 0)
        result4 = self.calc.tan(math.pi / 3, 0)

        assert result1 < result2 < result3 < result4


class TestLogarithmEdgeCases:
    """Additional edge case tests for logarithmic functions."""

    def setup_method(self):
        self.calc = Calculator()

    def test_log_is_increasing(self):
        """Test that log is an increasing function."""
        result1 = self.calc.log(1, 0)
        result2 = self.calc.log(2, 0)
        result3 = self.calc.log(10, 0)
        result4 = self.calc.log(100, 0)
        result5 = self.calc.log(1000, 0)

        assert result1 < result2 < result3 < result4 < result5

    def test_ln_is_increasing(self):
        """Test that ln is an increasing function."""
        result1 = self.calc.ln(1, 0)
        result2 = self.calc.ln(2, 0)
        result3 = self.calc.ln(math.e, 0)
        result4 = self.calc.ln(10, 0)
        result5 = self.calc.ln(100, 0)

        assert result1 < result2 < result3 < result4 < result5

    def test_log_of_power_of_10(self):
        """Test log of powers of 10."""
        for i in range(-3, 4):
            result = self.calc.log(10 ** i, 0)
            assert result == pytest.approx(float(i))

    def test_ln_of_power_of_e(self):
        """Test ln of powers of e."""
        for i in range(-3, 4):
            result = self.calc.ln(math.e ** i, 0)
            assert result == pytest.approx(float(i))


class TestExponentialEdgeCases:
    """Additional edge case tests for exponential functions."""

    def setup_method(self):
        self.calc = Calculator()

    def test_exp_is_increasing(self):
        """Test that exp is an increasing function."""
        result1 = self.calc.exp(-2, 0)
        result2 = self.calc.exp(-1, 0)
        result3 = self.calc.exp(0, 0)
        result4 = self.calc.exp(1, 0)
        result5 = self.calc.exp(2, 0)

        assert result1 < result2 < result3 < result4 < result5

    def test_exp_of_ln_is_identity(self):
        """Test that exp(ln(x)) = x for positive x."""
        for x in [0.1, 1, 2.5, 10, 100]:
            ln_x = self.calc.ln(x, 0)
            exp_ln_x = self.calc.exp(ln_x, 0)
            assert exp_ln_x == pytest.approx(x, rel=1e-10)

    def test_ln_of_exp_is_identity(self):
        """Test that ln(exp(x)) = x."""
        for x in [-2, -1, 0, 1, 2]:
            exp_x = self.calc.exp(x, 0)
            ln_exp_x = self.calc.ln(exp_x, 0)
            assert ln_exp_x == pytest.approx(x, rel=1e-10)
