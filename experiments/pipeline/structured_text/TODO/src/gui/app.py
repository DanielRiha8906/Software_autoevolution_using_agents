"""Main GUI application window."""

import tkinter as tk
from tkinter import messagebox
from typing import Optional

from ..container import Container
from ..models.task_status import TaskStatus
from ..exceptions import TaskNotFoundError
from .widgets.task_list import TaskListWidget
from .widgets.filter_bar import FilterBar
from .widgets.action_bar import ActionBar
from .dialogs.add_task import AddTaskDialog
from .dialogs.edit_task import EditTaskDialog
from .dialogs.delete_confirm import DeleteConfirmDialog


class GUIApp(tk.Tk):
    """Main GUI application window."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the GUI application.

        Args:
            storage_path: Optional custom path for task storage
        """
        super().__init__()
        self.title("TODO Manager")
        self.geometry("900x600")

        self.container = Container(storage_path)
        self.service = self.container.get_todo_service()

        self._create_widgets()
        self._refresh_tasks()

    def _create_widgets(self) -> None:
        """Create main window widgets."""
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.action_bar = ActionBar(
            main_frame,
            on_add=self._on_add_task,
            on_edit=self._on_edit_task,
            on_delete=self._on_delete_task,
            on_refresh=self._refresh_tasks,
        )
        self.action_bar.pack(fill=tk.X, pady=5)

        self.filter_bar = FilterBar(main_frame, on_filter_change=self._on_filter_change)
        self.filter_bar.pack(fill=tk.X, padx=5, pady=5)

        self.task_list = TaskListWidget(
            main_frame,
            on_select=self._on_task_select,
            on_double_click=self._on_task_double_click,
        )
        self.task_list.pack(fill=tk.BOTH, expand=True)

        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = tk.Label(status_frame, text="Ready", font=("Arial", 9))
        self.status_label.pack(side=tk.LEFT)

        self._selected_task_id: Optional[str] = None

    def _refresh_tasks(self) -> None:
        """Refresh task list from service."""
        try:
            status_filter = self.filter_bar.get_status_filter()
            status = None
            if status_filter:
                status = TaskStatus(status_filter)

            tasks = self.service.list_tasks(status=status)

            self.task_list.clear()

            projects = self.service.list_projects()
            project_map = {p.id: p.name for p in projects}
            self.filter_bar.set_projects([(p.id, p.name) for p in projects])

            for task in tasks:
                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "due_date": task.due_date,
                    "project_name": project_map.get(task.project_id) if task.project_id else "",
                }
                is_overdue = task.is_overdue()
                self.task_list.add_task(task_dict, is_overdue)

            self.status_label.config(text=f"Loaded {len(tasks)} tasks")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {str(e)}")
            self.status_label.config(text="Error loading tasks")

    def _on_filter_change(self) -> None:
        """Handle filter change."""
        self._refresh_tasks()

    def _on_task_select(self, task_id: str) -> None:
        """Handle task selection.

        Args:
            task_id: ID of selected task
        """
        self._selected_task_id = task_id
        try:
            task = self.service.get_task(task_id)
            self.status_label.config(text=f"Selected: {task.title}")
        except TaskNotFoundError:
            self.status_label.config(text="Task not found")

    def _on_task_double_click(self, task_id: str) -> None:
        """Handle task double-click (edit).

        Args:
            task_id: ID of task to edit
        """
        self._selected_task_id = task_id
        self._on_edit_task()

    def _on_add_task(self) -> None:
        """Handle Add Task button."""
        dialog = AddTaskDialog(self)

        projects = self.service.list_projects()
        dialog.set_projects([(p.id, p.name) for p in projects])

        self.wait_window(dialog)

        if dialog.result:
            try:
                task_data = dialog.result
                task = self.service.add_task(task_data["title"], task_data["description"])

                if task_data.get("due_date"):
                    task.due_date = task_data["due_date"]

                if task_data.get("project_id"):
                    task.project_id = task_data["project_id"]

                task_repo = self.container.get_task_repository()
                task_repo._items[task.id] = task
                task_repo._persist()

                self._refresh_tasks()
                self.status_label.config(text=f"Added: {task.title}")
            except ValueError as e:
                messagebox.showerror("Error", f"Failed to add task: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")

    def _on_edit_task(self) -> None:
        """Handle Edit button."""
        if not self._selected_task_id:
            messagebox.showwarning("No Selection", "Please select a task to edit")
            return

        try:
            task = self.service.get_task(self._selected_task_id)

            projects = self.service.list_projects()
            project_map = {p.id: p.name for p in projects}

            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "due_date": task.due_date,
                "project_id": task.project_id,
                "project_name": project_map.get(task.project_id) if task.project_id else "",
            }

            dialog = EditTaskDialog(self, task_dict)
            dialog.set_projects([(p.id, p.name) for p in projects])

            self.wait_window(dialog)

            if dialog.result:
                data = dialog.result
                self.service.update_task(task.id, title=data["title"], description=data["description"])

                updated_task = self.service.get_task(task.id)
                updated_task.due_date = data["due_date"]
                updated_task.project_id = data["project_id"]

                task_repo = self.container.get_task_repository()
                task_repo._items[updated_task.id] = updated_task
                task_repo._persist()

                self._refresh_tasks()
                self.status_label.config(text=f"Updated: {updated_task.title}")
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit task: {str(e)}")

    def _on_delete_task(self) -> None:
        """Handle Delete button."""
        if not self._selected_task_id:
            messagebox.showwarning("No Selection", "Please select a task to delete")
            return

        try:
            task = self.service.get_task(self._selected_task_id)
            dialog = DeleteConfirmDialog(self, task.title)
            self.wait_window(dialog)

            if dialog.result:
                self.service.delete_task(task.id)
                self._selected_task_id = None
                self._refresh_tasks()
                self.status_label.config(text="Task deleted")
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {str(e)}")
