"""Result display panel for calculation results and errors."""

import tkinter as tk

from .constants import (
    FONT_RESULT, FONT_ERROR, PADDING_STANDARD,
    COLOR_PANEL_BACKGROUND, COLOR_ERROR_TEXT, COLOR_ERROR_BACKGROUND,
    COLOR_SUCCESS_TEXT, COLOR_SUCCESS_BACKGROUND
)
from ..models.memory_entry import MemoryEntry


class ResultPanel(tk.Frame):
    """Panel displaying the result of the last calculation.

    Shows either:
    - Success result in format "a op b = result"
    - Error message in format "ERROR: message"
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the result panel.

        Args:
            parent: Parent tkinter widget.
        """
        super().__init__(parent, bg=COLOR_PANEL_BACKGROUND)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tk.Label(
            self,
            text="Result:",
            font=("Arial", 10, "bold"),
            bg=COLOR_PANEL_BACKGROUND
        ).pack(anchor=tk.W, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        self.result_label = tk.Label(
            self,
            text="No calculation yet",
            font=FONT_RESULT,
            bg=COLOR_SUCCESS_BACKGROUND,
            fg=COLOR_SUCCESS_TEXT,
            wraplength=400,
            justify=tk.LEFT
        )
        self.result_label.pack(fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

    def display_result(self, entry: MemoryEntry) -> None:
        """Display a calculation result.

        Args:
            entry: MemoryEntry from the last calculation.
        """
        if entry.error:
            # Display error
            message = f"ERROR: {entry.error}"
            self.result_label.config(
                text=message,
                fg=COLOR_ERROR_TEXT,
                bg=COLOR_ERROR_BACKGROUND,
                font=FONT_ERROR
            )
        else:
            # Display success result
            message = str(entry)
            self.result_label.config(
                text=message,
                fg=COLOR_SUCCESS_TEXT,
                bg=COLOR_SUCCESS_BACKGROUND,
                font=FONT_RESULT
            )

    def clear(self) -> None:
        """Clear the result display."""
        self.result_label.config(
            text="No calculation yet",
            fg=COLOR_SUCCESS_TEXT,
            bg=COLOR_SUCCESS_BACKGROUND,
            font=FONT_RESULT
        )
