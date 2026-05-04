"""Action bar widget with Add and Refresh buttons."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ActionBar(ttk.Frame):
    """Action bar with Add and Refresh buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        on_add: Optional[Callable[[], None]] = None,
        on_refresh: Optional[Callable[[], None]] = None,
        on_edit: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize the action bar.

        Args:
            parent: Parent widget
            on_add: Callback for Add button
            on_refresh: Callback for Refresh button
            on_edit: Callback for Edit button
            on_delete: Callback for Delete button
        """
        super().__init__(parent)
        self.on_add = on_add
        self.on_refresh = on_refresh
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create action buttons."""
        ttk.Button(self, text="Add Task", command=self._on_add_click).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self, text="Edit", command=self._on_edit_click).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self, text="Delete", command=self._on_delete_click).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self, text="Refresh", command=self._on_refresh_click).pack(side=tk.LEFT, padx=5, pady=5)

    def _on_add_click(self) -> None:
        """Handle Add button click."""
        if self.on_add:
            self.on_add()

    def _on_edit_click(self) -> None:
        """Handle Edit button click."""
        if self.on_edit:
            self.on_edit()

    def _on_delete_click(self) -> None:
        """Handle Delete button click."""
        if self.on_delete:
            self.on_delete()

    def _on_refresh_click(self) -> None:
        """Handle Refresh button click."""
        if self.on_refresh:
            self.on_refresh()
