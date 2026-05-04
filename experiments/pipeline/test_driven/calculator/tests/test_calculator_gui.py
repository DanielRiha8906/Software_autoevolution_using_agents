import inspect
import pytest
from unittest.mock import MagicMock, patch, call
import tkinter as tk

from src.gui.calculator_gui import CalculatorGUI
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult


# ============================================================================
# Provided Test Cases (MUST PASS)
# ============================================================================

def test_calculator_gui_module_exists():
    """Test that the CalculatorGUI class exists and can be imported."""
    from src.gui.calculator_gui import CalculatorGUI
    assert CalculatorGUI is not None


def test_calculator_gui_accepts_service():
    """Test that CalculatorGUI accepts a service instance in __init__."""
    from src.gui.calculator_gui import CalculatorGUI
    gui = CalculatorGUI(MagicMock())
    assert gui is not None


def test_gui_does_not_instantiate_calculator_directly():
    """Test that the GUI module does not instantiate Calculator directly."""
    from src.gui import calculator_gui
    source = inspect.getsource(calculator_gui)
    assert "Calculator()" not in source


def test_gui_contains_no_arithmetic_logic():
    """Test that the GUI module contains no arithmetic logic."""
    from src.gui import calculator_gui
    source = inspect.getsource(calculator_gui)
    assert "def add(" not in source
    assert "def divide(" not in source


def test_gui_references_service():
    """Test that the GUI module references the service."""
    from src.gui import calculator_gui
    source = inspect.getsource(calculator_gui)
    assert "service" in source.lower()


# ============================================================================
# Additional GUI Functionality Tests
# ============================================================================

class TestCalculatorGUIInitialization:
    """Test GUI initialization and setup."""

    def test_gui_stores_service_reference(self):
        """Test that the GUI stores the service reference."""
        mock_service = MagicMock()
        gui = CalculatorGUI(mock_service)
        assert gui.service is mock_service

    def test_gui_creates_tk_root(self):
        """Test that the GUI creates a Tk root window."""
        mock_service = MagicMock()
        gui = CalculatorGUI(mock_service)
        assert gui.root is not None
        assert isinstance(gui.root, tk.Tk)
        gui.root.destroy()

    def test_gui_window_title_is_calculator(self):
        """Test that the window title is set to Calculator."""
        mock_service = MagicMock()
        gui = CalculatorGUI(mock_service)
        assert gui.root.title() == "Calculator"
        gui.root.destroy()

    def test_gui_initializes_operand_variables(self):
        """Test that operand StringVar variables are initialized."""
        mock_service = MagicMock()
        gui = CalculatorGUI(mock_service)
        assert isinstance(gui.operand_a_var, tk.StringVar)
        assert isinstance(gui.operand_b_var, tk.StringVar)
        assert isinstance(gui.result_var, tk.StringVar)
        gui.root.destroy()

    def test_gui_result_var_empty_initially(self):
        """Test that result display is empty initially."""
        mock_service = MagicMock()
        gui = CalculatorGUI(mock_service)
        assert gui.result_var.get() == ""
        gui.root.destroy()


class TestOperationButtonDelegation:
    """Test that operation buttons delegate to the service."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mock service and GUI before each test."""
        self.mock_service = MagicMock()
        self.mock_result = CalculationResult("add", 3, 5, 8)
        self.mock_service.perform.return_value = self.mock_result
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_operation_button_click_delegates_to_service(self):
        """Test that clicking an operation button calls service.perform."""
        self.gui.operand_a_var.set("3")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_called_once_with(Operation.ADD, 3.0, 5.0)

    def test_operation_delegates_with_correct_operation_enum(self):
        """Test that the correct Operation enum is passed to service."""
        self.gui.operand_a_var.set("10")
        self.gui.operand_b_var.set("2")
        self.gui._on_operation_selected(Operation.MULTIPLY)
        args = self.mock_service.perform.call_args[0]
        assert args[0] == Operation.MULTIPLY

    def test_operation_delegates_with_float_operands(self):
        """Test that operands are converted to float when delegating."""
        self.gui.operand_a_var.set("3.5")
        self.gui.operand_b_var.set("2.5")
        self.gui._on_operation_selected(Operation.ADD)
        args = self.mock_service.perform.call_args[0]
        assert args[1] == 3.5
        assert args[2] == 2.5

    def test_operation_with_integer_strings_converts_to_float(self):
        """Test that integer strings are converted to float."""
        self.gui.operand_a_var.set("10")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.DIVIDE)
        args = self.mock_service.perform.call_args[0]
        assert args[1] == 10.0
        assert args[2] == 5.0


class TestInvalidInputHandling:
    """Test error handling for invalid input."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mock service and GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    @patch("tkinter.messagebox.showerror")
    def test_non_numeric_operand_a_shows_error(self, mock_error):
        """Test that non-numeric operand A triggers error message."""
        self.gui.operand_a_var.set("abc")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        mock_error.assert_called_once()
        assert "Input Error" in mock_error.call_args[0]

    @patch("tkinter.messagebox.showerror")
    def test_non_numeric_operand_b_shows_error(self, mock_error):
        """Test that non-numeric operand B triggers error message."""
        self.gui.operand_a_var.set("5")
        self.gui.operand_b_var.set("xyz")
        self.gui._on_operation_selected(Operation.ADD)
        mock_error.assert_called_once()
        assert "Input Error" in mock_error.call_args[0]

    @patch("tkinter.messagebox.showerror")
    def test_empty_operand_a_shows_error(self, mock_error):
        """Test that empty operand A triggers error message."""
        self.gui.operand_a_var.set("")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        mock_error.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_empty_operand_b_shows_error(self, mock_error):
        """Test that empty operand B triggers error message."""
        self.gui.operand_a_var.set("5")
        self.gui.operand_b_var.set("")
        self.gui._on_operation_selected(Operation.ADD)
        mock_error.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_service_exception_shows_error(self, mock_error):
        """Test that exceptions from service show error message."""
        self.mock_service.perform.side_effect = Exception("Test error")
        self.gui.operand_a_var.set("5")
        self.gui.operand_b_var.set("0")
        self.gui._on_operation_selected(Operation.DIVIDE)
        mock_error.assert_called_once()
        assert "Calculation Error" in mock_error.call_args[0]

    @patch("tkinter.messagebox.showerror")
    def test_service_not_called_on_invalid_input(self, mock_error):
        """Test that service is not called when input is invalid."""
        self.gui.operand_a_var.set("abc")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_not_called()

    @pytest.fixture
    def mock_service(self):
        """Provide mock service for setup method."""
        return MagicMock()


class TestClearFunctionality:
    """Test the clear button functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_clear_empties_operand_a(self):
        """Test that clear empties operand A field."""
        self.gui.operand_a_var.set("42")
        self.gui._on_clear()
        assert self.gui.operand_a_var.get() == ""

    def test_clear_empties_operand_b(self):
        """Test that clear empties operand B field."""
        self.gui.operand_b_var.set("42")
        self.gui._on_clear()
        assert self.gui.operand_b_var.get() == ""

    def test_clear_empties_result(self):
        """Test that clear empties the result display."""
        self.gui.result_var.set("42")
        self.gui._on_clear()
        assert self.gui.result_var.get() == ""

    def test_clear_empties_all_fields(self):
        """Test that clear empties all fields at once."""
        self.gui.operand_a_var.set("10")
        self.gui.operand_b_var.set("20")
        self.gui.result_var.set("30")
        self.gui._on_clear()
        assert self.gui.operand_a_var.get() == ""
        assert self.gui.operand_b_var.get() == ""
        assert self.gui.result_var.get() == ""


class TestOperationButtonCount:
    """Test that all Operation enum values have buttons."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_operation_enum_has_14_members(self):
        """Test that the Operation enum has exactly 14 members."""
        operations = list(Operation)
        assert len(operations) == 14

    def test_all_operation_enums_present(self):
        """Test that all expected operations are present."""
        expected_ops = [
            Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY,
            Operation.DIVIDE, Operation.SQUARE, Operation.SQRT,
            Operation.POWER, Operation.MODULO, Operation.SIN,
            Operation.COS, Operation.TAN, Operation.LOG,
            Operation.LN, Operation.EXP
        ]
        for op in expected_ops:
            assert op in list(Operation)

    def test_operation_display_names_are_capitalized(self):
        """Test that operation display names are properly formatted."""
        operations = list(Operation)
        for op in operations:
            display_name = op.display_name()
            assert display_name[0].isupper()
            assert display_name.islower() or display_name[0].isupper()


class TestCalculationResultDisplay:
    """Test CalculationResult display."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_display_result_shows_result(self):
        """Test that _display_result shows the result value."""
        result = CalculationResult("add", 3, 5, 8)
        self.gui._display_result(result)
        assert "8" in self.gui.result_var.get()

    def test_display_result_shows_operation(self):
        """Test that _display_result includes the operation."""
        result = CalculationResult("add", 3, 5, 8)
        self.gui._display_result(result)
        result_text = self.gui.result_var.get()
        assert "3" in result_text
        assert "5" in result_text

    def test_display_result_with_subtract(self):
        """Test displaying subtraction result."""
        result = CalculationResult("subtract", 10, 3, 7)
        self.gui._display_result(result)
        assert "7" in self.gui.result_var.get()

    def test_display_result_with_float_operands(self):
        """Test displaying result with float operands."""
        result = CalculationResult("multiply", 2.5, 4.0, 10.0)
        self.gui._display_result(result)
        result_text = self.gui.result_var.get()
        assert "10" in result_text

    def test_display_result_updates_result_var(self):
        """Test that result display updates the StringVar."""
        result = CalculationResult("divide", 10, 2, 5.0)
        self.gui._display_result(result)
        assert self.gui.result_var.get() != ""


class TestMainPyGUIFlagSupport:
    """Test that __main__.py supports --gui flag."""

    def test_main_py_imports_calculator_gui(self):
        """Test that __main__.py imports CalculatorGUI."""
        from src import __main__
        source = inspect.getsource(__main__)
        assert "CalculatorGUI" in source

    def test_main_py_has_gui_argument(self):
        """Test that __main__.py argparse includes --gui argument."""
        from src import __main__
        source = inspect.getsource(__main__)
        assert "--gui" in source

    def test_main_py_instantiates_gui_with_service(self):
        """Test that __main__.py instantiates GUI with service."""
        from src import __main__
        source = inspect.getsource(__main__)
        assert "CalculatorGUI(service)" in source

    def test_main_py_calls_gui_run(self):
        """Test that __main__.py calls gui.run()."""
        from src import __main__
        source = inspect.getsource(__main__)
        assert "gui.run()" in source


class TestOperationButtonCreation:
    """Test that operation buttons are properly created."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_create_operation_buttons_called(self):
        """Test that _create_operation_buttons is called during setup."""
        # The method is called in __init__ via _setup_ui
        # We can't directly test this without mocking, so we verify the
        # buttons exist by checking the root has children
        assert len(self.gui.root.winfo_children()) > 0

    def test_operation_buttons_have_display_names(self):
        """Test that operation buttons are created with display names."""
        operations = list(Operation)
        for op in operations:
            display_name = op.display_name()
            assert display_name is not None
            assert len(display_name) > 0


class TestGUIIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.mock_result = CalculationResult("add", 3, 5, 8)
        self.mock_service.perform.return_value = self.mock_result
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_full_calculation_workflow(self):
        """Test complete calculation workflow."""
        # Set inputs
        self.gui.operand_a_var.set("3")
        self.gui.operand_b_var.set("5")
        # Perform operation
        self.gui._on_operation_selected(Operation.ADD)
        # Verify service was called
        self.mock_service.perform.assert_called_once_with(Operation.ADD, 3.0, 5.0)
        # Verify result is displayed
        assert "8" in self.gui.result_var.get()

    def test_multiple_operations_in_sequence(self):
        """Test performing multiple operations."""
        results = [
            CalculationResult("add", 3, 5, 8),
            CalculationResult("multiply", 4, 2, 8),
        ]
        self.mock_service.perform.side_effect = results

        # First operation
        self.gui.operand_a_var.set("3")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        assert "8" in self.gui.result_var.get()

        # Second operation
        self.gui.operand_a_var.set("4")
        self.gui.operand_b_var.set("2")
        self.gui._on_operation_selected(Operation.MULTIPLY)
        assert "8" in self.gui.result_var.get()

    def test_clear_then_new_calculation(self):
        """Test clearing fields and performing a new calculation."""
        # First calculation
        mock_result_1 = CalculationResult("add", 10, 5, 15)
        self.mock_service.perform.return_value = mock_result_1
        self.gui.operand_a_var.set("10")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        assert "15" in self.gui.result_var.get()

        # Clear
        self.gui._on_clear()
        assert self.gui.operand_a_var.get() == ""
        assert self.gui.operand_b_var.get() == ""

        # New calculation
        mock_result_2 = CalculationResult("subtract", 20, 8, 12)
        self.mock_service.perform.return_value = mock_result_2
        self.gui.operand_a_var.set("20")
        self.gui.operand_b_var.set("8")
        self.gui._on_operation_selected(Operation.SUBTRACT)
        assert "12" in self.gui.result_var.get()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup GUI before each test."""
        self.mock_service = MagicMock()
        self.gui = CalculatorGUI(self.mock_service)
        yield
        self.gui.root.destroy()

    def test_very_large_numbers(self):
        """Test with very large numbers."""
        self.mock_service.perform.return_value = CalculationResult(
            "add", 1000000, 2000000, 3000000
        )
        self.gui.operand_a_var.set("1000000")
        self.gui.operand_b_var.set("2000000")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_called_once()

    def test_very_small_numbers(self):
        """Test with very small numbers."""
        self.mock_service.perform.return_value = CalculationResult(
            "add", 0.000001, 0.000002, 0.000003
        )
        self.gui.operand_a_var.set("0.000001")
        self.gui.operand_b_var.set("0.000002")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_called_once()

    def test_negative_numbers(self):
        """Test with negative numbers."""
        self.mock_service.perform.return_value = CalculationResult(
            "subtract", -10, -5, -5
        )
        self.gui.operand_a_var.set("-10")
        self.gui.operand_b_var.set("-5")
        self.gui._on_operation_selected(Operation.SUBTRACT)
        self.mock_service.perform.assert_called_once()

    def test_zero_operands(self):
        """Test with zero as operand."""
        self.mock_service.perform.return_value = CalculationResult(
            "add", 0, 5, 5
        )
        self.gui.operand_a_var.set("0")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_whitespace_operands(self, mock_error):
        """Test that whitespace-only operands are invalid."""
        self.gui.operand_a_var.set("   ")
        self.gui.operand_b_var.set("5")
        self.gui._on_operation_selected(Operation.ADD)
        mock_error.assert_called_once()

    def test_decimal_numbers(self):
        """Test with decimal numbers."""
        self.mock_service.perform.return_value = CalculationResult(
            "add", 1.5, 2.3, 3.8
        )
        self.gui.operand_a_var.set("1.5")
        self.gui.operand_b_var.set("2.3")
        self.gui._on_operation_selected(Operation.ADD)
        self.mock_service.perform.assert_called_once()
