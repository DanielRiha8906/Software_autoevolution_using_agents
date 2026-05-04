"""Tests for the Calculator GUI.

Tests verify that the GUI:
1. Exists at the expected location
2. Accepts a service instance through constructor
3. Does not instantiate Calculator directly
4. Contains no arithmetic logic
5. Delegates to the service layer
"""

import pytest
from unittest.mock import MagicMock, patch
from src.models.calculation_result import CalculationResult
from src.gui.calculator_gui import CalculatorGUI


_TS = "2026-01-01T00:00:00"


def test_calculator_gui_module_exists():
    """GUI class must exist at src.gui.calculator_gui.CalculatorGUI."""
    assert CalculatorGUI is not None


def test_calculator_gui_accepts_service():
    """GUI constructor must accept a service instance."""
    service = MagicMock()
    gui = CalculatorGUI(service)
    assert gui.service is service


def test_gui_does_not_instantiate_calculator_directly():
    """No 'Calculator()' should appear in GUI source code."""
    import inspect
    from src.gui import calculator_gui

    source = inspect.getsource(calculator_gui)
    assert "Calculator()" not in source, "GUI should not instantiate Calculator directly"


def test_gui_contains_no_arithmetic_logic():
    """No arithmetic functions (add, divide, etc.) in GUI source."""
    import inspect
    from src.gui import calculator_gui

    source = inspect.getsource(calculator_gui)
    # Check that arithmetic function definitions are not in GUI
    arithmetic_patterns = [
        "def add(",
        "def subtract(",
        "def multiply(",
        "def divide(",
        "def sqrt(",
        "def power(",
        "def modulo(",
        "def square(",
    ]
    for pattern in arithmetic_patterns:
        assert pattern not in source, f"GUI should not contain {pattern}"


def test_gui_references_service():
    """GUI source must contain 'service' (case-insensitive)."""
    import inspect
    from src.gui import calculator_gui

    source = inspect.getsource(calculator_gui)
    assert "service" in source.lower(), "GUI should reference service"
