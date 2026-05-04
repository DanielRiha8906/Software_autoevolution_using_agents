"""Main GUI window for the TODO Manager."""

from datetime import datetime
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox

from ..models.task_status import TaskStatus
from ..services import TodoService, TaskNotFoundError
from .styles import COLORS, FONTS, TREEVIEW_TAGS
from .task_display import TaskRow
from .dialogs import (
    AddTaskDialog,
    ChangeStatusDialog,
    ConfirmDeleteDialog,
    SetDueDateDialog,
    UpdateTaskDialog,
)


class TodoGUI:
    """Main window for the TODO Manager GUI."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the TODO GUI.

        Args:
            storage_path: Optional path to the storage file.
        """
        self.service = TodoService()
        if storage_path:
            from ..storage.json_storage import JsonStorage
            storage = JsonStorage(storage_path)
            self.service = TodoService(storage)

        self.root = tk.Tk()
        self.root.title("TODO Manager")
        self.root.geometry("900x600")

        self.filter_status: Optional[TaskStatus] = None
        self.filter_project: Optional[str] = None

        self._build_ui()
        self.refresh_task_list()

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Header
        header_frame = tk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=10)

        title_label = tk.Label(header_frame, text="TODO Manager", font=FONTS["title"])
        title_label.pack(anchor="w")

        # Filter frame
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Status:").pack(side="left", padx=5)
        self.status_combo = ttk.Combobox(
            filter_frame,
            values=["All", "pending", "in_progress", "done"],
            state="readonly",
            width=15,
        )
        self.status_combo.set("All")
        self.status_combo.pack(side="left", padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", lambda _: self._on_filter_changed())

        tk.Label(filter_frame, text="Project:").pack(side="left", padx=5)
        self.project_combo = ttk.Combobox(filter_frame, state="readonly", width=15)
        self.project_combo.set("None")
        self.project_combo.pack(side="left", padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", lambda _: self._on_filter_changed())

        # Treeview
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        self.treeview = ttk.Treeview(
            tree_frame,
            columns=("Status", "Title", "Due Date", "Project", "ID"),
            height=15,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
        )
        tree_scroll_y.config(command=self.treeview.yview)
        tree_scroll_x.config(command=self.treeview.xview)

        # Configure columns
        self.treeview.column("#0", width=0, stretch=False)
        self.treeview.column("Status", anchor="center", width=50)
        self.treeview.column("Title", anchor="w", width=300)
        self.treeview.column("Due Date", anchor="center", width=120)
        self.treeview.column("Project", anchor="w", width=150)
        self.treeview.column("ID", anchor="w", width=0, stretch=False)

        self.treeview.heading("#0", text="")
        self.treeview.heading("Status", text="Status")
        self.treeview.heading("Title", text="Title")
        self.treeview.heading("Due Date", text="Due Date")
        self.treeview.heading("Project", text="Project")
        self.treeview.heading("ID", text="ID")

        # Configure tags for styling
        self.treeview.tag_configure("overdue", **TREEVIEW_TAGS["overdue"])
        self.treeview.tag_configure("normal", **TREEVIEW_TAGS["normal"])

        self.treeview.pack(fill="both", expand=True)

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(button_frame, text="Add Task", command=self.on_add_task).pack(side="left", padx=5)
        tk.Button(button_frame, text="Change Status", command=self.on_change_status).pack(side="left", padx=5)
        tk.Button(button_frame, text="Update", command=self.on_update_task).pack(side="left", padx=5)
        tk.Button(button_frame, text="Set Due Date", command=self.on_set_due_date).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", command=self.on_delete_task).pack(side="left", padx=5)

        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="",
            bg="#f0f0f0",
            anchor="w",
            padx=10,
            pady=5,
        )
        self.status_bar.pack(fill="x", side="bottom")

    def _update_project_combo(self) -> None:
        """Update project combo with current projects."""
        projects = self.service.list_projects()
        project_names = [p.name for p in projects]
        project_options = ["None"] + project_names
        self.project_combo["values"] = project_options
        if self.project_combo.get() not in project_options:
            self.project_combo.set("None")

    def _on_filter_changed(self) -> None:
        """Handle filter change."""
        status_str = self.status_combo.get()
        project_name = self.project_combo.get()

        # Convert status string to TaskStatus or None
        filter_status = None
        if status_str != "All":
            filter_status = TaskStatus(status_str)

        # Convert project name to project_id or None
        filter_project = None
        if project_name != "None":
            projects = self.service.list_projects()
            for project in projects:
                if project.name == project_name:
                    filter_project = project.id
                    break

        self.apply_filter(filter_status, filter_project)

    def apply_filter(
        self,
        status: Optional[TaskStatus] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """Apply filter to task list.

        Args:
            status: Optional status filter.
            project_id: Optional project ID filter.
        """
        self.filter_status = status
        self.filter_project = project_id
        self.refresh_task_list(status, project_id)

    def refresh_task_list(
        self,
        filter_status: Optional[TaskStatus] = None,
        filter_project: Optional[str] = None,
    ) -> None:
        """Refresh the task list display.

        Args:
            filter_status: Optional status filter.
            filter_project: Optional project ID filter.
        """
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        # Get tasks with filters
        tasks = self.service.list_tasks(status=filter_status, project_id=filter_project)

        # Build project name map
        projects = {p.id: p.name for p in self.service.list_projects()}

        # Add tasks to treeview
        for task in tasks:
            project_name = projects.get(task.project_id, "") if task.project_id else ""
            row = TaskRow(task, project_name)
            values = row.format_for_treeview()
            tag = row.get_tag()
            self.treeview.insert("", "end", values=values, tags=(tag,))

        # Update status bar
        all_tasks = self.service.list_tasks()
        total_count = len(all_tasks)
        overdue_count = len([t for t in all_tasks if t.is_overdue()])
        completed_count = len([t for t in all_tasks if t.is_completed()])

        status_text = f"{total_count} tasks • {overdue_count} overdue • {completed_count} completed"
        self.status_bar.config(text=status_text)

        # Update project combo
        self._update_project_combo()

    def get_selected_task(self) -> str:
        """Get the ID of the selected task.

        Returns:
            The task ID.

        Raises:
            ValueError: If no task is selected.
        """
        selection = self.treeview.selection()
        if not selection:
            raise ValueError("No task selected")

        item = selection[0]
        values = self.treeview.item(item, "values")
        # Task ID is the last column
        task_id = values[4]
        return task_id

    def on_add_task(self) -> None:
        """Handle add task button click."""
        projects = self.service.list_projects()
        project_ids = [p.id for p in projects]

        dialog = AddTaskDialog(self.root, project_ids)
        if dialog.result:
            try:
                title, description, project_id = dialog.result
                self.service.add_task(title, description, project_id)
                self.refresh_task_list(self.filter_status, self.filter_project)
                messagebox.showinfo("Success", f"Task '{title}' added successfully")
            except ValueError as e:
                self.show_error("Error", str(e))

    def on_change_status(self) -> None:
        """Handle change status button click."""
        try:
            task_id = self.get_selected_task()
            task = self.service.get_task(task_id)

            dialog = ChangeStatusDialog(self.root, task.status)
            if dialog.result:
                new_status = dialog.result
                if new_status == TaskStatus.PENDING:
                    self.service.reopen_task(task_id)
                elif new_status == TaskStatus.IN_PROGRESS:
                    self.service.start_task(task_id)
                elif new_status == TaskStatus.DONE:
                    self.service.complete_task(task_id)

                self.refresh_task_list(self.filter_status, self.filter_project)
        except ValueError as e:
            self.show_error("Error", str(e))
        except TaskNotFoundError:
            self.show_error("Error", "Task not found")

    def on_update_task(self) -> None:
        """Handle update task button click."""
        try:
            task_id = self.get_selected_task()
            task = self.service.get_task(task_id)

            dialog = UpdateTaskDialog(self.root, task)
            if dialog.result:
                new_title, new_description = dialog.result
                self.service.update_task(task_id, new_title, new_description)
                self.refresh_task_list(self.filter_status, self.filter_project)
                messagebox.showinfo("Success", "Task updated successfully")
        except ValueError as e:
            self.show_error("Error", str(e))
        except TaskNotFoundError:
            self.show_error("Error", "Task not found")

    def on_set_due_date(self) -> None:
        """Handle set due date button click."""
        try:
            task_id = self.get_selected_task()
            task = self.service.get_task(task_id)

            dialog = SetDueDateDialog(self.root, task.due_date)
            if dialog.result is not None or (hasattr(dialog, 'result') and dialog.result is None):
                self.service.set_due_date(task_id, dialog.result)
                self.refresh_task_list(self.filter_status, self.filter_project)
                messagebox.showinfo("Success", "Due date updated successfully")
        except ValueError as e:
            self.show_error("Error", str(e))
        except TaskNotFoundError:
            self.show_error("Error", "Task not found")

    def on_delete_task(self) -> None:
        """Handle delete task button click."""
        try:
            task_id = self.get_selected_task()
            task = self.service.get_task(task_id)

            dialog = ConfirmDeleteDialog(self.root, task.title)
            if dialog.result:
                self.service.delete_task(task_id)
                self.refresh_task_list(self.filter_status, self.filter_project)
                messagebox.showinfo("Success", "Task deleted successfully")
        except ValueError as e:
            self.show_error("Error", str(e))
        except TaskNotFoundError:
            self.show_error("Error", "Task not found")

    def show_error(self, title: str, message: str) -> None:
        """Show an error dialog.

        Args:
            title: Dialog title.
            message: Error message.
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """Show an info dialog.

        Args:
            title: Dialog title.
            message: Info message.
        """
        messagebox.showinfo(title, message)

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()
