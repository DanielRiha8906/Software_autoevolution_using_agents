"""Filter bar widget with status and project dropdowns."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FilterBar(ttk.Frame):
    """Filter bar with status and project dropdowns."""

    def __init__(
        self,
        parent: tk.Widget,
        on_filter_change: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize the filter bar.

        Args:
            parent: Parent widget
            on_filter_change: Callback when filter changes
        """
        super().__init__(parent)
        self.on_filter_change = on_filter_change
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create filter widgets."""
        ttk.Label(self, text="Status:").pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(
            self,
            textvariable=self.status_var,
            values=["all", "pending", "in_progress", "done"],
            state="readonly",
            width=12,
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        ttk.Label(self, text="Project:").pack(side=tk.LEFT, padx=5)

        self.project_var = tk.StringVar(value="all")
        self.project_combo = ttk.Combobox(
            self,
            textvariable=self.project_var,
            values=["all"],
            state="readonly",
            width=20,
        )
        self.project_combo.pack(side=tk.LEFT, padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", lambda e: self._on_change())

    def _on_change(self) -> None:
        """Handle filter change."""
        if self.on_filter_change:
            self.on_filter_change()

    def get_status_filter(self) -> Optional[str]:
        """Get selected status filter.

        Returns:
            Status string or None for all statuses
        """
        status = self.status_var.get()
        return None if status == "all" else status

    def get_project_filter(self) -> Optional[str]:
        """Get selected project filter.

        Returns:
            Project ID or None for all projects
        """
        project = self.project_var.get()
        return None if project == "all" else project

    def set_projects(self, projects: list[tuple[str, str]]) -> None:
        """Set available projects.

        Args:
            projects: List of (project_id, project_name) tuples
        """
        values = ["all"] + [name for _, name in projects]
        self.project_combo["values"] = values
        self._project_id_map = {name: proj_id for proj_id, name in projects}

    def reset_filters(self) -> None:
        """Reset all filters to default values."""
        self.status_var.set("all")
        self.project_var.set("all")
