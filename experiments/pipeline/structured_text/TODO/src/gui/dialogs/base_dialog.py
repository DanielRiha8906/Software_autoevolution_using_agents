"""Base class for dialog windows."""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk


class BaseDialog(ABC, tk.Toplevel):
    """Abstract base class for modal dialog windows."""

    def __init__(self, parent: tk.Widget, title: str) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent window
            title: Dialog title
        """
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.result = None

        self._create_widgets()
        self.geometry("400x300")
        self.resizable(False, False)

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 150
        self.geometry(f"+{x}+{y}")

        self.focus()

    @abstractmethod
    def _create_widgets(self) -> None:
        """Create dialog widgets. Must be implemented by subclasses."""
        pass

    def _on_ok(self) -> None:
        """Handle OK button. Should be overridden by subclasses if needed."""
        self.result = True
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle Cancel button."""
        self.result = None
        self.destroy()
