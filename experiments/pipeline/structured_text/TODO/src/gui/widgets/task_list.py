"""Task list widget using Treeview."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..utils.formatting import format_date


class TaskListWidget(ttk.Frame):
    """Task list display using Treeview with columns for status, title, due date, project."""

    def __init__(
        self,
        parent: tk.Widget,
        on_select: Optional[Callable[[str], None]] = None,
        on_double_click: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the task list widget.

        Args:
            parent: Parent widget
            on_select: Callback when a task is selected (called with task ID)
            on_double_click: Callback when a task is double-clicked (called with task ID)
        """
        super().__init__(parent)
        self.on_select = on_select
        self.on_double_click = on_double_click
        self._task_id_map = {}

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create treeview and scrollbar."""
        scroll_frame = ttk.Frame(self)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            scroll_frame,
            columns=("Status", "Title", "Due Date", "Project"),
            show="tree headings",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("Status", width=40, anchor=tk.W)
        self.tree.column("Title", width=250, anchor=tk.W)
        self.tree.column("Due Date", width=100, anchor=tk.CENTER)
        self.tree.column("Project", width=150, anchor=tk.W)

        self.tree.heading("Status", text="")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Project", text="Project")

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_select(self, event: tk.Event) -> None:
        """Handle selection event."""
        if not self.on_select:
            return
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            task_id = self._task_id_map.get(item)
            if task_id:
                self.on_select(task_id)

    def _on_double_click(self, event: tk.Event) -> None:
        """Handle double-click event."""
        if not self.on_double_click:
            return
        item = self.tree.identify("item", event.x, event.y)
        if item:
            task_id = self._task_id_map.get(item)
            if task_id:
                self.on_double_click(task_id)

    def clear(self) -> None:
        """Clear all tasks from the list."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._task_id_map.clear()

    def add_task(self, task: dict, is_overdue: bool = False) -> None:
        """Add a task to the list.

        Args:
            task: Task dictionary with id, status, title, due_date, project_name
            is_overdue: Whether the task is overdue
        """
        status_symbol = self._get_status_symbol(task["status"])
        title = task["title"]
        due_date_str = format_date(task["due_date"]) if task.get("due_date") else ""
        project_name = task.get("project_name", "")

        tags = []
        if is_overdue:
            tags.append("overdue")

        item = self.tree.insert("", tk.END, values=(status_symbol, title, due_date_str, project_name), tags=tags)
        self._task_id_map[item] = task["id"]

        if is_overdue:
            self.tree.tag_configure("overdue", foreground="red", background="#ffe0e0")

    def _get_status_symbol(self, status: str) -> str:
        """Get status symbol for display.

        Args:
            status: Task status string

        Returns:
            Status symbol
        """
        symbols = {
            "pending": "[ ]",
            "in_progress": "[~]",
            "done": "[x]",
        }
        return symbols.get(status, "?")

    def get_selected_task_id(self) -> Optional[str]:
        """Get the ID of the currently selected task.

        Returns:
            Task ID if a task is selected, None otherwise
        """
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            return self._task_id_map.get(item)
        return None
