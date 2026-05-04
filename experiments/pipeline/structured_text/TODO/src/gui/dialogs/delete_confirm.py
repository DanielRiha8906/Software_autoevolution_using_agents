"""Dialog for confirming task deletion."""

import tkinter as tk
from tkinter import ttk

from .base_dialog import BaseDialog


class DeleteConfirmDialog(BaseDialog):
    """Dialog for confirming task deletion."""

    def __init__(self, parent: tk.Widget, task_title: str) -> None:
        """Initialize the delete confirmation dialog.

        Args:
            parent: Parent window
            task_title: Title of the task to delete
        """
        self.task_title = task_title
        super().__init__(parent, "Confirm Delete")
        self.geometry("350x150")

    def _create_widgets(self) -> None:
        """Create confirmation widgets."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        label = ttk.Label(frame, text=f'Delete task "{self.task_title}"?', wraplength=300)
        label.pack(pady=20)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Delete", command=self._on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_delete(self) -> None:
        """Handle delete confirmation."""
        self.result = True
        self.destroy()
