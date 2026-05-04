"""GUI implementation for TODO application using tkinter."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from pathlib import Path

from ..models import Task, TaskStatus, TaskComment, Project
from ..services import TodoService, TaskNotFoundError, ProjectNotFoundError


class TodoGUI:
    """Main GUI application window for TODO management."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the GUI with optional custom storage path.

        Args:
            storage_path: Optional path to JSON storage file. Defaults to ~/.todo/tasks.json.
        """
        self.service = TodoService()
        self.root = tk.Tk()
        self.root.title("TODO Manager")
        self.root.geometry("1000x700")

        # State for tracking selected task and current filters
        self.selected_task: Optional[Task] = None
        self.current_status_filter: Optional[TaskStatus] = None
        self.current_project_filter: Optional[str] = None
        self.current_overdue_filter: bool = False

        # Create GUI components
        self.main_window = MainWindow(self.root, self)
        self._setup_bindings()

    def _setup_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        self.root.bind("<Control-n>", lambda e: self._on_add_task())
        self.root.bind("<Control-r>", lambda e: self._refresh())
        self.root.bind("<Delete>", lambda e: self._on_delete_task())

    def _on_add_task(self) -> None:
        """Handle add task keyboard shortcut."""
        self.main_window.action_frame.on_add_task()

    def _on_delete_task(self) -> None:
        """Handle delete task keyboard shortcut."""
        self.main_window.action_frame.on_delete_task()

    def _refresh(self) -> None:
        """Refresh the task list with current filters."""
        self.main_window.task_list_frame.refresh_tasks(
            status=self.current_status_filter,
            project_id=self.current_project_filter,
            overdue_only=self.current_overdue_filter,
        )

    def select_task(self, task: Optional[Task]) -> None:
        """Select a task and update the details panel.

        Args:
            task: Task to select or None to clear selection.
        """
        self.selected_task = task
        if task:
            self.main_window.task_details_frame.display_task(task)
        else:
            self.main_window.task_details_frame.clear()

    def run(self) -> None:
        """Launch the GUI mainloop."""
        self.root.mainloop()


class MainWindow:
    """Main window container with menu bar and frames."""

    def __init__(self, root: tk.Tk, gui: TodoGUI) -> None:
        """Initialize the main window layout.

        Args:
            root: Tk root window.
            gui: Parent TodoGUI instance.
        """
        self.gui = gui
        self.root = root

        # Create frames
        self.filter_frame = FilterFrame(root, gui)
        self.task_list_frame = TaskListFrame(root, gui)
        self.task_details_frame = TaskDetailsFrame(root, gui)
        self.action_frame = ActionButtonFrame(root, gui)

        # Layout
        self.filter_frame.frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        self.task_list_frame.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.task_details_frame.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.action_frame.frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # Initial load
        self.task_list_frame.refresh_tasks()


class FilterFrame:
    """Frame for task filtering controls."""

    def __init__(self, root: tk.Tk, gui: TodoGUI) -> None:
        """Initialize filter controls.

        Args:
            root: Tk root window.
            gui: Parent TodoGUI instance.
        """
        self.gui = gui
        self.frame = ttk.Frame(root)

        # Status filter buttons
        ttk.Label(self.frame, text="Status:").pack(side=tk.LEFT, padx=5)
        ttk.Button(self.frame, text="All", command=self._filter_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Pending", command=self._filter_pending).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(self.frame, text="In Progress", command=self._filter_in_progress).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(self.frame, text="Done", command=self._filter_done).pack(side=tk.LEFT, padx=2)

        ttk.Separator(self.frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Project filter
        ttk.Label(self.frame, text="Project:").pack(side=tk.LEFT, padx=5)
        self.project_var = tk.StringVar(value="")
        self.project_dropdown = ttk.Combobox(
            self.frame, textvariable=self.project_var, width=15, state="readonly"
        )
        self.project_dropdown.pack(side=tk.LEFT, padx=2)
        self.project_dropdown.bind("<<ComboboxSelected>>", lambda e: self._on_project_select())
        self._refresh_projects()

        # Overdue filter checkbox
        self.overdue_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.frame, text="Overdue Only", variable=self.overdue_var,
                       command=self._on_overdue_toggle).pack(side=tk.LEFT, padx=5)

        # Clear filters button
        ttk.Button(self.frame, text="Clear Filters", command=self._clear_filters).pack(
            side=tk.LEFT, padx=5
        )

    def _filter_all(self) -> None:
        """Show all tasks."""
        self.gui.current_status_filter = None
        self._refresh()

    def _filter_pending(self) -> None:
        """Filter to pending tasks."""
        self.gui.current_status_filter = TaskStatus.PENDING
        self._refresh()

    def _filter_in_progress(self) -> None:
        """Filter to in-progress tasks."""
        self.gui.current_status_filter = TaskStatus.IN_PROGRESS
        self._refresh()

    def _filter_done(self) -> None:
        """Filter to done tasks."""
        self.gui.current_status_filter = TaskStatus.DONE
        self._refresh()

    def _on_project_select(self) -> None:
        """Handle project selection."""
        selected = self.project_var.get()
        self.gui.current_project_filter = selected if selected else None
        self._refresh()

    def _on_overdue_toggle(self) -> None:
        """Handle overdue filter toggle."""
        self.gui.current_overdue_filter = self.overdue_var.get()
        self._refresh()

    def _clear_filters(self) -> None:
        """Clear all filters."""
        self.gui.current_status_filter = None
        self.gui.current_project_filter = None
        self.gui.current_overdue_filter = False
        self.project_var.set("")
        self.overdue_var.set(False)
        self._refresh()

    def _refresh_projects(self) -> None:
        """Refresh project dropdown options."""
        try:
            projects = self.gui.service.list_projects()
            self.project_dropdown["values"] = [""] + [p.name for p in projects]
        except Exception:
            pass

    def _refresh(self) -> None:
        """Refresh task list with current filters."""
        self.gui.main_window.task_list_frame.refresh_tasks(
            status=self.gui.current_status_filter,
            project_id=self.gui.current_project_filter,
            overdue_only=self.gui.current_overdue_filter,
        )


class TaskListFrame:
    """Frame displaying the list of tasks in a table."""

    def __init__(self, root: tk.Tk, gui: TodoGUI) -> None:
        """Initialize task list frame.

        Args:
            root: Tk root window.
            gui: Parent TodoGUI instance.
        """
        self.gui = gui
        self.frame = ttk.Frame(root)

        # Create treeview
        columns = ("Title", "Status", "Due Date", "Project", "Comments")
        self.tree = ttk.Treeview(self.frame, columns=columns, height=15)
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("Title", anchor=tk.W, width=200)
        self.tree.column("Status", anchor=tk.CENTER, width=80)
        self.tree.column("Due Date", anchor=tk.CENTER, width=100)
        self.tree.column("Project", anchor=tk.CENTER, width=100)
        self.tree.column("Comments", anchor=tk.CENTER, width=60)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("Title", text="Title", anchor=tk.W)
        self.tree.heading("Status", text="Status", anchor=tk.CENTER)
        self.tree.heading("Due Date", text="Due Date", anchor=tk.CENTER)
        self.tree.heading("Project", text="Project", anchor=tk.CENTER)
        self.tree.heading("Comments", text="Comments", anchor=tk.CENTER)

        # Configure overdue tag with red background
        self.tree.tag_configure("overdue", background="#ffcccc")

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        # Pack
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store task ID to item mapping
        self._task_items: dict[str, str] = {}

    def _on_select(self, event: Any) -> None:
        """Handle task selection."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            # Find task by item
            for task_id, item_id in self._task_items.items():
                if item_id == item:
                    try:
                        task = self.gui.service.get_task(task_id)
                        self.gui.select_task(task)
                    except TaskNotFoundError:
                        pass
                    break
        else:
            self.gui.select_task(None)

    def refresh_tasks(
        self,
        status: Optional[TaskStatus] = None,
        project_id: Optional[str] = None,
        overdue_only: bool = False,
    ) -> None:
        """Refresh task list with optional filters.

        Args:
            status: Optional status filter.
            project_id: Optional project filter.
            overdue_only: Whether to show only overdue tasks.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._task_items.clear()

        # Get tasks with filters
        try:
            tasks = self.gui.service.list_tasks(
                status=status, overdue_only=overdue_only
            )

            # Apply project filter if specified
            if project_id:
                tasks = [t for t in tasks if t.project_id == project_id]

            # Sort by status then by title
            tasks = sorted(tasks, key=lambda t: (t.status.value, t.title))

            # Populate tree
            for task in tasks:
                due_date_str = ""
                if task.due_date:
                    due_date_str = task.due_date.strftime("%Y-%m-%d")

                project_name = ""
                if task.project_id:
                    try:
                        project = self.gui.service.get_project(task.project_id)
                        project_name = project.name
                    except ProjectNotFoundError:
                        project_name = "Unknown"

                comment_count = len(task.comments)

                # Determine if overdue and add tag
                tags = ()
                if task.is_overdue():
                    tags = ("overdue",)

                item = self.tree.insert(
                    "",
                    "end",
                    values=(
                        task.title,
                        task.status.value.replace("_", " ").title(),
                        due_date_str,
                        project_name,
                        comment_count,
                    ),
                    tags=tags,
                )
                self._task_items[task.id] = item

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {str(e)}")


class TaskDetailsFrame:
    """Frame for displaying selected task details and comments."""

    def __init__(self, root: tk.Tk, gui: TodoGUI) -> None:
        """Initialize task details frame.

        Args:
            root: Tk root window.
            gui: Parent TodoGUI instance.
        """
        self.gui = gui
        self.frame = ttk.LabelFrame(root, text="Task Details")
        self.current_task: Optional[Task] = None

        # Task info section
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text="Title:").pack(side=tk.LEFT)
        self.title_label = ttk.Label(info_frame, text="", foreground="blue")
        self.title_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(info_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 0))
        self.status_label = ttk.Label(info_frame, text="", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Description section
        desc_frame = ttk.LabelFrame(self.frame, text="Description")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.description_text = tk.Text(desc_frame, height=5, wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True)
        self.description_text.config(state=tk.DISABLED)

        # Due date and project section
        meta_frame = ttk.Frame(self.frame)
        meta_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(meta_frame, text="Due Date:").pack(side=tk.LEFT)
        self.due_date_label = ttk.Label(meta_frame, text="None", foreground="darkred")
        self.due_date_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(meta_frame, text="Project:").pack(side=tk.LEFT, padx=(20, 0))
        self.project_label = ttk.Label(meta_frame, text="None", foreground="darkblue")
        self.project_label.pack(side=tk.LEFT, padx=5)

        # Comments section
        comments_frame = ttk.LabelFrame(self.frame, text="Comments")
        comments_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.comments_text = tk.Text(comments_frame, height=6, wrap=tk.WORD)
        self.comments_text.pack(fill=tk.BOTH, expand=True)
        self.comments_text.config(state=tk.DISABLED)

        # Comments buttons
        comments_button_frame = ttk.Frame(comments_frame)
        comments_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            comments_button_frame, text="Add Comment", command=self._on_add_comment
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            comments_button_frame, text="Clear Selection", command=self._on_clear_selection
        ).pack(side=tk.LEFT, padx=2)

    def display_task(self, task: Task) -> None:
        """Display task details.

        Args:
            task: Task to display.
        """
        self.current_task = task

        self.title_label.config(text=task.title)
        self.status_label.config(text=task.status.value.replace("_", " ").title())

        # Description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete("1.0", tk.END)
        if task.description:
            self.description_text.insert("1.0", task.description)
        self.description_text.config(state=tk.DISABLED)

        # Due date
        if task.due_date:
            self.due_date_label.config(text=task.due_date.strftime("%Y-%m-%d %H:%M"))
        else:
            self.due_date_label.config(text="None")

        # Project
        project_name = "None"
        if task.project_id:
            try:
                project = self.gui.service.get_project(task.project_id)
                project_name = project.name
            except ProjectNotFoundError:
                project_name = "Unknown"
        self.project_label.config(text=project_name)

        # Comments
        self._refresh_comments()

    def _refresh_comments(self) -> None:
        """Refresh comments display."""
        if not self.current_task:
            return

        self.comments_text.config(state=tk.NORMAL)
        self.comments_text.delete("1.0", tk.END)

        try:
            comments = self.gui.service.get_comments(self.current_task.id)
            if comments:
                for comment in comments:
                    author = comment.author or "Anonymous"
                    created = comment.created_at.strftime("%Y-%m-%d %H:%M")
                    text = f"[{author}] {created}\n{comment.content}\n\n"
                    self.comments_text.insert(tk.END, text)
            else:
                self.comments_text.insert("1.0", "No comments yet.")
        except Exception:
            pass

        self.comments_text.config(state=tk.DISABLED)

    def _on_add_comment(self) -> None:
        """Handle add comment button."""
        if not self.current_task:
            messagebox.showwarning("No Task", "Please select a task first.")
            return

        dialog = CommentDialog(self.gui.root, "Add Comment")
        if dialog.result:
            try:
                self.gui.service.add_comment(
                    self.current_task.id, dialog.result["content"], dialog.result.get("author")
                )
                self._refresh_comments()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add comment: {str(e)}")

    def _on_clear_selection(self) -> None:
        """Clear the task selection."""
        self.clear()
        self.gui.select_task(None)

    def clear(self) -> None:
        """Clear task details display."""
        self.current_task = None
        self.title_label.config(text="")
        self.status_label.config(text="")
        self.due_date_label.config(text="")
        self.project_label.config(text="")

        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete("1.0", tk.END)
        self.description_text.config(state=tk.DISABLED)

        self.comments_text.config(state=tk.NORMAL)
        self.comments_text.delete("1.0", tk.END)
        self.comments_text.config(state=tk.DISABLED)


class ActionButtonFrame:
    """Frame for action buttons (Add, Edit, Delete)."""

    def __init__(self, root: tk.Tk, gui: TodoGUI) -> None:
        """Initialize action buttons frame.

        Args:
            root: Tk root window.
            gui: Parent TodoGUI instance.
        """
        self.gui = gui
        self.frame = ttk.Frame(root)

        ttk.Button(self.frame, text="Add Task (Ctrl+N)", command=self.on_add_task).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.frame, text="Start Task", command=self._on_start_task).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.frame, text="Complete Task", command=self._on_complete_task).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.frame, text="Edit Task", command=self._on_edit_task).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.frame, text="Delete Task (Delete)", command=self.on_delete_task).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.frame, text="Refresh (Ctrl+R)", command=self._on_refresh).pack(
            side=tk.LEFT, padx=5
        )

    def on_add_task(self) -> None:
        """Handle add task button."""
        dialog = AddTaskDialog(self.gui.root, self.gui.service)
        if dialog.result:
            try:
                self.gui.service.add_task(
                    dialog.result["title"],
                    dialog.result.get("description"),
                    dialog.result.get("due_date"),
                )
                if dialog.result.get("project_id"):
                    # Get the just-added task and assign project
                    tasks = self.gui.service.list_tasks()
                    if tasks:
                        latest = max(tasks, key=lambda t: t.created_at)
                        self.gui.service.move_task_to_project(latest.id, dialog.result["project_id"])

                self.gui._refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add task: {str(e)}")

    def on_delete_task(self) -> None:
        """Handle delete task button."""
        if not self.gui.selected_task:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Delete this task?"):
            try:
                self.gui.service.delete_task(self.gui.selected_task.id)
                self.gui.select_task(None)
                self.gui._refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {str(e)}")

    def _on_start_task(self) -> None:
        """Mark selected task as in progress."""
        if not self.gui.selected_task:
            messagebox.showwarning("No Selection", "Please select a task.")
            return

        try:
            self.gui.service.start_task(self.gui.selected_task.id)
            self.gui.select_task(self.gui.service.get_task(self.gui.selected_task.id))
            self.gui._refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start task: {str(e)}")

    def _on_complete_task(self) -> None:
        """Mark selected task as done."""
        if not self.gui.selected_task:
            messagebox.showwarning("No Selection", "Please select a task.")
            return

        try:
            self.gui.service.complete_task(self.gui.selected_task.id)
            self.gui.select_task(self.gui.service.get_task(self.gui.selected_task.id))
            self.gui._refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete task: {str(e)}")

    def _on_edit_task(self) -> None:
        """Handle edit task button."""
        if not self.gui.selected_task:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return

        dialog = EditTaskDialog(self.gui.root, self.gui.service, self.gui.selected_task)
        if dialog.result:
            try:
                updates = dialog.result
                self.gui.service.update_task(
                    self.gui.selected_task.id,
                    updates.get("title"),
                    updates.get("description"),
                    updates.get("due_date"),
                )
                if "project_id" in updates:
                    self.gui.service.move_task_to_project(
                        self.gui.selected_task.id, updates["project_id"]
                    )
                self.gui.select_task(self.gui.service.get_task(self.gui.selected_task.id))
                self.gui._refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update task: {str(e)}")

    def _on_refresh(self) -> None:
        """Handle refresh button."""
        self.gui._refresh()


class AddTaskDialog(tk.Toplevel):
    """Modal dialog for adding a new task."""

    def __init__(self, parent: tk.Widget, service: TodoService) -> None:
        """Initialize add task dialog.

        Args:
            parent: Parent widget.
            service: TodoService instance.
        """
        super().__init__(parent)
        self.service = service
        self.result: Optional[dict[str, Any]] = None
        self.title("Add Task")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()

        # Title (required)
        ttk.Label(self, text="Title (required):").pack(padx=10, pady=5, anchor=tk.W)
        self.title_entry = ttk.Entry(self, width=40)
        self.title_entry.pack(padx=10, pady=5, fill=tk.X)
        self.title_entry.focus()

        # Description
        ttk.Label(self, text="Description:").pack(padx=10, pady=5, anchor=tk.W)
        self.description_text = tk.Text(self, height=4, width=40)
        self.description_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Due date
        ttk.Label(self, text="Due Date (YYYY-MM-DD HH:MM UTC):").pack(padx=10, pady=5, anchor=tk.W)
        self.due_date_entry = ttk.Entry(self, width=40)
        self.due_date_entry.pack(padx=10, pady=5, fill=tk.X)

        # Project
        ttk.Label(self, text="Project:").pack(padx=10, pady=5, anchor=tk.W)
        self.project_var = tk.StringVar(value="")
        projects = service.list_projects()
        project_names = [""] + [p.name for p in projects]
        self.project_dropdown = ttk.Combobox(
            self, textvariable=self.project_var, values=project_names, width=38, state="readonly"
        )
        self.project_dropdown.pack(padx=10, pady=5, fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_save(self) -> None:
        """Handle save button."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required.")
            return

        description = self.description_text.get("1.0", tk.END).strip() or None
        due_date_str = self.due_date_entry.get().strip()
        due_date = None

        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str).replace(tzinfo=timezone.utc)
            except ValueError:
                messagebox.showerror("Validation", "Invalid date format. Use YYYY-MM-DD HH:MM UTC")
                return

        project_id = None
        project_name = self.project_var.get()
        if project_name:
            projects = self.service.list_projects()
            for proj in projects:
                if proj.name == project_name:
                    project_id = proj.id
                    break

        self.result = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "project_id": project_id,
        }
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        self.destroy()


class EditTaskDialog(tk.Toplevel):
    """Modal dialog for editing a task."""

    def __init__(self, parent: tk.Widget, service: TodoService, task: Task) -> None:
        """Initialize edit task dialog.

        Args:
            parent: Parent widget.
            service: TodoService instance.
            task: Task to edit.
        """
        super().__init__(parent)
        self.service = service
        self.task = task
        self.result: Optional[dict[str, Any]] = None
        self.title("Edit Task")
        self.geometry("400x350")
        self.transient(parent)
        self.grab_set()

        # Title (required)
        ttk.Label(self, text="Title (required):").pack(padx=10, pady=5, anchor=tk.W)
        self.title_entry = ttk.Entry(self, width=40)
        self.title_entry.insert(0, task.title)
        self.title_entry.pack(padx=10, pady=5, fill=tk.X)
        self.title_entry.focus()

        # Description
        ttk.Label(self, text="Description:").pack(padx=10, pady=5, anchor=tk.W)
        self.description_text = tk.Text(self, height=4, width=40)
        if task.description:
            self.description_text.insert("1.0", task.description)
        self.description_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Due date
        ttk.Label(self, text="Due Date (YYYY-MM-DD HH:MM UTC):").pack(padx=10, pady=5, anchor=tk.W)
        self.due_date_entry = ttk.Entry(self, width=40)
        if task.due_date:
            self.due_date_entry.insert(0, task.due_date.strftime("%Y-%m-%d %H:%M"))
        self.due_date_entry.pack(padx=10, pady=5, fill=tk.X)

        # Project
        ttk.Label(self, text="Project:").pack(padx=10, pady=5, anchor=tk.W)
        self.project_var = tk.StringVar(value="")
        projects = service.list_projects()
        project_names = [""] + [p.name for p in projects]
        self.project_dropdown = ttk.Combobox(
            self, textvariable=self.project_var, values=project_names, width=38, state="readonly"
        )
        if task.project_id:
            for proj in projects:
                if proj.id == task.project_id:
                    self.project_var.set(proj.name)
                    break
        self.project_dropdown.pack(padx=10, pady=5, fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_save(self) -> None:
        """Handle save button."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required.")
            return

        description = self.description_text.get("1.0", tk.END).strip() or None
        due_date_str = self.due_date_entry.get().strip()
        due_date = None

        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str).replace(tzinfo=timezone.utc)
            except ValueError:
                messagebox.showerror("Validation", "Invalid date format. Use YYYY-MM-DD HH:MM UTC")
                return

        project_id = None
        project_name = self.project_var.get()
        if project_name:
            projects = self.service.list_projects()
            for proj in projects:
                if proj.name == project_name:
                    project_id = proj.id
                    break

        self.result = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "project_id": project_id,
        }
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        self.destroy()


class CommentDialog(tk.Toplevel):
    """Modal dialog for adding a comment."""

    def __init__(self, parent: tk.Widget, title: str) -> None:
        """Initialize comment dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
        """
        super().__init__(parent)
        self.result: Optional[dict[str, Any]] = None
        self.title(title)
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        # Author (optional)
        ttk.Label(self, text="Author (optional):").pack(padx=10, pady=5, anchor=tk.W)
        self.author_entry = ttk.Entry(self, width=40)
        self.author_entry.pack(padx=10, pady=5, fill=tk.X)

        # Comment text
        ttk.Label(self, text="Comment (required):").pack(padx=10, pady=5, anchor=tk.W)
        self.comment_text = tk.Text(self, height=8, width=40)
        self.comment_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.comment_text.focus()

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(button_frame, text="Add", command=self._on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_add(self) -> None:
        """Handle add button."""
        content = self.comment_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Validation", "Comment cannot be empty.")
            return

        author = self.author_entry.get().strip() or None

        self.result = {"content": content, "author": author}
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        self.destroy()
