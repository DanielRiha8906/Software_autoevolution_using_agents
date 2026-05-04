"""Dialog for adding a new task."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone

from .base_dialog import BaseDialog


class AddTaskDialog(BaseDialog):
    """Dialog for creating a new task."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the add task dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent, "Add Task")

    def _create_widgets(self) -> None:
        """Create form widgets."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(frame, width=40, height=6)
        self.desc_text.grid(row=1, column=1, sticky=tk.EW + tk.NS, pady=5)

        ttk.Label(frame, text="Due Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.due_date_entry = ttk.Entry(frame, width=40)
        self.due_date_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text="Project:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.project_var = tk.StringVar(value="")
        self.project_combo = ttk.Combobox(frame, textvariable=self.project_var, width=37)
        self.project_combo.grid(row=3, column=1, sticky=tk.EW, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self.title_entry.focus()

    def get_task_data(self) -> dict:
        """Get the entered task data.

        Returns:
            Dictionary with title, description, due_date, and project_id
        """
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        due_date_str = self.due_date_entry.get().strip()
        project_id = self.project_var.get().strip() or None

        due_date = None
        if due_date_str:
            try:
                parsed = datetime.strptime(due_date_str, "%Y-%m-%d")
                due_date = parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid date format: {due_date_str}. Use YYYY-MM-DD.")

        return {
            "title": title,
            "description": description if description else None,
            "due_date": due_date,
            "project_id": project_id,
        }

    def set_projects(self, projects: list[tuple[str, str]]) -> None:
        """Set available projects for dropdown.

        Args:
            projects: List of (project_id, project_name) tuples
        """
        self.project_combo["values"] = [name for _, name in projects]
        self._project_id_map = {name: proj_id for proj_id, name in projects}

    def _on_ok(self) -> None:
        """Validate and close dialog."""
        try:
            data = self.get_task_data()
            if not data["title"]:
                raise ValueError("Task title cannot be empty")
            self.result = data
            self.destroy()
        except ValueError as e:
            from tkinter import messagebox

            messagebox.showerror("Invalid Input", str(e))
