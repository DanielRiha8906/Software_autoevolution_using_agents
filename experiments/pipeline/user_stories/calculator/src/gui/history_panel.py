"""History panel for displaying calculation history."""

import tkinter as tk
from tkinter import ttk

from .constants import (
    FONT_HISTORY, PADDING_STANDARD,
    COLOR_PANEL_BACKGROUND, COLOR_ERROR_TEXT, COLOR_ERROR_BACKGROUND,
    COLOR_SUCCESS_TEXT, COLOR_SUCCESS_BACKGROUND
)
from ..models.memory_entry import MemoryEntry


class HistoryPanel(tk.Frame):
    """Panel displaying scrollable list of calculation history.

    Each entry shows:
    - Successful: "i. a op b = result [timestamp]"
    - Error: "i. a op b = ERROR: message" with red highlighting
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the history panel.

        Args:
            parent: Parent tkinter widget.
        """
        super().__init__(parent, bg=COLOR_PANEL_BACKGROUND)
        self._setup_ui()
        self.entries: list[MemoryEntry] = []

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Title
        tk.Label(
            self,
            text="History:",
            font=("Arial", 10, "bold"),
            bg=COLOR_PANEL_BACKGROUND
        ).pack(anchor=tk.W, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        # Create frame for listbox and scrollbar
        list_frame = tk.Frame(self, bg=COLOR_PANEL_BACKGROUND)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create listbox
        self.history_listbox = tk.Listbox(
            list_frame,
            font=FONT_HISTORY,
            yscrollcommand=scrollbar.set,
            bg=COLOR_SUCCESS_BACKGROUND,
            fg=COLOR_SUCCESS_TEXT
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)

    def refresh(self, entries: list[MemoryEntry]) -> None:
        """Refresh the history display with new entries.

        Args:
            entries: List of MemoryEntry objects to display.
        """
        self.entries = entries
        self.history_listbox.delete(0, tk.END)

        for idx, entry in enumerate(entries, start=1):
            # Format entry string
            entry_str = f"{idx}. {str(entry)}"

            # Insert into listbox
            self.history_listbox.insert(tk.END, entry_str)

            # Apply error highlighting if needed
            if entry.error:
                # Get the index of this entry
                item_index = idx - 1
                self.history_listbox.itemconfig(
                    item_index,
                    fg=COLOR_ERROR_TEXT,
                    bg=COLOR_ERROR_BACKGROUND
                )
            else:
                item_index = idx - 1
                self.history_listbox.itemconfig(
                    item_index,
                    fg=COLOR_SUCCESS_TEXT,
                    bg=COLOR_SUCCESS_BACKGROUND
                )

    def clear(self) -> None:
        """Clear the history display."""
        self.history_listbox.delete(0, tk.END)
        self.entries = []

    def get_entries(self) -> list[MemoryEntry]:
        """Get the currently displayed entries.

        Returns:
            List of MemoryEntry objects.
        """
        return self.entries
