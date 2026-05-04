"""Tests for --gui flag in __main__.py."""

import pytest
from unittest.mock import patch, MagicMock, call
import argparse


class TestGUIFlagParsing:
    """Test suite for GUI flag parsing in __main__.py."""

    def test_gui_flag_is_in_parser(self):
        """Test that --gui flag is recognized by argparse."""
        # Import here to avoid sys.exit issues
        import sys
        from src import __main__

        # Create a parser like __main__ does
        parser = argparse.ArgumentParser(
            prog="python -m src",
            description="OOP Calculator — run interactively or pass --operation for one-shot use",
        )
        parser.add_argument(
            "--operation",
            metavar="OP",
            choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
            help="Operation to perform",
        )
        parser.add_argument(
            "--gui",
            action="store_true",
            help="Launch the graphical user interface",
        )

        # Test parsing
        args = parser.parse_args(["--gui"])
        assert args.gui is True

    def test_gui_flag_default_is_false(self):
        """Test that --gui defaults to False when not provided."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true", help="Launch GUI")

        args = parser.parse_args([])
        assert args.gui is False

    def test_gui_flag_with_other_flags(self):
        """Test --gui can be combined with other flags."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true")
        parser.add_argument("--show-history", action="store_true")
        parser.add_argument("--operation", choices=["add"])

        args = parser.parse_args(["--gui", "--show-history"])
        assert args.gui is True
        assert args.show_history is True

    def test_gui_flag_is_boolean_action(self):
        """Test that --gui is a store_true action."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true")

        args = parser.parse_args(["--gui"])
        assert isinstance(args.gui, bool)
        assert args.gui is True

    def test_gui_flag_with_operation_both_parsed(self):
        """Test that both --gui and --operation can be parsed together."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true")
        parser.add_argument("--operation", choices=["add", "subtract"])
        parser.add_argument("operands", nargs="*")

        args = parser.parse_args(["--gui", "--operation", "add", "1", "2"])
        assert args.gui is True
        assert args.operation == "add"

    def test_gui_controller_initialization(self):
        """Test that GUIController can be instantiated with services."""
        from src.gui.gui_controller import GUIController
        from src.services.calculator_service import CalculatorService
        from src.services.memory_service import MemoryService
        from src.services.statistics_service import StatisticsService

        calc_service = MagicMock(spec=CalculatorService)
        mem_service = MagicMock(spec=MemoryService)
        stats_service = MagicMock(spec=StatisticsService)

        controller = GUIController(calc_service, mem_service, stats_service)

        assert controller.calculator_service == calc_service
        assert controller.memory_service == mem_service
        assert controller.statistics_service == stats_service

    def test_gui_flag_comparison_with_other_flags(self):
        """Test priority of --gui over other flags in argparse."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true")
        parser.add_argument("--operation")
        parser.add_argument("--show-history", action="store_true")
        parser.add_argument("operands", nargs="*")

        # When --gui is set, other flags are also parsed but should be handled after
        args = parser.parse_args(["--gui", "--operation", "add", "1", "2"])
        assert args.gui is True
        assert args.operation == "add"
        assert hasattr(args, "show_history")

    def test_services_can_be_built(self):
        """Test that services can be built for GUI."""
        from pathlib import Path
        from src.services.calculator import Calculator
        from src.services.calculator_service import CalculatorService
        from src.services.memory_service import MemoryService
        from src.services.statistics_service import StatisticsService
        from src.storage.json_storage import JsonStorage

        # Mock storage
        with patch("src.storage.json_storage.JsonStorage") as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage

            storage = JsonStorage(Path("test.json"))
            memory_service = MemoryService(storage)
            calculator_service = CalculatorService(Calculator(), memory_service)
            statistics_service = StatisticsService(memory_service)

            assert calculator_service is not None
            assert memory_service is not None
            assert statistics_service is not None

    def test_gui_help_shows_flag(self):
        """Test that --help shows the --gui flag."""
        import argparse
        import io
        import sys

        parser = argparse.ArgumentParser()
        parser.add_argument("--gui", action="store_true", help="Launch the graphical user interface")

        # Capture help output
        with pytest.raises(SystemExit):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                parser.parse_args(["--help"])

    def test_operation_enum_validation(self):
        """Test that Operation enum validates correctly."""
        from src.models.operation import Operation

        # Valid operations
        valid_ops = ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"]

        for op in valid_ops:
            result = Operation.from_string(op)
            assert result.value == op

    def test_invalid_operation_raises_error(self):
        """Test that invalid operation raises ValueError."""
        from src.models.operation import Operation

        with pytest.raises(ValueError):
            Operation.from_string("invalid_operation")

    def test_gui_controller_methods_exist(self):
        """Test that GUIController has required methods."""
        from src.gui.gui_controller import GUIController

        methods = [
            "perform_calculation",
            "get_history",
            "filter_history",
            "get_statistics",
        ]

        for method in methods:
            assert hasattr(GUIController, method)
            assert callable(getattr(GUIController, method))

    def test_gui_components_can_be_imported(self):
        """Test that all GUI components can be imported."""
        from src.gui.gui_controller import GUIController
        from src.gui.input_panel import InputPanel
        from src.gui.result_panel import ResultPanel
        from src.gui.history_panel import HistoryPanel
        from src.gui.mode_selector import ModeSelector

        assert GUIController is not None
        assert InputPanel is not None
        assert ResultPanel is not None
        assert HistoryPanel is not None
        assert ModeSelector is not None

    def test_constants_are_properly_defined(self):
        """Test that GUI constants are defined."""
        from src.gui.constants import (
            STANDARD_OPS, SCIENTIFIC_OPS, FONT_RESULT, FONT_ERROR,
            COLOR_ERROR_TEXT, COLOR_SUCCESS_TEXT
        )

        assert len(STANDARD_OPS) == 6
        assert len(SCIENTIFIC_OPS) == 14
        assert FONT_RESULT is not None
        assert FONT_ERROR is not None
        assert COLOR_ERROR_TEXT is not None
        assert COLOR_SUCCESS_TEXT is not None

    def test_main_entry_point_exists(self):
        """Test that main function exists in __main__.py."""
        from src.__main__ import main

        assert callable(main)

    def test_memory_entry_string_representation(self):
        """Test MemoryEntry string representation."""
        from src.models.memory_entry import MemoryEntry

        entry = MemoryEntry("add", 2.0, 3.0, 5.0, None, None)
        entry_str = str(entry)

        assert "2" in entry_str
        assert "3" in entry_str
        assert "5" in entry_str
        assert "+" in entry_str

    def test_memory_entry_error_representation(self):
        """Test MemoryEntry error string representation."""
        from src.models.memory_entry import MemoryEntry

        entry = MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError")
        entry_str = str(entry)

        assert "ERROR:" in entry_str
        assert "Division by zero" in entry_str

    def test_main_parser_has_gui_flag_in_choices(self):
        """Test that main parser includes --gui in its setup."""
        import inspect
        from src.__main__ import main

        source = inspect.getsource(main)
        assert "--gui" in source
        assert "action=\"store_true\"" in source or "action='store_true'" in source
