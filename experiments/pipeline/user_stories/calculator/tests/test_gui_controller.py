"""Tests for GUIController class."""

import pytest
from unittest.mock import MagicMock, Mock
from src.models.operation import Operation
from src.models.memory_entry import MemoryEntry
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService
from src.gui.gui_controller import GUIController


class TestGUIController:
    """Test suite for GUIController service bridge."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator_service_mock = MagicMock(spec=CalculatorService)
        self.memory_service_mock = MagicMock(spec=MemoryService)
        self.statistics_service_mock = MagicMock(spec=StatisticsService)
        self.controller = GUIController(
            self.calculator_service_mock,
            self.memory_service_mock,
            self.statistics_service_mock,
        )

    def test_perform_calculation_with_valid_operation(self):
        """Test performing a calculation with a valid operation."""
        expected_entry = MemoryEntry(
            operation="add",
            operand_a=2.0,
            operand_b=3.0,
            result=5.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("add", 2.0, 3.0)

        assert result == expected_entry
        self.calculator_service_mock.perform.assert_called_once()
        call_args = self.calculator_service_mock.perform.call_args
        assert call_args[0][1] == 2.0
        assert call_args[0][2] == 3.0

    def test_perform_calculation_with_subtract(self):
        """Test subtraction operation."""
        expected_entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("subtract", 10.0, 3.0)

        assert result.result == 7.0
        assert result.operation == "subtract"

    def test_perform_calculation_division_by_zero(self):
        """Test that division by zero returns error entry."""
        error_entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        self.calculator_service_mock.perform.return_value = error_entry

        result = self.controller.perform_calculation("divide", 5.0, 0.0)

        assert result.error is not None
        assert result.result is None
        assert "Division by zero" in result.error

    def test_perform_calculation_invalid_operation_raises_valueerror(self):
        """Test that invalid operation string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown operation"):
            self.controller.perform_calculation("invalid_op", 1.0, 2.0)

    def test_perform_calculation_with_negative_operands(self):
        """Test calculation with negative numbers."""
        expected_entry = MemoryEntry(
            operation="multiply",
            operand_a=-5.0,
            operand_b=3.0,
            result=-15.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("multiply", -5.0, 3.0)

        assert result.result == -15.0

    def test_perform_calculation_with_zero(self):
        """Test calculation with zero operand."""
        expected_entry = MemoryEntry(
            operation="add",
            operand_a=0.0,
            operand_b=5.0,
            result=5.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("add", 0.0, 5.0)

        assert result.result == 5.0

    def test_perform_calculation_sqrt(self):
        """Test sqrt unary operation."""
        expected_entry = MemoryEntry(
            operation="sqrt",
            operand_a=16.0,
            operand_b=0.0,
            result=4.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("sqrt", 16.0, 0.0)

        assert result.result == 4.0
        assert result.operation == "sqrt"

    def test_perform_calculation_with_float_operands(self):
        """Test calculation with floating point operands."""
        expected_entry = MemoryEntry(
            operation="divide",
            operand_a=7.5,
            operand_b=2.5,
            result=3.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("divide", 7.5, 2.5)

        assert result.result == 3.0

    def test_get_history_returns_all_entries(self):
        """Test getting full calculation history."""
        expected_history = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
        ]
        self.calculator_service_mock.get_history.return_value = expected_history

        result = self.controller.get_history()

        assert result == expected_history
        assert len(result) == 2
        self.calculator_service_mock.get_history.assert_called_once()

    def test_get_history_empty(self):
        """Test getting history when it's empty."""
        self.calculator_service_mock.get_history.return_value = []

        result = self.controller.get_history()

        assert result == []
        assert len(result) == 0

    def test_get_history_includes_errors(self):
        """Test that history includes both successful and failed entries."""
        expected_history = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
        ]
        self.calculator_service_mock.get_history.return_value = expected_history

        result = self.controller.get_history()

        assert len(result) == 2
        assert result[1].error is not None

    def test_filter_history_by_operations(self):
        """Test filtering history by specific operations."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("add", 5.0, 6.0, 11.0, None, None),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(operations=["add"])

        assert len(result) == 2
        assert all(e.operation == "add" for e in result)
        self.calculator_service_mock.filter_history.assert_called_once_with(
            ["add"], None
        )

    def test_filter_history_by_multiple_operations(self):
        """Test filtering by multiple operation types."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(operations=["add", "multiply"])

        assert len(result) == 2
        self.calculator_service_mock.filter_history.assert_called_once_with(
            ["add", "multiply"], None
        )

    def test_filter_history_by_state_success(self):
        """Test filtering history by successful state."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(state="success")

        assert len(result) == 2
        assert all(e.error is None for e in result)
        self.calculator_service_mock.filter_history.assert_called_once_with(
            None, "success"
        )

    def test_filter_history_by_state_error(self):
        """Test filtering history by error state."""
        filtered_entries = [
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(state="error")

        assert len(result) == 1
        assert result[0].error is not None
        self.calculator_service_mock.filter_history.assert_called_once_with(
            None, "error"
        )

    def test_filter_history_by_state_both(self):
        """Test filtering history with 'both' state includes all."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(state="both")

        assert len(result) == 2
        self.calculator_service_mock.filter_history.assert_called_once_with(
            None, "both"
        )

    def test_filter_history_by_operations_and_state(self):
        """Test filtering by both operations and state."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(operations=["add"], state="success")

        assert len(result) == 1
        self.calculator_service_mock.filter_history.assert_called_once_with(
            ["add"], "success"
        )

    def test_filter_history_empty_operations_list(self):
        """Test filtering with empty operations list."""
        self.calculator_service_mock.filter_history.return_value = []

        result = self.controller.filter_history(operations=[])

        assert result == []

    def test_filter_history_with_none_parameters(self):
        """Test filter_history with None parameters defaults to all."""
        all_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("divide", 5.0, 0.0, None, "Error", "ValueError"),
        ]
        self.calculator_service_mock.filter_history.return_value = all_entries

        result = self.controller.filter_history(operations=None, state=None)

        assert len(result) == 2

    def test_get_statistics(self):
        """Test retrieving calculation statistics."""
        stats_mock = MagicMock()
        self.statistics_service_mock.calculate_statistics.return_value = stats_mock

        result = self.controller.get_statistics()

        assert result == stats_mock
        self.statistics_service_mock.calculate_statistics.assert_called_once()

    def test_multiple_calculations_sequence(self):
        """Test performing multiple calculations in sequence."""
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, None, None)
        entry2 = MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None)
        self.calculator_service_mock.perform.side_effect = [entry1, entry2]

        result1 = self.controller.perform_calculation("add", 1.0, 2.0)
        result2 = self.controller.perform_calculation("subtract", 5.0, 2.0)

        assert result1.result == 3.0
        assert result2.result == 3.0
        assert self.calculator_service_mock.perform.call_count == 2

    def test_perform_calculation_preserves_operation_enum(self):
        """Test that Operation.from_string is properly called."""
        expected_entry = MemoryEntry(
            operation="power",
            operand_a=2.0,
            operand_b=3.0,
            result=8.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        result = self.controller.perform_calculation("power", 2.0, 3.0)

        assert result.operation == "power"
        # Verify the operation was converted by from_string
        call_args = self.calculator_service_mock.perform.call_args[0]
        assert isinstance(call_args[0], Operation)
        assert call_args[0].value == "power"
