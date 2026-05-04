"""Main GUI window for the calculator application."""

import tkinter as tk

from .constants import (
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    COLOR_BACKGROUND, PADDING_STANDARD
)
from .gui_controller import GUIController
from .input_panel import InputPanel
from .result_panel import ResultPanel
from .history_panel import HistoryPanel
from .mode_selector import ModeSelector


class MainWindow(tk.Tk):
    """Root tkinter window for the calculator GUI.

    Integrates:
    - ModeSelector (top)
    - InputPanel (operation and operand input)
    - ResultPanel (result display)
    - HistoryPanel (scrollable history list)

    Event flow:
    1. User selects operation and enters operands in InputPanel
    2. User clicks Calculate
    3. InputPanel calls gui_controller.perform_calculation()
    4. ResultPanel displays the result
    5. HistoryPanel refreshes to show new entry
    """

    def __init__(self, gui_controller: GUIController) -> None:
        """Initialize the main window.

        Args:
            gui_controller: GUIController instance for service integration.
        """
        super().__init__()
        self.gui_controller = gui_controller
        self.title("Calculator")
        self.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.minsize(700, 500)

        # Configure main window background
        self.config(bg=COLOR_BACKGROUND)

        self._setup_ui()
        self._setup_callbacks()

    def _setup_ui(self) -> None:
        """Set up the UI layout."""
        # Create main container with padding
        main_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        # Mode selector (top)
        self.mode_selector = ModeSelector(main_frame)
        self.mode_selector.pack(fill=tk.X, pady=PADDING_STANDARD)

        # Input panel
        self.input_panel = InputPanel(main_frame)
        self.input_panel.pack(fill=tk.X, pady=PADDING_STANDARD)

        # Result panel
        self.result_panel = ResultPanel(main_frame)
        self.result_panel.pack(fill=tk.X, pady=PADDING_STANDARD)

        # History panel (takes remaining space)
        self.history_panel = HistoryPanel(main_frame)
        self.history_panel.pack(fill=tk.BOTH, expand=True, pady=PADDING_STANDARD)

    def _setup_callbacks(self) -> None:
        """Set up event callbacks."""
        self.input_panel.set_calculate_callback(self._on_calculate)
        self.mode_selector.set_mode_changed_callback(self._on_mode_changed)

    def _on_calculate(self, operation_str: str, a: float, b: float) -> None:
        """Handle calculation request from InputPanel.

        Args:
            operation_str: Operation name.
            a: First operand.
            b: Second operand.
        """
        try:
            entry = self.gui_controller.perform_calculation(operation_str, a, b)
            self.result_panel.display_result(entry)
            self._refresh_history()
        except ValueError as e:
            self.input_panel.set_error_message(f"Error: {str(e)}")

    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode change from ModeSelector.

        Args:
            mode: New mode ('standard' or 'scientific').
        """
        self.input_panel.set_mode(mode)

    def _refresh_history(self) -> None:
        """Refresh the history panel with current data."""
        entries = self.gui_controller.get_history()
        self.history_panel.refresh(entries)

    def run(self) -> None:
        """Start the GUI event loop."""
        self.mainloop()
