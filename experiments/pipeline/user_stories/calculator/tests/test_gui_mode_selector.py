"""Tests for ModeSelector GUI component - Unit testing with mocks."""

import pytest
from unittest.mock import MagicMock, patch
from src.gui.mode_selector import ModeSelector
from src.gui.constants import STANDARD_OPS, SCIENTIFIC_OPS


class TestModeSelectorLogic:
    """Test suite for ModeSelector logic without requiring display."""

    def setup_method(self):
        """Set up test fixtures with mocked tkinter."""
        self.mock_root = MagicMock()

        with patch("src.gui.mode_selector.tk.Frame.__init__", return_value=None):
            with patch.object(ModeSelector, "_setup_ui"):
                self.selector = ModeSelector(self.mock_root)

        # Mock the mode_var StringVar
        self.selector.mode_var = MagicMock()
        self.selector.mode_var.get = MagicMock(return_value="scientific")
        self.selector.mode_var.set = MagicMock()

    def teardown_method(self):
        """Clean up."""
        pass

    def test_mode_selector_initialization(self):
        """Test that ModeSelector initializes with scientific mode."""
        assert self.selector.current_mode == "scientific"

    def test_get_mode_returns_current_selection(self):
        """Test that get_mode returns the current mode."""
        assert self.selector.get_mode() == "scientific"
        self.selector.current_mode = "standard"
        assert self.selector.get_mode() == "standard"

    def test_set_mode_changed_callback(self):
        """Test setting a callback for mode change."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)
        assert self.selector.mode_changed_callback == callback

    def test_on_mode_changed_calls_callback(self):
        """Test that mode change invokes the callback."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        callback.assert_called_once_with("standard")

    def test_on_mode_changed_updates_current_mode(self):
        """Test that mode change updates current_mode attribute."""
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.current_mode == "standard"

    def test_on_mode_changed_to_scientific(self):
        """Test changing to scientific mode."""
        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.current_mode == "scientific"

    def test_mode_toggle_standard_to_scientific(self):
        """Test toggling from standard to scientific."""
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "scientific"

    def test_mode_toggle_scientific_to_standard(self):
        """Test toggling from scientific to standard."""
        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "scientific"

        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

    def test_callback_receives_correct_mode_for_standard(self):
        """Test callback receives 'standard' when switching to standard."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        callback.assert_called_with("standard")

    def test_callback_receives_correct_mode_for_scientific(self):
        """Test callback receives 'scientific' when switching to scientific."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)
        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        callback.assert_called_with("scientific")

    def test_on_mode_changed_without_callback(self):
        """Test that mode change works without callback set."""
        self.selector.mode_var.get.return_value = "standard"
        # Should not crash
        self.selector._on_mode_changed()
        assert self.selector.current_mode == "standard"

    def test_multiple_mode_changes(self):
        """Test multiple sequential mode changes."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)

        # Change to standard
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

        # Change back to scientific
        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "scientific"

        # Change to standard again
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

        # Callback called 3 times
        assert callback.call_count == 3

    def test_standard_mode_option_available(self):
        """Test that standard mode option is available."""
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

    def test_scientific_mode_option_available(self):
        """Test that scientific mode option is available."""
        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "scientific"

    def test_mode_selector_default_is_scientific(self):
        """Test that default mode is scientific, not standard."""
        assert self.selector.current_mode == "scientific"

    def test_callback_not_called_on_initialization(self):
        """Test that callback is not called during initialization."""
        callback = MagicMock()
        # Set callback after initialization
        self.selector.set_mode_changed_callback(callback)
        # Callback should not be called yet
        callback.assert_not_called()

    def test_current_mode_property_reflects_selection(self):
        """Test that current_mode property reflects radio button selection."""
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.current_mode == "standard"
        assert self.selector.get_mode() == "standard"

    def test_rapid_mode_changes(self):
        """Test rapid sequential mode changes."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)

        for i in range(5):
            self.selector.mode_var.get.return_value = "standard"
            self.selector._on_mode_changed()
            self.selector.mode_var.get.return_value = "scientific"
            self.selector._on_mode_changed()

        assert callback.call_count == 10

    def test_setting_callback_multiple_times(self):
        """Test that setting callback multiple times overwrites previous."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.selector.set_mode_changed_callback(callback1)
        self.selector.set_mode_changed_callback(callback2)

        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()

        # Only callback2 should be called
        callback1.assert_not_called()
        callback2.assert_called_once_with("standard")

    def test_mode_change_callback_with_exception_handling(self):
        """Test mode change when callback exists."""
        def callback_that_does_nothing(mode):
            pass

        self.selector.set_mode_changed_callback(callback_that_does_nothing)
        self.selector.mode_var.get.return_value = "standard"
        # Should not raise
        self.selector._on_mode_changed()
        assert self.selector.current_mode == "standard"

    def test_get_mode_always_returns_string(self):
        """Test that get_mode always returns a string."""
        self.selector.current_mode = "standard"
        result = self.selector.get_mode()
        assert isinstance(result, str)
        assert result in ["standard", "scientific"]

    def test_mode_options_are_mutually_exclusive(self):
        """Test that only one mode can be selected at a time."""
        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "standard"

        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert self.selector.get_mode() == "scientific"
        # standard should no longer be selected
        assert self.selector.get_mode() != "standard"

    def test_mode_persistence_across_calls(self):
        """Test that mode persists across multiple get_mode calls."""
        self.selector.current_mode = "standard"

        mode1 = self.selector.get_mode()
        mode2 = self.selector.get_mode()
        mode3 = self.selector.get_mode()

        assert mode1 == mode2 == mode3 == "standard"

    def test_callback_with_varying_modes(self):
        """Test callback is called with correct mode each time."""
        callback = MagicMock()
        self.selector.set_mode_changed_callback(callback)

        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert callback.call_args[0][0] == "standard"

        self.selector.mode_var.get.return_value = "scientific"
        self.selector._on_mode_changed()
        assert callback.call_args[0][0] == "scientific"

        self.selector.mode_var.get.return_value = "standard"
        self.selector._on_mode_changed()
        assert callback.call_args[0][0] == "standard"

    def test_standard_ops_constant(self):
        """Test STANDARD_OPS constant."""
        assert len(STANDARD_OPS) == 6
        assert "add" in STANDARD_OPS
        assert "sqrt" in STANDARD_OPS

    def test_scientific_ops_constant(self):
        """Test SCIENTIFIC_OPS constant."""
        assert len(SCIENTIFIC_OPS) == 14
        assert "add" in SCIENTIFIC_OPS
        assert "sin" in SCIENTIFIC_OPS
        assert "cos" in SCIENTIFIC_OPS
        assert "tan" in SCIENTIFIC_OPS
