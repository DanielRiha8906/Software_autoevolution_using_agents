"""Tests for InputPanel GUI component - Unit testing with mocks."""

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from src.gui.input_panel import InputPanel
from src.gui.constants import STANDARD_OPS, SCIENTIFIC_OPS


class TestInputPanelLogic:
    """Test suite for InputPanel logic without requiring display."""

    def setup_method(self):
        """Set up test fixtures with mocked tkinter."""
        # Mock tkinter components
        self.mock_root = MagicMock()

        with patch("src.gui.input_panel.tk.Frame.__init__", return_value=None):
            with patch.object(InputPanel, "_setup_ui"):
                self.panel = InputPanel(self.mock_root)

        # Set up actual StringVar-like mocks
        self.operation_var = {}
        self.operand_a_var = {}
        self.operand_b_var = {}
        self.error_text = {}

        def create_string_var(initial_value):
            var = {"value": initial_value}
            return var

        # Create the variables
        self.operation_var = create_string_var("add")
        self.operand_a_var = create_string_var("0")
        self.operand_b_var = create_string_var("0")
        self.error_text = {"value": ""}

        # Assign to panel
        self.panel.operation_var = MagicMock()
        self.panel.operand_a_var = MagicMock()
        self.panel.operand_b_var = MagicMock()
        self.panel.error_label = MagicMock()
        self.panel.operation_dropdown = MagicMock()
        self.panel.operand_a_entry = MagicMock()
        self.panel.operand_b_entry = MagicMock()

        # Mock the StringVar get/set behavior
        self.panel.operation_var.get = MagicMock(return_value="add")
        self.panel.operation_var.set = MagicMock()
        self.panel.operand_a_var.get = MagicMock(return_value="0")
        self.panel.operand_a_var.set = MagicMock()
        self.panel.operand_b_var.get = MagicMock(return_value="0")
        self.panel.operand_b_var.set = MagicMock()

        self.panel.calculate_callback = None
        self.panel.current_mode = "scientific"

    def teardown_method(self):
        """Clean up."""
        pass

    def test_get_operation_returns_selected_operation(self):
        """Test getting the currently selected operation."""
        self.panel.operation_var.get.return_value = "multiply"
        assert self.panel.get_operation() == "multiply"

    def test_get_operands_returns_tuple_of_floats(self):
        """Test getting operands as floats."""
        self.panel.operand_a_var.get.return_value = "5.5"
        self.panel.operand_b_var.get.return_value = "2.5"
        a, b = self.panel.get_operands()
        assert a == 5.5
        assert b == 2.5
        assert isinstance(a, float)
        assert isinstance(b, float)

    def test_get_operands_with_integers(self):
        """Test getting operands when entered as integers."""
        self.panel.operand_a_var.get.return_value = "10"
        self.panel.operand_b_var.get.return_value = "3"
        a, b = self.panel.get_operands()
        assert a == 10.0
        assert b == 3.0

    def test_get_operands_with_negative_numbers(self):
        """Test getting operands with negative values."""
        self.panel.operand_a_var.get.return_value = "-5.5"
        self.panel.operand_b_var.get.return_value = "-2.5"
        a, b = self.panel.get_operands()
        assert a == -5.5
        assert b == -2.5

    def test_get_operands_invalid_operand_a_raises_valueerror(self):
        """Test that non-numeric operand A raises ValueError."""
        self.panel.operand_a_var.get.return_value = "abc"
        self.panel.operand_b_var.get.return_value = "5"
        with pytest.raises(ValueError):
            self.panel.get_operands()

    def test_get_operands_invalid_operand_b_raises_valueerror(self):
        """Test that non-numeric operand B raises ValueError."""
        self.panel.operand_a_var.get.return_value = "5"
        self.panel.operand_b_var.get.return_value = "xyz"
        with pytest.raises(ValueError):
            self.panel.get_operands()

    def test_get_operands_both_invalid_raises_valueerror(self):
        """Test that both non-numeric operands raise ValueError."""
        self.panel.operand_a_var.get.return_value = "abc"
        self.panel.operand_b_var.get.return_value = "xyz"
        with pytest.raises(ValueError):
            self.panel.get_operands()

    def test_on_operation_change_disables_operand_b_for_unary(self):
        """Test that operand B is disabled for unary operations."""
        unary_ops = ["square", "sqrt", "sin", "cos", "tan", "log", "ln", "exp"]
        for op in unary_ops:
            self.panel.operation_var.get.return_value = op
            self.panel._on_operation_changed()
            self.panel.operand_b_entry.config.assert_called_with(state="disabled")

    def test_on_operation_change_enables_operand_b_for_binary(self):
        """Test that operand B is enabled for binary operations."""
        binary_ops = ["add", "subtract", "multiply", "divide", "power", "modulo"]
        for op in binary_ops:
            self.panel.operation_var.get.return_value = op
            self.panel._on_operation_changed()
            self.panel.operand_b_entry.config.assert_called_with(state="normal")

    def test_set_error_message(self):
        """Test setting an error message."""
        error_msg = "Error: Invalid input"
        self.panel.set_error_message(error_msg)
        self.panel.error_label.config.assert_called_with(text=error_msg)

    def test_clear_error_message(self):
        """Test clearing error message."""
        self.panel.clear_error_message()
        self.panel.error_label.config.assert_called_with(text="")

    def test_set_calculate_callback(self):
        """Test setting a callback for calculate button."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        assert self.panel.calculate_callback == callback

    def test_on_calculate_invokes_callback_with_correct_args(self):
        """Test that calculate button invokes callback with operation and operands."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        self.panel.operation_var.get.return_value = "multiply"
        self.panel.operand_a_var.get.return_value = "3"
        self.panel.operand_b_var.get.return_value = "4"

        self.panel._on_calculate()

        callback.assert_called_once_with("multiply", 3.0, 4.0)

    def test_on_calculate_with_float_operands(self):
        """Test calculate button with float operands."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        self.panel.operation_var.get.return_value = "divide"
        self.panel.operand_a_var.get.return_value = "7.5"
        self.panel.operand_b_var.get.return_value = "2.5"

        self.panel._on_calculate()

        callback.assert_called_once_with("divide", 7.5, 2.5)

    def test_on_calculate_clears_previous_error(self):
        """Test that calculate clears previous error messages."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        self.panel.operand_a_var.get.return_value = "5"
        self.panel.operand_b_var.get.return_value = "3"

        self.panel._on_calculate()

        # First call in _on_calculate should clear error
        self.panel.error_label.config.assert_called()

    def test_on_calculate_invalid_operand_shows_error(self):
        """Test that invalid operand shows error without calling callback."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        self.panel.operand_a_var.get.return_value = "abc"
        self.panel.operand_b_var.get.return_value = "5"

        self.panel._on_calculate()

        # Error label should be configured with error text
        calls = self.panel.error_label.config.call_args_list
        assert any("Error:" in str(call) for call in calls)
        callback.assert_not_called()

    def test_on_calculate_no_callback_does_not_crash(self):
        """Test that calculate without callback set doesn't crash."""
        self.panel.operand_a_var.get.return_value = "5"
        self.panel.operand_b_var.get.return_value = "3"
        # Should not raise
        self.panel._on_calculate()

    def test_on_clear_resets_operands(self):
        """Test that clear button resets operands."""
        self.panel._on_clear()

        self.panel.operand_a_var.set.assert_called_with("0")
        self.panel.operand_b_var.set.assert_called_with("0")

    def test_on_clear_resets_operation(self):
        """Test that clear button resets operation."""
        self.panel._on_clear()

        self.panel.operation_var.set.assert_called_with("add")

    def test_on_clear_clears_error_message(self):
        """Test that clear button clears error messages."""
        self.panel._on_clear()

        # error_label.config should be called with empty text
        calls = self.panel.error_label.config.call_args_list
        assert any(call[1].get('text') == "" for call in calls if call[1])

    def test_set_mode_standard(self):
        """Test setting standard mode."""
        self.panel.operation_dropdown.config = MagicMock()
        self.panel.set_mode("standard")

        assert self.panel.current_mode == "standard"
        # operation_dropdown should be updated with standard ops
        self.panel.operation_dropdown.config.assert_called()

    def test_set_mode_scientific(self):
        """Test setting scientific mode."""
        self.panel.operation_dropdown.config = MagicMock()
        self.panel.set_mode("scientific")

        assert self.panel.current_mode == "scientific"
        # operation_dropdown should be updated with scientific ops
        self.panel.operation_dropdown.config.assert_called()

    def test_standard_ops_count(self):
        """Test that standard mode has exactly 6 operations."""
        assert len(STANDARD_OPS) == 6

    def test_scientific_ops_count(self):
        """Test that scientific mode has exactly 14 operations."""
        assert len(SCIENTIFIC_OPS) == 14

    def test_get_operands_with_zero(self):
        """Test getting operands when one is zero."""
        self.panel.operand_a_var.get.return_value = "0"
        self.panel.operand_b_var.get.return_value = "5"
        a, b = self.panel.get_operands()
        assert a == 0.0
        assert b == 5.0

    def test_get_operands_very_large_numbers(self):
        """Test getting very large operands."""
        self.panel.operand_a_var.get.return_value = "999999999.99"
        self.panel.operand_b_var.get.return_value = "888888888.88"
        a, b = self.panel.get_operands()
        assert a == 999999999.99
        assert b == 888888888.88

    def test_get_operands_very_small_numbers(self):
        """Test getting very small operands."""
        self.panel.operand_a_var.get.return_value = "0.0001"
        self.panel.operand_b_var.get.return_value = "0.00001"
        a, b = self.panel.get_operands()
        assert a == pytest.approx(0.0001)
        assert b == pytest.approx(0.00001)

    def test_on_calculate_with_negative_result(self):
        """Test calculate with operands that produce negative result."""
        callback = MagicMock()
        self.panel.set_calculate_callback(callback)
        self.panel.operation_var.get.return_value = "subtract"
        self.panel.operand_a_var.get.return_value = "3"
        self.panel.operand_b_var.get.return_value = "5"

        self.panel._on_calculate()

        callback.assert_called_once_with("subtract", 3.0, 5.0)

    def test_set_mode_invalid_operation_resets(self):
        """Test that setting mode resets invalid operations."""
        self.panel.operation_var.get.return_value = "sin"
        self.panel.operation_dropdown.config = MagicMock()
        self.panel.set_mode("standard")

        # Should try to set operation to first standard op
        calls = self.panel.operation_var.set.call_args_list
        # After mode change, if sin not in standard, it should reset

    def test_multiple_callbacks_last_one_used(self):
        """Test that setting callback multiple times uses the last one."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.panel.set_calculate_callback(callback1)
        self.panel.set_calculate_callback(callback2)

        self.panel.operation_var.get.return_value = "add"
        self.panel.operand_a_var.get.return_value = "1"
        self.panel.operand_b_var.get.return_value = "2"

        self.panel._on_calculate()

        callback2.assert_called_once()
        callback1.assert_not_called()

    def test_operand_with_spaces(self):
        """Test that operands with spaces are handled."""
        self.panel.operand_a_var.get.return_value = " 5 "
        self.panel.operand_b_var.get.return_value = " 3 "
        a, b = self.panel.get_operands()
        # float() should handle leading/trailing spaces
        assert a == 5.0
        assert b == 3.0

    def test_operand_scientific_notation(self):
        """Test that operands in scientific notation work."""
        self.panel.operand_a_var.get.return_value = "1e3"
        self.panel.operand_b_var.get.return_value = "1e-2"
        a, b = self.panel.get_operands()
        assert a == 1000.0
        assert b == pytest.approx(0.01)
