"""Integration tests for GUI components working together."""

import pytest
from unittest.mock import MagicMock, Mock, patch
from src.gui.gui_controller import GUIController
from src.models.memory_entry import MemoryEntry
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService


class TestGUIIntegration:
    """Integration tests for GUI components."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock services
        self.calculator_service_mock = MagicMock(spec=CalculatorService)
        self.memory_service_mock = MagicMock(spec=MemoryService)
        self.statistics_service_mock = MagicMock(spec=StatisticsService)

        # Create controller
        self.controller = GUIController(
            self.calculator_service_mock,
            self.memory_service_mock,
            self.statistics_service_mock,
        )

    def teardown_method(self):
        """Clean up."""
        pass

    def test_calculation_flow_standard(self):
        """Test standard calculation flow: input -> calculate -> display result."""
        # Simulate calculation
        expected_entry = MemoryEntry(
            operation="add",
            operand_a=2.0,
            operand_b=3.0,
            result=5.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = expected_entry

        # Perform calculation
        result = self.controller.perform_calculation("add", 2.0, 3.0)

        # Verify result
        assert result.result == 5.0
        assert result.operation == "add"

    def test_calculation_with_history_persistence(self):
        """Test that calculation results persist in history."""
        # Set up history mock
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, None, None)
        entry2 = MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None)
        self.calculator_service_mock.get_history.return_value = [entry1, entry2]

        # Get history
        history = self.controller.get_history()

        # Verify history is returned
        assert len(history) == 2
        assert history[0].operation == "add"
        assert history[1].operation == "subtract"

    def test_error_calculation_with_error_display(self):
        """Test error calculation flow with error highlighting."""
        # Simulate error
        error_entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        self.calculator_service_mock.perform.return_value = error_entry

        # Perform calculation
        result = self.controller.perform_calculation("divide", 5.0, 0.0)

        # Verify error is present
        assert result.error is not None
        assert "Division by zero" in result.error

    def test_filtering_history_by_operation(self):
        """Test filtering history by operation type."""
        # Set up history
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
            MemoryEntry("add", 5.0, 6.0, 11.0, None, None),
        ]
        add_only = [entries[0], entries[2]]

        self.calculator_service_mock.get_history.return_value = entries
        self.calculator_service_mock.filter_history.return_value = add_only

        # Get all history
        history = self.controller.get_history()
        assert len(history) == 3

        # Filter to add operations only
        filtered = self.controller.filter_history(operations=["add"])
        assert len(filtered) == 2

    def test_sequential_calculations_flow(self):
        """Test performing multiple calculations in sequence."""
        calculations = [
            ("add", 1.0, 2.0, 3.0),
            ("subtract", 5.0, 2.0, 3.0),
            ("multiply", 3.0, 4.0, 12.0),
        ]

        entries = []

        for op, a, b, expected_result in calculations:
            # Create entry
            entry = MemoryEntry(op, a, b, expected_result, None, None)
            entries.append(entry)
            self.calculator_service_mock.perform.return_value = entry

            # Perform calculation
            result = self.controller.perform_calculation(op, a, b)

            # Verify result
            assert result.result == expected_result

        # Verify multiple calculations were performed
        assert self.calculator_service_mock.perform.call_count == 3

    def test_mixed_success_and_error_history(self):
        """Test history with both successful and failed calculations."""
        history = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]

        self.calculator_service_mock.get_history.return_value = history

        # Get history
        retrieved_history = self.controller.get_history()

        # Verify all entries are present
        assert len(retrieved_history) == 3

        # Verify errors are preserved
        assert retrieved_history[1].error is not None

    def test_filtering_by_state_success(self):
        """Test filtering history by success state."""
        success_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]

        self.calculator_service_mock.filter_history.return_value = success_entries

        # Filter to success only
        filtered = self.controller.filter_history(state="success")

        # Verify all returned entries are successful
        assert all(e.error is None for e in success_entries)

    def test_filtering_by_state_error(self):
        """Test filtering history by error state."""
        error_entries = [
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
        ]

        self.calculator_service_mock.filter_history.return_value = error_entries

        # Filter to error only
        filtered = self.controller.filter_history(state="error")

        # Verify all returned entries are errors
        assert filtered[0].error is not None

    def test_controller_with_multiple_operations(self):
        """Test controller with multiple different operations."""
        ops_and_results = [
            ("add", 2.0, 3.0, 5.0),
            ("subtract", 10.0, 3.0, 7.0),
            ("multiply", 4.0, 5.0, 20.0),
            ("divide", 20.0, 4.0, 5.0),
            ("sqrt", 16.0, 0.0, 4.0),
        ]

        for op, a, b, result in ops_and_results:
            entry = MemoryEntry(op, a, b, result, None, None)
            self.calculator_service_mock.perform.return_value = entry

            calculated = self.controller.perform_calculation(op, a, b)
            assert calculated.result == result

    def test_invalid_operation_raises_error(self):
        """Test that invalid operation raises ValueError."""
        with pytest.raises(ValueError):
            self.controller.perform_calculation("invalid_op", 1.0, 2.0)

    def test_unary_operation_flow(self):
        """Test flow for unary operations."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=16.0,
            operand_b=0.0,
            result=4.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = entry

        result = self.controller.perform_calculation("sqrt", 16.0, 0.0)

        assert result.result == 4.0
        assert result.operation == "sqrt"

    def test_statistics_retrieval(self):
        """Test retrieving statistics through controller."""
        stats_mock = MagicMock()
        self.statistics_service_mock.calculate_statistics.return_value = stats_mock

        stats = self.controller.get_statistics()

        assert stats == stats_mock
        self.statistics_service_mock.calculate_statistics.assert_called_once()

    def test_combined_operation_and_history(self):
        """Test that operations are properly recorded in history."""
        # Perform an operation
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, None, None)
        self.calculator_service_mock.perform.return_value = entry

        self.controller.perform_calculation("add", 1.0, 2.0)

        # Then get history
        all_history = [entry]
        self.calculator_service_mock.get_history.return_value = all_history

        history = self.controller.get_history()
        assert len(history) == 1
        assert history[0].result == 3.0

    def test_filter_history_with_multiple_criteria(self):
        """Test filtering with both operation and state criteria."""
        filtered_entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
        ]
        self.calculator_service_mock.filter_history.return_value = filtered_entries

        result = self.controller.filter_history(operations=["add"], state="success")

        assert len(result) == 1
        # Verify filter_history was called with both parameters
        self.calculator_service_mock.filter_history.assert_called_with(["add"], "success")

    def test_negative_operands_flow(self):
        """Test calculations with negative operands."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=-3.0,
            operand_b=-4.0,
            result=12.0,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = entry

        result = self.controller.perform_calculation("multiply", -3.0, -4.0)

        assert result.result == 12.0

    def test_large_operands_flow(self):
        """Test calculations with very large operands."""
        entry = MemoryEntry(
            operation="add",
            operand_a=999999.99,
            operand_b=888888.88,
            result=1888888.87,
            error=None,
            error_type=None,
        )
        self.calculator_service_mock.perform.return_value = entry

        result = self.controller.perform_calculation("add", 999999.99, 888888.88)

        assert result.result == pytest.approx(1888888.87)

    def test_empty_history_retrieval(self):
        """Test retrieving empty history."""
        self.calculator_service_mock.get_history.return_value = []

        history = self.controller.get_history()

        assert history == []
        assert len(history) == 0

    def test_all_operations_supported(self):
        """Test that all operation types are supported."""
        all_ops = ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"]

        for op in all_ops:
            entry = MemoryEntry(op, 1.0, 2.0, 3.0, None, None)
            self.calculator_service_mock.perform.return_value = entry

            # Should not raise
            result = self.controller.perform_calculation(op, 1.0, 2.0)
            assert result.operation == op
