"""TodoGUI: tkinter-based GUI for task management."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..formatters.task_formatter import TaskFormatter
from ..services.todo_service import TodoService


class TodoGUI:
    """Tkinter-based GUI for managing tasks.

    Provides a windowed interface for adding, updating, deleting, and
    filtering tasks. Uses service injection for all data operations.
    """

    def __init__(self, service: TodoService) -> None:
        """Initialize TodoGUI with an injected service instance.

        Args:
            service: A TodoService instance for task operations.
        """
        self.service = service
        self.task_widgets: Dict[str, tk.Widget] = {}
        self.current_filter: Dict[str, Optional[str]] = {
            "status": None,
            "project": None,
        }
        self.selected_task_id: Optional[str] = None

        try:
            self.root = tk.Tk()
            self.root.title("Todo Manager")
            self.root.geometry("800x600")
            self._create_widgets()
            self._refresh_task_list()
        except tk.TclError:
            # Headless environment - store None root for testing
            self.root = None

    def _create_widgets(self) -> None:
        """Initialize all tkinter widgets and layout."""
        # Top control frame
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(top_frame, text="Todo Manager", font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self._refresh_task_list)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Input/Action frame
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="New Task:").pack(side=tk.LEFT, padx=5)
        self.task_input = ttk.Entry(input_frame, width=40)
        self.task_input.pack(side=tk.LEFT, padx=5)
        self.task_input.bind("<Return>", lambda e: self._handle_add_task())

        add_btn = ttk.Button(input_frame, text="Add", command=self._handle_add_task)
        add_btn.pack(side=tk.LEFT, padx=5)

        # Filter buttons frame
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="All", command=self._filter_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Pending", command=self._filter_pending).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="In Progress", command=self._filter_in_progress).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Done", command=self._filter_done).pack(side=tk.LEFT, padx=2)

        # Task list frame (scrollable)
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.task_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            height=15,
        )
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.task_listbox.yview)
        self.task_listbox.bind("<<ListboxSelect>>", self._on_task_select_event)

        # Task details frame
        details_frame = ttk.LabelFrame(self.root, text="Task Actions", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=5)

        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Start", command=self._handle_start_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Complete", command=self._handle_complete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reopen", command=self._handle_reopen_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self._handle_delete_task).pack(side=tk.LEFT, padx=5)

        self.details_text = tk.Text(details_frame, height=4, width=80, state=tk.DISABLED)
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def _refresh_task_list(self) -> None:
        """Reload tasks from service and update display."""
        if self.root is None:
            # Headless mode - skip widget updates but still validate service
            try:
                status = None
                if self.current_filter["status"] == "pending":
                    status = TaskStatus.PENDING
                elif self.current_filter["status"] == "in_progress":
                    status = TaskStatus.IN_PROGRESS
                elif self.current_filter["status"] == "done":
                    status = TaskStatus.DONE

                self.service.list_tasks(
                    status=status,
                    project_id=self.current_filter.get("project"),
                )
            except Exception:
                pass
            return

        try:
            status = None
            if self.current_filter["status"] == "pending":
                status = TaskStatus.PENDING
            elif self.current_filter["status"] == "in_progress":
                status = TaskStatus.IN_PROGRESS
            elif self.current_filter["status"] == "done":
                status = TaskStatus.DONE

            tasks = self.service.list_tasks(
                status=status,
                project_id=self.current_filter.get("project"),
            )

            self.task_listbox.delete(0, tk.END)
            self.task_widgets.clear()

            for task in tasks:
                display_text = self._display_task_line(task)
                self.task_listbox.insert(tk.END, display_text)
                self.task_widgets[task.id] = task

                # Apply red color for overdue tasks
                if task.is_overdue():
                    index = self.task_listbox.size() - 1
                    self.task_listbox.itemconfig(index, fg="red")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh task list: {str(e)}")

    def _display_task_line(self, task: Task) -> str:
        """Render a single task with status symbol and details.

        Args:
            task: The task to display.

        Returns:
            Formatted task line string.
        """
        symbol = TaskFormatter.get_status_symbol(task.status)
        line = f"{symbol} {task.id[:8]}  {task.title}"
        if task.due_date:
            line += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
        if task.project_id:
            line += f" [{task.project_id[:8]}]"
        return line

    def _on_task_select_event(self, event) -> None:
        """Handle task selection from the listbox."""
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            display_text = self.task_listbox.get(index)
            # Extract task ID from display text (8 chars after status symbol)
            task_id_start = display_text.find(" ") + 1
            task_id = display_text[task_id_start:task_id_start + 8]

            # Find the actual task by ID prefix
            for task_id_full, task in self.task_widgets.items():
                if task_id_full.startswith(task_id):
                    self._on_task_select(task_id_full)
                    break

    def _on_task_select(self, task_id: str) -> None:
        """Display selected task details.

        Args:
            task_id: The ID of the selected task.
        """
        self.selected_task_id = task_id
        try:
            task = self.service.get_task(task_id)
            details = f"""ID: {task.id}
Title: {task.title}
Status: {task.status.value}
Description: {task.description or '—'}
Created: {task.created_at.isoformat() if task.created_at else '—'}
Due: {task.due_date.isoformat() if task.due_date else '—'}
Overdue: {'Yes' if task.is_overdue() else 'No'}"""

            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details)
            self.details_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load task details: {str(e)}")

    def _handle_add_task(self) -> None:
        """Add a new task via service."""
        title = self.task_input.get().strip()
        if not title:
            messagebox.showwarning("Input Error", "Please enter a task title")
            return

        try:
            self.service.add_task(title)
            self.task_input.delete(0, tk.END)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add task: {str(e)}")

    def _handle_start_task(self) -> None:
        """Start the selected task."""
        if not self.selected_task_id:
            messagebox.showwarning("Selection Error", "Please select a task")
            return

        try:
            self.service.start_task(self.selected_task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start task: {str(e)}")

    def _handle_complete_task(self) -> None:
        """Mark the selected task as complete."""
        if not self.selected_task_id:
            messagebox.showwarning("Selection Error", "Please select a task")
            return

        try:
            self.service.complete_task(self.selected_task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete task: {str(e)}")

    def _handle_reopen_task(self) -> None:
        """Reopen the selected task."""
        if not self.selected_task_id:
            messagebox.showwarning("Selection Error", "Please select a task")
            return

        try:
            self.service.reopen_task(self.selected_task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reopen task: {str(e)}")

    def _handle_delete_task(self) -> None:
        """Delete the selected task with confirmation."""
        if not self.selected_task_id:
            messagebox.showwarning("Selection Error", "Please select a task")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            try:
                self.service.delete_task(self.selected_task_id)
                self._refresh_task_list()
                self.selected_task_id = None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {str(e)}")

    def _filter_all(self) -> None:
        """Show all tasks."""
        self.current_filter["status"] = None
        self._refresh_task_list()

    def _filter_pending(self) -> None:
        """Show only pending tasks."""
        self.current_filter["status"] = "pending"
        self._refresh_task_list()

    def _filter_in_progress(self) -> None:
        """Show only in-progress tasks."""
        self.current_filter["status"] = "in_progress"
        self._refresh_task_list()

    def _filter_done(self) -> None:
        """Show only completed tasks."""
        self.current_filter["status"] = "done"
        self._refresh_task_list()

    def run(self) -> None:
        """Start the GUI event loop."""
        if self.root is not None:
            self.root.mainloop()
