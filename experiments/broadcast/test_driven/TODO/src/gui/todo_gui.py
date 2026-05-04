"""TodoGUI: A tkinter-based graphical interface for task management.

This module provides a GUI for displaying and managing tasks via a graphical
interface. All business logic is delegated to the service layer.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional


class TodoGUI:
    """A tkinter-based GUI for displaying and managing TODO tasks.

    The GUI displays tasks with their status, due date, and project information.
    Overdue tasks are highlighted to alert the user. All business logic is
    delegated to the service layer — this class handles only presentation.

    Args:
        service: A TodoService instance providing access to task operations.
    """

    def __init__(self, service) -> None:
        """Initialize TodoGUI with a service instance.

        Args:
            service: A TodoService instance for task operations and queries.
        """
        self.service = service
        self.root = None
        self.task_tree = None

    def run(self) -> None:
        """Launch the GUI window and start the event loop."""
        self.root = tk.Tk()
        self.root.title("TODO Manager")
        self.root.geometry("900x600")

        self._create_widgets()
        self._refresh_task_list()

        self.root.mainloop()

    def _create_widgets(self) -> None:
        """Create and layout GUI widgets."""
        # Top frame for controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        refresh_btn = ttk.Button(control_frame, text="Refresh", command=self._refresh_task_list)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying tasks
        columns = ("Status", "Title", "Due Date", "Project")
        self.task_tree = ttk.Treeview(self.root, columns=columns, height=20)
        self.task_tree.column("#0", width=40, minwidth=40)
        self.task_tree.column("Status", width=100, minwidth=80)
        self.task_tree.column("Title", width=300, minwidth=150)
        self.task_tree.column("Due Date", width=150, minwidth=100)
        self.task_tree.column("Project", width=150, minwidth=100)

        self.task_tree.heading("#0", text="ID")
        self.task_tree.heading("Status", text="Status")
        self.task_tree.heading("Title", text="Title")
        self.task_tree.heading("Due Date", text="Due Date")
        self.task_tree.heading("Project", text="Project")

        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscroll=scrollbar.set)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh_task_list(self) -> None:
        """Refresh the task list from the service."""
        if self.task_tree is None:
            return

        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Get all tasks from service
        tasks = self.service.list_tasks()

        # Add tasks to tree
        for task in tasks:
            task_id = task.id[:8]
            status = task.status.value
            title = task.title
            due_date = self._format_due_date(task.due_date)
            project = task.project_id or ""

            # Insert task row
            item_id = self.task_tree.insert("", "end", text=task_id, values=(status, title, due_date, project))

            # Highlight overdue tasks
            if task.is_overdue():
                self.task_tree.item(item_id, tags=("overdue",))

        # Configure tag for overdue tasks (red background)
        self.task_tree.tag_configure("overdue", background="#ffcccc")

    def _format_due_date(self, due_date: Optional[datetime]) -> str:
        """Format a due date for display.

        Args:
            due_date: A datetime object or None.

        Returns:
            A formatted date string, or empty string if due_date is None.
        """
        if due_date is None:
            return ""
        return due_date.strftime("%Y-%m-%d %H:%M")
