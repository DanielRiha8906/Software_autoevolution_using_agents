import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable, Optional

from ..models.task_status import TaskStatus
from ..utils.datetime_utils import parse_datetime_or_iso_string


class AddTaskDialog(tk.Toplevel):
    """Dialog for adding a new task."""

    def __init__(
        self,
        parent: tk.Widget,
        callback: Callable[[str, Optional[str], Optional[datetime], Optional[str]], None],
        projects: list[dict],
    ) -> None:
        """
        Initialize AddTaskDialog.

        Args:
            parent: Parent widget
            callback: Callback function (title, description, due_date, project_id)
            projects: List of project dicts with 'id' and 'name' keys
        """
        super().__init__(parent)
        self.title("Add Task")
        self.geometry("400x300")
        self.callback = callback
        self.projects = projects
        self.result = None

        self._build_widgets()
        self.transient(parent)
        self.grab_set()

    def _build_widgets(self) -> None:
        """Build dialog widgets."""
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(frame, text="Title (required):").grid(row=0, column=0, sticky=tk.W)
        self.title_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.title_var, width=40).grid(
            row=0, column=1, sticky=tk.EW
        )

        # Description
        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var, width=40).grid(
            row=1, column=1, sticky=tk.EW
        )

        # Due date
        ttk.Label(frame, text="Due date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W)
        self.due_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.due_var, width=40).grid(
            row=2, column=1, sticky=tk.EW
        )

        # Project
        ttk.Label(frame, text="Project:").grid(row=3, column=0, sticky=tk.W)
        self.project_var = tk.StringVar()
        project_options = ["None"] + [f"{p['id'][:8]}  {p['name']}" for p in self.projects]
        project_combo = ttk.Combobox(
            frame,
            textvariable=self.project_var,
            values=project_options,
            state="readonly",
            width=37,
        )
        project_combo.grid(row=3, column=1, sticky=tk.EW)
        if project_options:
            project_combo.current(0)
        self.project_options = project_options

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)

        frame.columnconfigure(1, weight=1)

    def on_ok(self) -> None:
        """Handle OK button click."""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Title cannot be empty")
            return

        description = self.desc_var.get().strip() or None
        due_date = None
        due_str = self.due_var.get().strip()
        if due_str:
            try:
                due_date = parse_datetime_or_iso_string(due_str)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid due date: {e}")
                return

        project_id = None
        project_sel = self.project_var.get()
        if project_sel and project_sel != "None":
            # Extract project ID from the selection
            idx = self.project_options.index(project_sel)
            if idx > 0:
                project_id = self.projects[idx - 1]["id"]

        self.callback(title, description, due_date, project_id)
        self.destroy()

    def on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.destroy()


class ViewTaskDialog(tk.Toplevel):
    """Dialog for viewing task details (read-only)."""

    def __init__(self, parent: tk.Widget, task: dict) -> None:
        """
        Initialize ViewTaskDialog.

        Args:
            parent: Parent widget
            task: Task dict with keys: id, title, description, status, created_at, updated_at, due_date, project_id
        """
        super().__init__(parent)
        self.title("View Task")
        self.geometry("500x400")
        self.task = task

        self._build_widgets()
        self.transient(parent)
        self.grab_set()

    def _build_widgets(self) -> None:
        """Build dialog widgets."""
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Display task details
        row = 0
        details = [
            ("ID:", self.task.get("id", "—")),
            ("Title:", self.task.get("title", "—")),
            ("Description:", self.task.get("description") or "—"),
            ("Status:", self.task.get("status", "—")),
            ("Created:", self.task.get("created_at", "—")),
            ("Updated:", self.task.get("updated_at", "—")),
            ("Due date:", self.task.get("due_date") or "—"),
            ("Project ID:", self.task.get("project_id") or "—"),
        ]

        for label_text, value in details:
            ttk.Label(frame, text=label_text, font=("TkDefaultFont", 9, "bold")).grid(
                row=row, column=0, sticky=tk.NW, pady=5
            )
            ttk.Label(frame, text=str(value), wraplength=300, justify=tk.LEFT).grid(
                row=row, column=1, sticky=tk.NW, padx=10, pady=5
            )
            row += 1

        # Close button
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack()


class ConfirmDialog(tk.Toplevel):
    """Yes/No confirmation dialog."""

    def __init__(
        self, parent: tk.Widget, title: str, message: str, callback: Callable[[bool], None]
    ) -> None:
        """
        Initialize ConfirmDialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Confirmation message
            callback: Callback function (True for yes, False for no)
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.callback = callback
        self.result = False

        self._build_widgets(message)
        self.transient(parent)
        self.grab_set()

    def _build_widgets(self, message: str) -> None:
        """Build dialog widgets."""
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=message, wraplength=280, justify=tk.CENTER).pack(pady=20)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Yes", command=self.on_yes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="No", command=self.on_no).pack(side=tk.LEFT, padx=5)

    def on_yes(self) -> None:
        """Handle Yes button click."""
        self.result = True
        self.callback(True)
        self.destroy()

    def on_no(self) -> None:
        """Handle No button click."""
        self.result = False
        self.callback(False)
        self.destroy()
