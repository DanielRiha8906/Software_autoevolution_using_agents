"""Dialog windows for the TODO Manager GUI."""

from datetime import datetime
from typing import Optional
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.ttk import Combobox

from ..models.task import Task
from ..models.task_status import TaskStatus


class AddTaskDialog:
    """Dialog to add a new task."""

    def __init__(self, parent: tk.Widget, projects_list: list[str]) -> None:
        """Initialize AddTaskDialog.

        Args:
            parent: Parent widget.
            projects_list: List of project IDs.
        """
        self.result = None
        self.parent = parent

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Task")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Title field
        tk.Label(self.dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.title_entry = tk.Entry(self.dialog, width=40)
        self.title_entry.grid(row=0, column=1, padx=10, pady=5)
        self.title_entry.focus()

        # Description field
        tk.Label(self.dialog, text="Description:").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        self.description_text = tk.Text(self.dialog, width=40, height=8)
        self.description_text.grid(row=1, column=1, padx=10, pady=5)

        # Project field
        tk.Label(self.dialog, text="Project:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        project_options = ["None"] + projects_list
        self.project_combo = Combobox(self.dialog, values=project_options, width=37, state="readonly")
        self.project_combo.set("None")
        self.project_combo.grid(row=2, column=1, padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(button_frame, text="Add", command=self._add).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="left", padx=5)

        self.dialog.wait_window()

    def _add(self) -> None:
        """Handle add button click."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title cannot be empty")
            return

        description = self.description_text.get("1.0", "end").strip()
        project_id = self.project_combo.get()
        if project_id == "None":
            project_id = None

        self.result = (title, description if description else None, project_id)
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Handle cancel button click."""
        self.dialog.destroy()


class ChangeStatusDialog:
    """Dialog to change task status."""

    def __init__(self, parent: tk.Widget, current_status: TaskStatus) -> None:
        """Initialize ChangeStatusDialog.

        Args:
            parent: Parent widget.
            current_status: The current task status.
        """
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Status")
        self.dialog.geometry("250x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text=f"Current: {current_status.value}").pack(pady=10)

        # Status buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Pending",
            command=lambda: self._select(TaskStatus.PENDING),
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="In Progress",
            command=lambda: self._select(TaskStatus.IN_PROGRESS),
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Done",
            command=lambda: self._select(TaskStatus.DONE),
        ).pack(side="left", padx=5)

        # Cancel button
        tk.Button(self.dialog, text="Cancel", command=self._cancel).pack(pady=10)

        self.dialog.wait_window()

    def _select(self, status: TaskStatus) -> None:
        """Select a status."""
        self.result = status
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Handle cancel button click."""
        self.dialog.destroy()


class ConfirmDeleteDialog:
    """Dialog to confirm task deletion."""

    def __init__(self, parent: tk.Widget, task_title: str) -> None:
        """Initialize ConfirmDeleteDialog.

        Args:
            parent: Parent widget.
            task_title: The task title to display in the confirmation message.
        """
        self.result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{task_title}'?",
            parent=parent,
        )


class SetDueDateDialog:
    """Dialog to set a task due date."""

    def __init__(self, parent: tk.Widget, current_due_date: Optional[datetime]) -> None:
        """Initialize SetDueDateDialog.

        Args:
            parent: Parent widget.
            current_due_date: The current due date, or None.
        """
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Set Due Date")
        self.dialog.geometry("350x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Date/Time (YYYY-MM-DD HH:MM):").pack(pady=5)

        self.date_entry = tk.Entry(self.dialog, width=30)
        self.date_entry.pack(pady=5)

        if current_due_date:
            self.date_entry.insert(0, current_due_date.strftime("%Y-%m-%d %H:%M"))

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Set", command=self._set).pack(side="left", padx=5)
        tk.Button(button_frame, text="Clear", command=self._clear).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="left", padx=5)

        self.dialog.wait_window()

    def _set(self) -> None:
        """Handle set button click."""
        date_str = self.date_entry.get().strip()
        if not date_str:
            messagebox.showerror("Error", "Please enter a date/time")
            return

        try:
            self.result = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD HH:MM")
            return

        self.dialog.destroy()

    def _clear(self) -> None:
        """Handle clear button click."""
        self.result = None
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Handle cancel button click."""
        self.dialog.destroy()


class UpdateTaskDialog:
    """Dialog to update task title and description."""

    def __init__(self, parent: tk.Widget, task: Task) -> None:
        """Initialize UpdateTaskDialog.

        Args:
            parent: Parent widget.
            task: The task to update.
        """
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Task")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Title field
        tk.Label(self.dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.title_entry = tk.Entry(self.dialog, width=40)
        self.title_entry.insert(0, task.title)
        self.title_entry.grid(row=0, column=1, padx=10, pady=5)
        self.title_entry.focus()

        # Description field
        tk.Label(self.dialog, text="Description:").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        self.description_text = tk.Text(self.dialog, width=40, height=8)
        if task.description:
            self.description_text.insert("1.0", task.description)
        self.description_text.grid(row=1, column=1, padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(button_frame, text="Update", command=self._update).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="left", padx=5)

        self.dialog.wait_window()

    def _update(self) -> None:
        """Handle update button click."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title cannot be empty")
            return

        description = self.description_text.get("1.0", "end").strip()
        self.result = (title, description if description else None)
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Handle cancel button click."""
        self.dialog.destroy()
