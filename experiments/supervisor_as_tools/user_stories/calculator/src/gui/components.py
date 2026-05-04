"""Reusable tkinter widgets and components."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Any

from .constants import (
    COLOR_BUTTON_BG,
    COLOR_BUTTON_FG,
    COLOR_DISPLAY_BG,
    COLOR_ERROR_BG,
    COLOR_ERROR_FG,
    COLOR_SUCCESS_BG,
    FONT_FAMILY,
    BUTTON_FONT_SIZE,
    DISPLAY_FONT_SIZE,
    PADDING_SMALL,
)


class NumberInput(ttk.Frame):
    """Reusable widget for number input with validation."""

    def __init__(self, parent: tk.Widget, label: str, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.label = tk.Label(self, text=label, font=(FONT_FAMILY, BUTTON_FONT_SIZE))
        self.label.pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.entry = tk.Entry(self, font=(FONT_FAMILY, BUTTON_FONT_SIZE), width=15)
        self.entry.pack(side=tk.LEFT, padx=PADDING_SMALL)

    def get(self) -> float | None:
        """Get the numeric value from the input, or None if invalid."""
        try:
            return float(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float) -> None:
        """Set the input value."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))

    def clear(self) -> None:
        """Clear the input field."""
        self.entry.delete(0, tk.END)


class OperationSelector(ttk.Frame):
    """Reusable widget for selecting an operation."""

    def __init__(
        self,
        parent: tk.Widget,
        operations: list[str],
        on_select: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.operations = operations
        self.on_select = on_select

        label = tk.Label(self, text="Operation:", font=(FONT_FAMILY, BUTTON_FONT_SIZE))
        label.pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.var = tk.StringVar(value=operations[0] if operations else "")
        self.dropdown = ttk.Combobox(
            self,
            textvariable=self.var,
            values=operations,
            state="readonly",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            width=15,
        )
        self.dropdown.pack(side=tk.LEFT, padx=PADDING_SMALL)

        if self.on_select:
            self.dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_select(self.get()))

    def get(self) -> str:
        """Get the selected operation."""
        return self.var.get()

    def set(self, operation: str) -> None:
        """Set the selected operation."""
        self.var.set(operation)


class HistoryEntry(ttk.Frame):
    """Display a single history entry in the list."""

    def __init__(
        self,
        parent: tk.Widget,
        entry_text: str,
        is_error: bool = False,
        on_double_click: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.is_error = is_error
        self.on_double_click = on_double_click

        bg_color = COLOR_ERROR_BG if is_error else COLOR_DISPLAY_BG
        fg_color = COLOR_ERROR_FG if is_error else "black"

        self.label = tk.Label(
            self,
            text=entry_text,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            bg=bg_color,
            fg=fg_color,
            anchor="w",
            justify=tk.LEFT,
        )
        self.label.pack(fill=tk.BOTH, expand=True, padx=PADDING_SMALL, pady=PADDING_SMALL)

        if on_double_click:
            self.label.bind("<Double-Button-1>", lambda e: on_double_click())

    def update_text(self, new_text: str) -> None:
        """Update the displayed text."""
        self.label.config(text=new_text)


class FilterPanel(ttk.Frame):
    """Filter controls for history display."""

    def __init__(
        self,
        parent: tk.Widget,
        operations: list[str],
        on_filter_changed: Callable[[str | None, bool | None], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.on_filter_changed = on_filter_changed

        # Operation filter
        op_label = tk.Label(self, text="Filter by operation:", font=(FONT_FAMILY, BUTTON_FONT_SIZE))
        op_label.pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.operation_var = tk.StringVar(value="All")
        operation_values = ["All"] + operations
        self.operation_dropdown = ttk.Combobox(
            self,
            textvariable=self.operation_var,
            values=operation_values,
            state="readonly",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            width=12,
        )
        self.operation_dropdown.pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.operation_dropdown.bind("<<ComboboxSelected>>", lambda e: self._notify_filter_changed())

        # Success checkbox
        self.success_var = tk.BooleanVar(value=False)
        self.success_check = tk.Checkbutton(
            self,
            text="Success only",
            variable=self.success_var,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            command=self._notify_filter_changed,
        )
        self.success_check.pack(side=tk.LEFT, padx=PADDING_SMALL)

        # Error checkbox
        self.error_var = tk.BooleanVar(value=False)
        self.error_check = tk.Checkbutton(
            self,
            text="Errors only",
            variable=self.error_var,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            command=self._notify_filter_changed,
        )
        self.error_check.pack(side=tk.LEFT, padx=PADDING_SMALL)

    def _notify_filter_changed(self) -> None:
        """Notify listener of filter change."""
        if self.on_filter_changed:
            operation = self.operation_var.get()
            operation = None if operation == "All" else operation
            success_filter = None
            if self.success_var.get():
                success_filter = True
            elif self.error_var.get():
                success_filter = False

            self.on_filter_changed(operation, success_filter)

    def get_filters(self) -> tuple[str | None, bool | None]:
        """Get current filter values."""
        operation = self.operation_var.get()
        operation = None if operation == "All" else operation
        success_filter = None
        if self.success_var.get():
            success_filter = True
        elif self.error_var.get():
            success_filter = False
        return operation, success_filter
