"""TodoGUI - tkinter-based graphical user interface for task management."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from ..services.todo_service import TodoService
from ..models.task_status import TaskStatus


class TodoGUI:
    """A tkinter GUI for managing TODO tasks using the TodoService."""

    def __init__(self, service: TodoService) -> None:
        """
        Initialize the TodoGUI with a TodoService instance.

        Args:
            service: The TodoService instance to use for all task operations.
        """
        self.service = service
        self.root: Optional[tk.Tk] = None
        self.tree: Optional[ttk.Treeview] = None

        # Status filter variable
        self.filter_status: Optional[TaskStatus] = None
        self.filter_overdue: bool = False

    def _ensure_root(self) -> None:
        """Ensure that the tkinter root window is initialized."""
        if self.root is None:
            self.root = tk.Tk()
            self.root.title("TODO Manager")
            self.root.geometry("900x600")
            self._create_widgets()
            self._refresh_task_list()

    def _create_widgets(self) -> None:
        """Create the main GUI widgets."""
        if self.root is None:
            raise RuntimeError("Root window not initialized")
        # Top frame for controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Filter buttons
        ttk.Button(control_frame, text="All Tasks", command=self._show_all).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(control_frame, text="Pending", command=self._show_pending).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(
            control_frame, text="In Progress", command=self._show_in_progress
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Done", command=self._show_done).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(control_frame, text="Overdue", command=self._show_overdue).pack(
            side=tk.LEFT, padx=2
        )

        # Action buttons frame
        action_frame = ttk.Frame(self.root)
        action_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="Add Task", command=self._add_task).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Start Task", command=self._start_task).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Complete Task", command=self._complete_task).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Reopen Task", command=self._reopen_task).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Delete Task", command=self._delete_task).pack(
            side=tk.LEFT, padx=2
        )

        # Task list frame
        list_frame = ttk.Frame(self.root)
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview for task display
        self.tree = ttk.Treeview(
            list_frame,
            columns=("id", "title", "status", "due_date", "project"),
            height=15,
        )
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("id", anchor=tk.W, width=40)
        self.tree.column("title", anchor=tk.W, width=250)
        self.tree.column("status", anchor=tk.W, width=100)
        self.tree.column("due_date", anchor=tk.W, width=150)
        self.tree.column("project", anchor=tk.W, width=100)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("id", text="ID", anchor=tk.W)
        self.tree.heading("title", text="Title", anchor=tk.W)
        self.tree.heading("status", text="Status", anchor=tk.W)
        self.tree.heading("due_date", text="Due Date", anchor=tk.W)
        self.tree.heading("project", text="Project", anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh_task_list(self) -> None:
        """Refresh the task list display with current filter."""
        if self.tree is None:
            return
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get filtered tasks
        tasks = self.service.list_tasks(
            status=self.filter_status, overdue=self.filter_overdue if self.filter_overdue else None
        )

        # Display tasks
        for task in tasks:
            due_date_str = (
                task.due_date.isoformat() if task.due_date else ""
            )
            project_str = task.project_id or ""

            # Determine if task is overdue
            is_overdue = task.is_overdue()

            # Create item ID for reference
            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    task.id[:8],
                    task.title,
                    task.status.value,
                    due_date_str,
                    project_str,
                ),
            )

            # Highlight overdue tasks
            if is_overdue:
                self.tree.item(item_id, tags=("overdue",))

        # Configure tag colors
        self.tree.tag_configure("overdue", foreground="red")

    def _show_all(self) -> None:
        """Show all tasks."""
        self.filter_status = None
        self.filter_overdue = False
        self._refresh_task_list()

    def _show_pending(self) -> None:
        """Show pending tasks."""
        self.filter_status = TaskStatus.PENDING
        self.filter_overdue = False
        self._refresh_task_list()

    def _show_in_progress(self) -> None:
        """Show in-progress tasks."""
        self.filter_status = TaskStatus.IN_PROGRESS
        self.filter_overdue = False
        self._refresh_task_list()

    def _show_done(self) -> None:
        """Show completed tasks."""
        self.filter_status = TaskStatus.DONE
        self.filter_overdue = False
        self._refresh_task_list()

    def _show_overdue(self) -> None:
        """Show overdue tasks."""
        self.filter_status = None
        self.filter_overdue = True
        self._refresh_task_list()

    def _get_selected_task_id(self) -> Optional[str]:
        """Get the ID of the currently selected task."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return None
        return selection[0]

    def _add_task(self) -> None:
        """Add a new task through a dialog."""
        title = simpledialog.askstring("Add Task", "Enter task title:")
        if not title:
            return

        description = simpledialog.askstring(
            "Add Task", "Enter task description (optional):", show=""
        )
        project_id = simpledialog.askstring(
            "Add Task", "Enter project ID (optional):", show=""
        )

        try:
            self.service.add_task(
                title=title,
                description=description if description else None,
                project_id=project_id if project_id else None,
            )
            self._refresh_task_list()
            messagebox.showinfo("Success", f"Task '{title}' added successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _start_task(self) -> None:
        """Start the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        # Extract task ID from the row
        item = selected[0]
        values = self.tree.item(item, "values")
        task_id = self._find_task_id_by_display_id(values[0])

        if not task_id:
            messagebox.showerror("Error", "Could not find task.")
            return

        try:
            self.service.start_task(task_id)
            self._refresh_task_list()
            messagebox.showinfo("Success", "Task started.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _complete_task(self) -> None:
        """Complete the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        item = selected[0]
        values = self.tree.item(item, "values")
        task_id = self._find_task_id_by_display_id(values[0])

        if not task_id:
            messagebox.showerror("Error", "Could not find task.")
            return

        try:
            self.service.complete_task(task_id)
            self._refresh_task_list()
            messagebox.showinfo("Success", "Task completed.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _reopen_task(self) -> None:
        """Reopen the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        item = selected[0]
        values = self.tree.item(item, "values")
        task_id = self._find_task_id_by_display_id(values[0])

        if not task_id:
            messagebox.showerror("Error", "Could not find task.")
            return

        try:
            self.service.reopen_task(task_id)
            self._refresh_task_list()
            messagebox.showinfo("Success", "Task reopened.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _delete_task(self) -> None:
        """Delete the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        item = selected[0]
        values = self.tree.item(item, "values")
        task_id = self._find_task_id_by_display_id(values[0])

        if not task_id:
            messagebox.showerror("Error", "Could not find task.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            try:
                self.service.delete_task(task_id)
                self._refresh_task_list()
                messagebox.showinfo("Success", "Task deleted.")
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def _find_task_id_by_display_id(self, display_id: str) -> Optional[str]:
        """Find the full task ID by its display ID (first 8 characters)."""
        tasks = self.service.list_tasks()
        for task in tasks:
            if task.id.startswith(display_id):
                return task.id
        return None

    def run(self) -> None:
        """Start the GUI event loop."""
        self._ensure_root()
        if self.root is not None:
            self.root.mainloop()


def main() -> None:
    """Launch the TODO GUI application."""
    from ..services.todo_service import TodoService

    service = TodoService()
    gui = TodoGUI(service)
    gui.run()


if __name__ == "__main__":
    main()
