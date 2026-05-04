import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ...models.workflow_status import WorkflowStatus
from ...models.workflow_conclusion import WorkflowConclusion


class FilterFrame(tk.Frame):
    """Status and conclusion filter controls."""

    def __init__(self, parent: tk.Widget, on_filter_change: Callable) -> None:
        super().__init__(parent)
        self._on_filter_change = on_filter_change

        # Title
        title = tk.Label(self, text="Filters", font=("Arial", 11, "bold"))
        title.pack(anchor="w", padx=10, pady=10)

        # Status filter
        status_frame = tk.Frame(self)
        status_frame.pack(anchor="w", padx=10, pady=5)

        tk.Label(status_frame, text="Status:").pack(side="left", padx=5)
        self._status_var = tk.StringVar(value="")
        status_options = [""] + [s.value for s in WorkflowStatus]
        self._status_combo = ttk.Combobox(
            status_frame, textvariable=self._status_var, values=status_options, state="readonly", width=15
        )
        self._status_combo.pack(side="left", padx=5)
        self._status_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        # Conclusion filter
        conclusion_frame = tk.Frame(self)
        conclusion_frame.pack(anchor="w", padx=10, pady=5)

        tk.Label(conclusion_frame, text="Conclusion:").pack(side="left", padx=5)
        self._conclusion_var = tk.StringVar(value="")
        conclusion_options = [""] + [c.value for c in WorkflowConclusion]
        self._conclusion_combo = ttk.Combobox(
            conclusion_frame, textvariable=self._conclusion_var, values=conclusion_options, state="readonly", width=15
        )
        self._conclusion_combo.pack(side="left", padx=5)
        self._conclusion_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        # Clear button
        clear_btn = tk.Button(self, text="Clear Filters", command=self._clear_filters)
        clear_btn.pack(anchor="w", padx=10, pady=5)

    def _clear_filters(self) -> None:
        """Clear all filters."""
        self._status_var.set("")
        self._conclusion_var.set("")
        self._on_filter_change()

    def get_filter_kwargs(self) -> dict:
        """Build filter_runs() compatible kwargs.

        Returns:
            Dictionary with status and/or conclusion filters, or empty dict
        """
        kwargs = {}

        status_val = self._status_var.get()
        if status_val:
            kwargs["status"] = WorkflowStatus(status_val)

        conclusion_val = self._conclusion_var.get()
        if conclusion_val:
            kwargs["conclusion"] = WorkflowConclusion(conclusion_val)

        return kwargs
