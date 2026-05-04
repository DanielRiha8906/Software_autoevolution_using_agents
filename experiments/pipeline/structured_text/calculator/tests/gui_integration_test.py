"""
Integration tests for CalculatorGUI.

Tests the CalculatorGUI class covering:
- GUI initialization with/without memory service
- Operation button click handling
- Calculation execution and result display
- Memory display refresh
- Statistics display refresh
- Input validation
- Error handling
- Field clearing

Note: These tests use mocking to avoid requiring an X11 display.
The focus is on testing the logic and data flow, not tkinter rendering.
"""

import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch, Mock
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.models.memory_entry import MemoryEntry
from src.models.calculation_statistics import CalculationStatistics


@pytest.fixture
def mock_service():
    """Create a mock calculation service."""
    return MagicMock()


@pytest.fixture
def mock_memory_service():
    """Create a mock memory service with default return values."""
    service = MagicMock()
    service.retrieve_all.return_value = []
    service.compute_statistics.return_value = CalculationStatistics(
        operation_counts={},
        total_calculations=0,
        error_count=0,
        error_percentage=0.0,
        average_execution_time_ms=0.0,
        min_execution_time_ms=0.0,
        max_execution_time_ms=0.0,
        per_operation_stats={},
    )
    return service


@pytest.fixture
def create_gui_with_mocks():
    """Fixture to create a CalculatorGUI instance with all tkinter components mocked."""
    def _create_gui(service, memory_service=None):
        # Patch all tkinter components before importing CalculatorGUI
        with patch('tkinter.Tk.__init__', return_value=None), \
             patch('tkinter.Tk.title'), \
             patch('tkinter.Tk.geometry'), \
             patch('tkinter.Tk.columnconfigure'), \
             patch('tkinter.Tk.rowconfigure'), \
             patch('tkinter.ttk.Frame') as mock_frame_cls, \
             patch('tkinter.ttk.Label'), \
             patch('tkinter.ttk.Notebook') as mock_notebook_cls, \
             patch('tkinter.ttk.LabelFrame'), \
             patch('tkinter.ttk.Entry') as mock_entry_cls, \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.ttk.Scrollbar'), \
             patch('tkinter.Listbox') as mock_listbox_cls, \
             patch('tkinter.Text') as mock_text_cls, \
             patch('tkinter.StringVar') as mock_stringvar_cls:

            # Configure mocks
            mock_frame_inst = Mock()
            mock_frame_cls.return_value = mock_frame_inst

            mock_notebook_inst = Mock()
            mock_notebook_cls.return_value = mock_notebook_inst

            mock_entry_inst = Mock()
            mock_entry_cls.return_value = mock_entry_inst

            mock_listbox_inst = Mock()
            mock_listbox_inst.size.return_value = 0
            mock_listbox_cls.return_value = mock_listbox_inst

            mock_text_inst = Mock()
            mock_text_cls.return_value = mock_text_inst

            # StringVar mock that actually stores values
            def create_stringvar(value=None):
                var = Mock()
                var._value = value or ""
                var.get = Mock(side_effect=lambda: var._value)
                var.set = Mock(side_effect=lambda v: setattr(var, '_value', v))
                return var

            mock_stringvar_cls.side_effect = create_stringvar

            # Import and create GUI
            from src.gui.calculator_gui import CalculatorGUI
            gui = CalculatorGUI(service, memory_service)

            # Store mock references for inspection
            gui._mock_listbox = mock_listbox_inst
            gui._mock_text = mock_text_inst
            gui._mock_entry = mock_entry_inst

            return gui

    return _create_gui


class TestCalculatorGUIInit:
    """Test CalculatorGUI.__init__() and initialization."""

    def test_init_with_calculation_service_only(self, mock_service, create_gui_with_mocks):
        """Test GUI initialization with only calculation service."""
        gui = create_gui_with_mocks(mock_service)
        assert gui.service == mock_service
        assert gui.memory_service is None
        assert gui._current_operation is None

    def test_init_with_both_services(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test GUI initialization with both calculation and memory services."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        assert gui.service == mock_service
        assert gui.memory_service == mock_memory_service

    def test_init_calls_refresh_when_memory_service_provided(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that __init__ calls refresh methods if memory_service provided."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        # If memory service was provided, refresh methods should have been called during __init__
        assert mock_memory_service.retrieve_all.called
        assert mock_memory_service.compute_statistics.called

    def test_init_without_memory_service_safe(self, mock_service, create_gui_with_mocks):
        """Test that __init__ handles no memory_service gracefully."""
        gui = create_gui_with_mocks(mock_service)
        assert gui.memory_service is None


class TestWidgetCreation:
    """Test _create_widgets() and related methods."""

    def test_operand_entry_variables_created(self, mock_service, create_gui_with_mocks):
        """Test that operand entry variables are created."""
        gui = create_gui_with_mocks(mock_service)
        # StringVar mocks should exist
        assert hasattr(gui, '_operand_a_var')
        assert hasattr(gui, '_operand_b_var')
        assert hasattr(gui, '_operand_a_entry')
        assert hasattr(gui, '_operand_b_entry')

    def test_result_display_created(self, mock_service, create_gui_with_mocks):
        """Test that result display is created."""
        gui = create_gui_with_mocks(mock_service)
        assert hasattr(gui, '_result_var')

    def test_memory_listbox_created(self, mock_service, create_gui_with_mocks):
        """Test that memory listbox is created."""
        gui = create_gui_with_mocks(mock_service)
        assert hasattr(gui, '_memory_listbox')

    def test_stats_text_only_with_memory_service(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that stats text widget only created if memory_service provided."""
        # Without memory service
        gui_no_mem = create_gui_with_mocks(mock_service)
        # Check directly in __dict__ to avoid recursion issues with Tk attribute lookups
        assert '_stats_text' not in gui_no_mem.__dict__

        # With memory service
        gui_with_mem = create_gui_with_mocks(mock_service, mock_memory_service)
        assert '_stats_text' in gui_with_mem.__dict__


class TestOperationConstants:
    """Test operation constant definitions."""

    def test_standard_operations_defined(self, mock_service, create_gui_with_mocks):
        """Test that standard operations list is properly defined."""
        gui = create_gui_with_mocks(mock_service)
        assert len(gui._STANDARD_OPS) == 8
        assert Operation.ADD in gui._STANDARD_OPS
        assert Operation.SUBTRACT in gui._STANDARD_OPS
        assert Operation.MULTIPLY in gui._STANDARD_OPS
        assert Operation.DIVIDE in gui._STANDARD_OPS
        assert Operation.SQUARE in gui._STANDARD_OPS
        assert Operation.SQRT in gui._STANDARD_OPS
        assert Operation.POWER in gui._STANDARD_OPS
        assert Operation.MODULO in gui._STANDARD_OPS

    def test_scientific_operations_defined(self, mock_service, create_gui_with_mocks):
        """Test that scientific operations list is properly defined."""
        gui = create_gui_with_mocks(mock_service)
        assert len(gui._SCIENTIFIC_OPS) == 6
        assert Operation.SIN in gui._SCIENTIFIC_OPS
        assert Operation.COS in gui._SCIENTIFIC_OPS
        assert Operation.TAN in gui._SCIENTIFIC_OPS
        assert Operation.LOG in gui._SCIENTIFIC_OPS
        assert Operation.LN in gui._SCIENTIFIC_OPS
        assert Operation.EXP in gui._SCIENTIFIC_OPS

    @pytest.mark.parametrize("operation", [
        Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE,
        Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO,
        Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP,
    ])
    def test_all_operations_have_display_names(self, operation):
        """Test that all operations have valid display names."""
        display_name = operation.display_name()
        assert isinstance(display_name, str)
        assert len(display_name) > 0


class TestOperationButtonClick:
    """Test _on_operation_button_click() method."""

    def test_operation_button_click_sets_current_operation(self, mock_service, create_gui_with_mocks):
        """Test that clicking operation sets _current_operation."""
        gui = create_gui_with_mocks(mock_service)
        gui._on_operation_button_click(Operation.ADD)
        assert gui._current_operation == Operation.ADD

    def test_operation_button_click_updates_result_display(self, mock_service, create_gui_with_mocks):
        """Test that operation button click updates result display."""
        gui = create_gui_with_mocks(mock_service)
        gui._on_operation_button_click(Operation.MULTIPLY)
        result_text = gui._result_var.get()
        assert "Multiply" in result_text
        assert "selected" in result_text.lower()
        assert "Calculate" in result_text

    @pytest.mark.parametrize("operation", [
        Operation.ADD, Operation.DIVIDE, Operation.SIN, Operation.LOG,
    ])
    def test_operation_button_click_various_operations(self, mock_service, create_gui_with_mocks, operation):
        """Test operation button click with various operations."""
        gui = create_gui_with_mocks(mock_service)
        gui._on_operation_button_click(operation)
        assert gui._current_operation == operation
        assert operation.display_name() in gui._result_var.get()


class TestCalculateButtonClick:
    """Test _on_calculate_button_click() method."""

    def test_calculate_without_operation_shows_warning(self, mock_service, create_gui_with_mocks):
        """Test that Calculate without operation shows warning."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("5")
        gui._operand_b_var.set("3")
        gui._current_operation = None

        with patch('tkinter.messagebox.showwarning') as mock_warn:
            gui._on_calculate_button_click()
            mock_warn.assert_called_once()
            assert "No Operation" in mock_warn.call_args[0][0]

    def test_calculate_with_invalid_operand_a(self, mock_service, create_gui_with_mocks):
        """Test that non-numeric Operand A shows error."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("not_a_number")
        gui._operand_b_var.set("5")
        gui._on_operation_button_click(Operation.ADD)

        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._on_calculate_button_click()
            mock_error.assert_called_once()
            assert "Invalid Input" in mock_error.call_args[0][0]
            assert "Operand A" in mock_error.call_args[0][1]

    def test_calculate_with_invalid_operand_b(self, mock_service, create_gui_with_mocks):
        """Test that non-numeric Operand B shows error."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("5")
        gui._operand_b_var.set("invalid")
        gui._on_operation_button_click(Operation.ADD)

        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._on_calculate_button_click()
            mock_error.assert_called_once()
            assert "Invalid Input" in mock_error.call_args[0][0]
            assert "Operand B" in mock_error.call_args[0][1]

    def test_calculate_with_empty_operand_a(self, mock_service, create_gui_with_mocks):
        """Test that empty Operand A shows error."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("")
        gui._operand_b_var.set("5")
        gui._on_operation_button_click(Operation.ADD)

        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._on_calculate_button_click()
            mock_error.assert_called_once()

    def test_calculate_with_valid_inputs_calls_execute(self, mock_service, create_gui_with_mocks):
        """Test that Calculate with valid inputs calls _execute_calculation."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("5")
        gui._operand_b_var.set("3")
        gui._on_operation_button_click(Operation.ADD)

        with patch.object(gui, '_execute_calculation') as mock_execute:
            gui._on_calculate_button_click()
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0]
            assert call_args[0] == Operation.ADD
            assert call_args[1] == 5.0
            assert call_args[2] == 3.0


class TestExecuteCalculation:
    """Test _execute_calculation() method."""

    def test_execute_calculation_success_no_memory_service(self, mock_service, create_gui_with_mocks):
        """Test successful calculation without memory service."""
        mock_result = CalculationResult("add", 5, 3, 8, "", 1.5)
        mock_service.perform.return_value = mock_result

        gui = create_gui_with_mocks(mock_service)
        gui._execute_calculation(Operation.ADD, 5, 3)

        mock_service.perform.assert_called_once_with(Operation.ADD, 5, 3)
        assert "8" in gui._result_var.get()

    def test_execute_calculation_success_with_memory(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test successful calculation with memory service."""
        mock_result = CalculationResult("add", 5, 3, 8, "", 1.5)
        mock_service.perform.return_value = mock_result

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._execute_calculation(Operation.ADD, 5, 3)

        # Should store in memory
        assert mock_memory_service.store.called
        stored_entry = mock_memory_service.store.call_args[0][0]
        assert isinstance(stored_entry, MemoryEntry)
        assert stored_entry.operation == "add"
        assert stored_entry.operand_a == 5
        assert stored_entry.operand_b == 3
        assert stored_entry.result == 8
        assert stored_entry.success is True

    def test_execute_calculation_with_value_error(self, mock_service, create_gui_with_mocks):
        """Test calculation that raises ValueError."""
        mock_service.perform.side_effect = ValueError("Division by zero")

        gui = create_gui_with_mocks(mock_service)

        with patch.object(gui, '_show_error') as mock_show_error:
            gui._execute_calculation(Operation.DIVIDE, 5, 0)
            mock_show_error.assert_called_once()
            assert "Division by zero" in mock_show_error.call_args[0][0]

    def test_execute_calculation_execution_time_captured(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that execution time is captured in memory entry."""
        mock_result = CalculationResult("multiply", 3, 4, 12, "", 2.5)
        mock_service.perform.return_value = mock_result

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._execute_calculation(Operation.MULTIPLY, 3, 4)

        stored_entry = mock_memory_service.store.call_args[0][0]
        assert stored_entry.execution_time_ms == 2.5


class TestDisplayResult:
    """Test _display_result() method."""

    def test_display_result_formats_integers(self, mock_service, create_gui_with_mocks):
        """Test that integer results are displayed without decimals."""
        gui = create_gui_with_mocks(mock_service)
        result = CalculationResult("add", 5.0, 3.0, 8.0, "", 1.5)
        gui._display_result(result)

        result_text = gui._result_var.get()
        assert "8" in result_text
        # Only one decimal point for the ms value
        assert result_text.count(".") == 1

    def test_display_result_formats_floats(self, mock_service, create_gui_with_mocks):
        """Test that float results display with decimals."""
        gui = create_gui_with_mocks(mock_service)
        result = CalculationResult("divide", 5.0, 2.0, 2.5, "", 1.5)
        gui._display_result(result)

        result_text = gui._result_var.get()
        assert "2.5" in result_text

    def test_display_result_includes_operation_name(self, mock_service, create_gui_with_mocks):
        """Test that result includes operation name."""
        gui = create_gui_with_mocks(mock_service)
        result = CalculationResult("sqrt", 4.0, 0.0, 2.0, "", 0.5)
        gui._display_result(result)

        result_text = gui._result_var.get()
        assert "SQRT" in result_text or "sqrt" in result_text.lower()

    def test_display_result_includes_execution_time(self, mock_service, create_gui_with_mocks):
        """Test that result includes execution time."""
        gui = create_gui_with_mocks(mock_service)
        result = CalculationResult("add", 1.0, 1.0, 2.0, "", 0.75)
        gui._display_result(result)

        result_text = gui._result_var.get()
        assert "0.75ms" in result_text


class TestRefreshMemoryDisplay:
    """Test _refresh_memory_display() method."""

    def test_refresh_memory_display_clears_listbox(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that refresh clears the listbox."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_memory_display()

        gui._memory_listbox.delete.assert_called_with(0, tk.END)

    def test_refresh_memory_display_with_entries(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test memory display refresh with entries."""
        entry = MemoryEntry(
            operation="add", operand_a=5.0, operand_b=3.0, result=8.0,
            success=True, error_message=None, execution_timestamp="", execution_time_ms=1.5
        )
        mock_memory_service.retrieve_all.return_value = [entry]

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_memory_display()

        # Should insert entries
        assert gui._memory_listbox.insert.called

    def test_refresh_memory_display_without_memory_service(self, mock_service, create_gui_with_mocks):
        """Test that refresh is safe without memory service."""
        gui = create_gui_with_mocks(mock_service)
        # Should not raise
        gui._refresh_memory_display()

    def test_refresh_memory_display_scrolls_to_bottom(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that listbox scrolls to bottom after refresh."""
        entries = [
            MemoryEntry("add", 5.0, 3.0, 8.0, True, None, "", 1.5),
            MemoryEntry("multiply", 2.0, 4.0, 8.0, True, None, "", 0.8),
        ]
        mock_memory_service.retrieve_all.return_value = entries

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_memory_display()

        # Should call see(tk.END) to scroll
        assert gui._memory_listbox.see.called


class TestRefreshStatisticsDisplay:
    """Test _refresh_statistics_display() method."""

    def test_refresh_statistics_updates_text_widget(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that statistics refresh updates the text widget."""
        stats = CalculationStatistics(
            operation_counts={}, total_calculations=0, error_count=0,
            error_percentage=0.0, average_execution_time_ms=0.0,
            min_execution_time_ms=0.0, max_execution_time_ms=0.0,
            per_operation_stats={},
        )
        mock_memory_service.compute_statistics.return_value = stats

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_statistics_display()

        # Should update text widget
        assert gui._stats_text.delete.called
        assert gui._stats_text.insert.called

    def test_refresh_statistics_displays_totals(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that statistics display includes totals."""
        stats = CalculationStatistics(
            operation_counts={"add": 5, "multiply": 3}, total_calculations=8,
            error_count=0, error_percentage=0.0, average_execution_time_ms=1.2,
            min_execution_time_ms=0.5, max_execution_time_ms=2.1, per_operation_stats={},
        )
        mock_memory_service.compute_statistics.return_value = stats

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_statistics_display()

        call_args = gui._stats_text.insert.call_args[0]
        stats_text = call_args[1]
        assert "8" in stats_text  # Total: 8

    def test_refresh_statistics_displays_error_info(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that statistics display includes error info."""
        stats = CalculationStatistics(
            operation_counts={"divide": 10}, total_calculations=10, error_count=2,
            error_percentage=20.0, average_execution_time_ms=1.0,
            min_execution_time_ms=0.5, max_execution_time_ms=2.0, per_operation_stats={},
        )
        mock_memory_service.compute_statistics.return_value = stats

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_statistics_display()

        call_args = gui._stats_text.insert.call_args[0]
        stats_text = call_args[1]
        assert "2" in stats_text  # Error count
        assert "20.00" in stats_text  # Error percentage

    def test_refresh_statistics_displays_timing_metrics(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that statistics display includes timing metrics."""
        stats = CalculationStatistics(
            operation_counts={"add": 5}, total_calculations=5, error_count=0,
            error_percentage=0.0, average_execution_time_ms=1.25,
            min_execution_time_ms=0.75, max_execution_time_ms=2.50, per_operation_stats={},
        )
        mock_memory_service.compute_statistics.return_value = stats

        gui = create_gui_with_mocks(mock_service, mock_memory_service)
        gui._refresh_statistics_display()

        call_args = gui._stats_text.insert.call_args[0]
        stats_text = call_args[1]
        assert "1.25" in stats_text
        assert "0.75" in stats_text
        assert "2.50" in stats_text

    def test_refresh_statistics_without_memory_service(self, mock_service, create_gui_with_mocks):
        """Test that refresh is safe without memory service."""
        gui = create_gui_with_mocks(mock_service)
        # Should not raise
        gui._refresh_statistics_display()


class TestShowError:
    """Test _show_error() method."""

    def test_show_error_displays_dialog(self, mock_service, create_gui_with_mocks):
        """Test that _show_error shows error message box."""
        gui = create_gui_with_mocks(mock_service)

        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._show_error("Test error message")
            mock_error.assert_called_once()
            assert "Calculation Error" in mock_error.call_args[0][0]
            assert "Test error message" in mock_error.call_args[0][1]

    def test_show_error_updates_result_display(self, mock_service, create_gui_with_mocks):
        """Test that _show_error updates result display."""
        gui = create_gui_with_mocks(mock_service)

        with patch('tkinter.messagebox.showerror'):
            gui._show_error("Division by zero")

        result_text = gui._result_var.get()
        assert "Error" in result_text


class TestClearFields:
    """Test _on_clear_fields() method."""

    def test_clear_fields_clears_operand_a(self, mock_service, create_gui_with_mocks):
        """Test that clear fields clears Operand A."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_a_var.set("5")
        gui._on_clear_fields()
        assert gui._operand_a_var.get() == ""

    def test_clear_fields_clears_operand_b(self, mock_service, create_gui_with_mocks):
        """Test that clear fields clears Operand B."""
        gui = create_gui_with_mocks(mock_service)
        gui._operand_b_var.set("3")
        gui._on_clear_fields()
        assert gui._operand_b_var.get() == ""

    def test_clear_fields_resets_result_display(self, mock_service, create_gui_with_mocks):
        """Test that clear fields resets result display."""
        gui = create_gui_with_mocks(mock_service)
        gui._result_var.set("Some result")
        gui._on_clear_fields()
        assert "Enter operands" in gui._result_var.get()

    def test_clear_fields_clears_current_operation(self, mock_service, create_gui_with_mocks):
        """Test that clear fields clears current operation."""
        gui = create_gui_with_mocks(mock_service)
        gui._on_operation_button_click(Operation.ADD)
        gui._on_clear_fields()
        assert gui._current_operation is None

    def test_clear_fields_focuses_entry(self, mock_service, create_gui_with_mocks):
        """Test that clear fields focuses on Operand A entry."""
        gui = create_gui_with_mocks(mock_service)
        gui._on_clear_fields()
        assert gui._operand_a_entry.focus.called


class TestClearMemory:
    """Test _on_clear_memory() method."""

    def test_clear_memory_without_memory_service(self, mock_service, create_gui_with_mocks):
        """Test that clear memory is safe without memory service."""
        gui = create_gui_with_mocks(mock_service)
        # Should not raise
        gui._on_clear_memory()

    def test_clear_memory_prompts_user(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that clear memory prompts user for confirmation."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)

        with patch('tkinter.messagebox.askyesno', return_value=False) as mock_askyesno:
            gui._on_clear_memory()
            mock_askyesno.assert_called_once()
            assert "Clear Memory" in mock_askyesno.call_args[0][0]

    def test_clear_memory_shows_message_when_confirmed(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that clear memory shows info message when confirmed."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)

        with patch('tkinter.messagebox.askyesno', return_value=True):
            with patch('tkinter.messagebox.showinfo') as mock_info:
                gui._on_clear_memory()
                mock_info.assert_called_once()

    def test_clear_memory_no_message_when_cancelled(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test that clear memory doesn't show message when cancelled."""
        gui = create_gui_with_mocks(mock_service, mock_memory_service)

        with patch('tkinter.messagebox.askyesno', return_value=False):
            with patch('tkinter.messagebox.showinfo') as mock_info:
                gui._on_clear_memory()
                mock_info.assert_not_called()


class TestRun:
    """Test run() method."""

    def test_run_starts_mainloop(self, mock_service, create_gui_with_mocks):
        """Test that run() starts the mainloop."""
        gui = create_gui_with_mocks(mock_service)

        with patch.object(gui, 'mainloop') as mock_mainloop:
            gui.run()
            mock_mainloop.assert_called_once()


class TestIntegrationFlow:
    """Integration tests for complete workflows."""

    def test_complete_calculation_flow_with_memory(self, mock_service, mock_memory_service, create_gui_with_mocks):
        """Test complete flow: select operation, enter operands, calculate."""
        calc_result = CalculationResult("add", 10.0, 5.0, 15.0, "", 1.2)
        mock_service.perform.return_value = calc_result

        mock_memory_service.retrieve_all.side_effect = [
            [],
            [MemoryEntry("add", 10.0, 5.0, 15.0, True, None, "", 1.2)]
        ]

        gui = create_gui_with_mocks(mock_service, mock_memory_service)

        # Select operation
        gui._on_operation_button_click(Operation.ADD)
        assert gui._current_operation == Operation.ADD

        # Enter operands
        gui._operand_a_var.set("10")
        gui._operand_b_var.set("5")

        # Click calculate
        gui._on_calculate_button_click()

        # Verify service called and memory stored
        mock_service.perform.assert_called_once_with(Operation.ADD, 10.0, 5.0)
        assert mock_memory_service.store.called

    def test_error_handling_flow(self, mock_service, create_gui_with_mocks):
        """Test error handling workflow."""
        mock_service.perform.side_effect = ValueError("Invalid operation")

        gui = create_gui_with_mocks(mock_service)

        gui._on_operation_button_click(Operation.DIVIDE)
        gui._operand_a_var.set("10")
        gui._operand_b_var.set("0")

        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._on_calculate_button_click()
            assert mock_error.called
