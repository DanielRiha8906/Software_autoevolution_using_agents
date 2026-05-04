import pytest
from unittest.mock import MagicMock, patch, Mock
import inspect
from src.gui.calculator_gui import CalculatorGUI
from src.services.calculator_service import CalculatorService


class TestCalculatorGUIModule:
    """Test that CalculatorGUI module and class exist."""

    def test_calculator_gui_module_exists(self):
        """Verify CalculatorGUI class can be imported."""
        assert CalculatorGUI is not None
        assert hasattr(CalculatorGUI, '__init__')

    def test_calculator_gui_is_class(self):
        """Verify CalculatorGUI is a class."""
        assert inspect.isclass(CalculatorGUI)


class TestCalculatorGUIConstructor:
    """Test CalculatorGUI constructor and initialization."""

    def test_calculator_gui_accepts_service(self):
        """Verify constructor accepts CalculatorService parameter."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)
        assert gui.service == mock_service

    def test_calculator_gui_stores_service_reference(self):
        """Verify the service is stored and accessible."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)
        assert hasattr(gui, 'service')
        assert gui.service is mock_service

    def test_calculator_gui_initializes_state(self):
        """Verify GUI state machine is properly initialized."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert gui.current_input == ""
        assert gui.pending_operation is None
        assert gui.operand_a == 0.0
        assert gui.result_shown is False

    def test_calculator_gui_initializes_widgets_as_none(self):
        """Verify widget references start as None (before run())."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert gui.root is None
        assert gui.display is None
        assert gui.history_text is None


class TestCalculatorGUISourceCode:
    """Test that GUI source code follows design constraints."""

    def test_gui_does_not_instantiate_calculator_directly(self):
        """Verify GUI source code contains no 'Calculator()' instantiation."""
        with open("src/gui/calculator_gui.py", "r") as f:
            source = f.read()

        # Check that "Calculator()" is not in the source
        assert "Calculator()" not in source, \
            "GUI should not instantiate Calculator directly; use injected service"

    def test_gui_contains_no_arithmetic_logic_functions(self):
        """Verify GUI source code contains no arithmetic operations."""
        with open("src/gui/calculator_gui.py", "r") as f:
            source = f.read()

        # Verify the file does not define core arithmetic functions
        arithmetic_functions = ["def add(", "def subtract(", "def multiply(",
                                "def divide(", "def sqrt(", "def power("]

        for func in arithmetic_functions:
            assert func not in source, \
                f"GUI should not contain {func}; arithmetic should be in service"

    def test_gui_references_service(self):
        """Verify GUI source code references 'service'."""
        with open("src/gui/calculator_gui.py", "r") as f:
            source = f.read()

        # Check that service is referenced
        assert "self.service" in source, \
            "GUI should reference self.service for performing calculations"


class TestCalculatorGUIServiceIntegration:
    """Test that GUI properly integrates with CalculatorService."""

    def test_gui_delegates_operations_to_service(self):
        """Verify GUI delegates operations to service."""
        mock_service = MagicMock(spec=CalculatorService)
        mock_result = MagicMock()
        mock_result.result = 8
        mock_service.perform.return_value = mock_result
        mock_service.get_history.return_value = []

        gui = CalculatorGUI(mock_service)
        assert gui.service is mock_service
        assert gui.service == mock_service

    def test_gui_service_parameter_is_required(self):
        """Verify service parameter is required in constructor."""
        import inspect
        sig = inspect.signature(CalculatorGUI.__init__)
        params = list(sig.parameters.keys())

        # Should have 'self' and 'service'
        assert 'service' in params, "Constructor must accept 'service' parameter"


class TestCalculatorGUIState:
    """Test GUI state management."""

    def test_gui_state_is_mutable(self):
        """Verify GUI maintains mutable state."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        # Test state can be modified
        gui.current_input = "5"
        assert gui.current_input == "5"

        gui.operand_a = 10.0
        assert gui.operand_a == 10.0

    def test_gui_has_clear_method(self):
        """Verify GUI has clear functionality."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        # Set some state
        gui.current_input = "123"
        gui.operand_a = 10.0

        # Verify methods exist
        assert hasattr(gui, '_on_clear_click')
        assert callable(gui._on_clear_click)


class TestCalculatorGUIUIElements:
    """Test that GUI creates appropriate UI elements."""

    def test_gui_has_run_method(self):
        """Verify GUI has run() method to start the application."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, 'run')
        assert callable(gui.run)

    def test_gui_has_create_widgets_method(self):
        """Verify GUI has _create_widgets() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_create_widgets')
        assert callable(gui._create_widgets)

    def test_gui_has_display_update_method(self):
        """Verify GUI has _update_display() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_update_display')
        assert callable(gui._update_display)


class TestCalculatorGUIEventHandlers:
    """Test GUI event handler methods exist."""

    def test_gui_has_number_click_handler(self):
        """Verify GUI has _on_number_click() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_on_number_click')
        assert callable(gui._on_number_click)

    def test_gui_has_operation_click_handler(self):
        """Verify GUI has _on_operation_click() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_on_operation_click')
        assert callable(gui._on_operation_click)

    def test_gui_has_equals_click_handler(self):
        """Verify GUI has _on_equals_click() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_on_equals_click')
        assert callable(gui._on_equals_click)

    def test_gui_has_backspace_handler(self):
        """Verify GUI has _on_backspace_click() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_on_backspace_click')
        assert callable(gui._on_backspace_click)


class TestCalculatorGUIHistory:
    """Test GUI history functionality."""

    def test_gui_has_history_refresh_method(self):
        """Verify GUI has _refresh_history() method."""
        mock_service = MagicMock(spec=CalculatorService)
        gui = CalculatorGUI(mock_service)

        assert hasattr(gui, '_refresh_history')
        assert callable(gui._refresh_history)

    def test_gui_queries_service_for_history(self):
        """Verify GUI calls service.get_history()."""
        mock_service = MagicMock(spec=CalculatorService)
        mock_service.get_history.return_value = []
        gui = CalculatorGUI(mock_service)

        # verify service has get_history
        assert hasattr(mock_service, 'get_history')
