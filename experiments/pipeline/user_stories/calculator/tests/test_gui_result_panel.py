"""Tests for ResultPanel GUI component - Unit testing with mocks."""

import pytest
from unittest.mock import MagicMock, patch
from src.gui.result_panel import ResultPanel
from src.gui.constants import (
    COLOR_ERROR_TEXT, COLOR_ERROR_BACKGROUND,
    COLOR_SUCCESS_TEXT, COLOR_SUCCESS_BACKGROUND,
    FONT_RESULT, FONT_ERROR
)
from src.models.memory_entry import MemoryEntry


class TestResultPanelLogic:
    """Test suite for ResultPanel logic without requiring display."""

    def setup_method(self):
        """Set up test fixtures with mocked tkinter."""
        self.mock_root = MagicMock()

        with patch("src.gui.result_panel.tk.Frame.__init__", return_value=None):
            with patch.object(ResultPanel, "_setup_ui"):
                self.panel = ResultPanel(self.mock_root)

        self.panel.result_label = MagicMock()

    def teardown_method(self):
        """Clean up."""
        pass

    def test_display_result_successful_calculation(self):
        """Test displaying a successful calculation result."""
        entry = MemoryEntry(
            operation="add",
            operand_a=2.0,
            operand_b=3.0,
            result=5.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        # Verify label was configured
        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "2 + 3 = 5" in call_kwargs.get("text", "")
        assert call_kwargs.get("fg") == COLOR_SUCCESS_TEXT
        assert call_kwargs.get("bg") == COLOR_SUCCESS_BACKGROUND

    def test_display_result_with_subtraction(self):
        """Test displaying subtraction result with correct symbol."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "10 - 3 = 7" in call_kwargs.get("text", "")

    def test_display_result_with_multiplication(self):
        """Test displaying multiplication result with correct symbol."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "3 × 4 = 12" in call_kwargs.get("text", "")

    def test_display_result_with_division(self):
        """Test displaying division result with correct symbol."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=8.0,
            operand_b=2.0,
            result=4.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "8 ÷ 2 = 4" in call_kwargs.get("text", "")

    def test_display_result_with_square(self):
        """Test displaying square operation result."""
        entry = MemoryEntry(
            operation="square",
            operand_a=5.0,
            operand_b=0.0,
            result=25.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "25" in call_kwargs.get("text", "")

    def test_display_result_with_sqrt(self):
        """Test displaying sqrt operation result."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=16.0,
            operand_b=0.0,
            result=4.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        assert "4" in text

    def test_display_result_error_division_by_zero(self):
        """Test displaying error for division by zero."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "ERROR:" in call_kwargs.get("text", "")
        assert "Division by zero" in call_kwargs.get("text", "")
        assert call_kwargs.get("fg") == COLOR_ERROR_TEXT
        assert call_kwargs.get("bg") == COLOR_ERROR_BACKGROUND

    def test_display_result_error_invalid_sqrt(self):
        """Test displaying error for invalid sqrt."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-4.0,
            operand_b=0.0,
            result=None,
            error="Cannot compute sqrt of negative number",
            error_type="ValueError",
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "ERROR:" in call_kwargs.get("text", "")
        assert "negative" in call_kwargs.get("text", "").lower()
        assert call_kwargs.get("fg") == COLOR_ERROR_TEXT

    def test_display_result_uses_font_result_for_success(self):
        """Test that successful results use FONT_RESULT."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=1.0,
            result=2.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert call_kwargs.get("font") == FONT_RESULT

    def test_display_result_uses_font_error_for_failure(self):
        """Test that error results use FONT_ERROR."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=1.0,
            operand_b=0.0,
            result=None,
            error="Error message",
            error_type="ValueError",
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert call_kwargs.get("font") == FONT_ERROR

    def test_clear_resets_to_initial_state(self):
        """Test that clear resets the panel to initial state."""
        self.panel.clear()

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert call_kwargs.get("text") == "No calculation yet"
        assert call_kwargs.get("fg") == COLOR_SUCCESS_TEXT
        assert call_kwargs.get("bg") == COLOR_SUCCESS_BACKGROUND

    def test_display_result_float_result(self):
        """Test displaying float results."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=7.0,
            operand_b=2.0,
            result=3.5,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "3.5" in call_kwargs.get("text", "")

    def test_display_result_negative_result(self):
        """Test displaying negative results."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=5.0,
            operand_b=10.0,
            result=-5.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "-5" in call_kwargs.get("text", "")

    def test_display_result_zero_result(self):
        """Test displaying zero result."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=5.0,
            operand_b=5.0,
            result=0.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "= 0" in call_kwargs.get("text", "")

    def test_display_result_with_negative_operands(self):
        """Test displaying result with negative operands."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=-3.0,
            operand_b=-4.0,
            result=12.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        assert "-3" in text
        assert "-4" in text
        assert "12" in text

    def test_display_result_integer_conversion(self):
        """Test that integer results are displayed without decimals."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        # Should show as "3" not "3.0"
        assert "= 3" in text
        assert "3.0" not in text

    def test_display_result_long_error_message(self):
        """Test displaying long error messages."""
        long_error = "This is a very long error message that describes what went wrong in detail"
        entry = MemoryEntry(
            operation="divide",
            operand_a=1.0,
            operand_b=0.0,
            result=None,
            error=long_error,
            error_type="ValueError",
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        assert long_error in text

    def test_display_multiple_results_sequentially(self):
        """Test displaying multiple results in sequence."""
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, None, None)
        entry2 = MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None)

        self.panel.display_result(entry1)
        call_kwargs1 = self.panel.result_label.config.call_args_list[-1][1]
        assert "1 + 2 = 3" in call_kwargs1.get("text", "")

        self.panel.display_result(entry2)
        call_kwargs2 = self.panel.result_label.config.call_args_list[-1][1]
        assert "3 × 4 = 12" in call_kwargs2.get("text", "")

    def test_display_result_then_clear_then_new_result(self):
        """Test the cycle of display, clear, display."""
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, None, None)
        entry2 = MemoryEntry("subtract", 10.0, 3.0, 7.0, None, None)

        self.panel.display_result(entry1)
        self.panel.clear()
        self.panel.display_result(entry2)

        # Last call should be for entry2
        call_kwargs = self.panel.result_label.config.call_args[1]
        assert "10 - 3 = 7" in call_kwargs.get("text", "")

    def test_display_result_power_operation(self):
        """Test displaying power operation result."""
        entry = MemoryEntry(
            operation="power",
            operand_a=2.0,
            operand_b=3.0,
            result=8.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        assert "8" in text

    def test_display_result_modulo_operation(self):
        """Test displaying modulo operation result."""
        entry = MemoryEntry(
            operation="modulo",
            operand_a=10.0,
            operand_b=3.0,
            result=1.0,
            error=None,
            error_type=None,
        )
        self.panel.display_result(entry)

        call_kwargs = self.panel.result_label.config.call_args[1]
        text = call_kwargs.get("text", "")
        assert "1" in text
