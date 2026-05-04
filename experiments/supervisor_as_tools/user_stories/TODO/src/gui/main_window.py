import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from .comments_dialog import CommentsDialog
from .dialogs import AddTaskDialog, ConfirmDialog, ViewTaskDialog


class MainWindow:
    """Main window for TODO GUI application."""

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize MainWindow.

        Args:
            root: Tk root widget
        """
        self.root = root
        self.root.title("TODO Manager")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)

        self._service = TodoService()
        self._build_widgets()
        self._populate_project_filter()
        self._populate_treeview()

    def _build_widgets(self) -> None:
        """Build main window widgets."""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(title_frame, text="TODO Manager", font=("TkDefaultFont", 16, "bold")).pack(
            side=tk.LEFT
        )

        # Filter frame
        filter_frame = ttk.LabelFrame(self.root, text="Filter", padding="10")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=["All", "Pending", "In Progress", "Done"],
            state="readonly",
            width=15,
        )
        status_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.on_filter_changed())

        ttk.Label(filter_frame, text="Project:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.project_var = tk.StringVar(value="All")
        self.project_combo = ttk.Combobox(
            filter_frame, textvariable=self.project_var, state="readonly", width=15
        )
        self.project_combo.grid(row=0, column=3, sticky=tk.W, padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", lambda e: self.on_filter_changed())

        ttk.Button(filter_frame, text="Refresh", command=self.on_refresh_clicked).grid(
            row=0, column=4, padx=5
        )

        # Treeview with scrollbars
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.treeview = ttk.Treeview(
            tree_frame,
            columns=("status", "id", "title", "due_date", "project"),
            height=15,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.config(command=self.treeview.yview)
        hsb.config(command=self.treeview.xview)

        self.treeview.column("#0", width=0, stretch=False)
        self.treeview.column("status", width=50, anchor=tk.CENTER)
        self.treeview.column("id", width=80, anchor=tk.W)
        self.treeview.column("title", width=300, anchor=tk.W)
        self.treeview.column("due_date", width=100, anchor=tk.CENTER)
        self.treeview.column("project", width=150, anchor=tk.W)

        self.treeview.heading("#0", text="", anchor=tk.W)
        self.treeview.heading("status", text="Status", anchor=tk.CENTER)
        self.treeview.heading("id", text="ID", anchor=tk.W)
        self.treeview.heading("title", text="Title", anchor=tk.W)
        self.treeview.heading("due_date", text="Due Date", anchor=tk.CENTER)
        self.treeview.heading("project", text="Project", anchor=tk.W)

        # Configure tag for overdue tasks
        self.treeview.tag_configure("overdue", background="#ffcccc")

        self.treeview.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Action buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="New Task", command=self.on_new_task_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="View", command=self.on_view_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Start", command=self.on_start_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Complete", command=self.on_complete_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Reopen", command=self.on_reopen_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Delete", command=self.on_delete_clicked).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Comments", command=self.on_comments_clicked).pack(
            side=tk.LEFT, padx=2
        )

        # Status bar
        self.status_var_label = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var_label, relief=tk.SUNKEN
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _populate_project_filter(self) -> None:
        """Populate project filter combobox."""
        try:
            projects = self._service.list_projects()
            project_options = ["All"] + [f"{p.id[:8]}  {p.name}" for p in projects]
            self.project_combo["values"] = project_options
            self.project_combo.current(0)
            self.projects_map = {f"{p.id[:8]}  {p.name}": p.id for p in projects}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load projects: {e}")

    def _populate_treeview(self) -> None:
        """Fetch tasks from service and populate Treeview."""
        try:
            # Get filter values
            status_filter = self.status_var.get()
            project_filter = self.project_var.get()

            # Convert status filter
            status = None
            if status_filter == "Pending":
                status = TaskStatus.PENDING
            elif status_filter == "In Progress":
                status = TaskStatus.IN_PROGRESS
            elif status_filter == "Done":
                status = TaskStatus.DONE

            # Convert project filter
            project_id = None
            if project_filter != "All" and project_filter in self.projects_map:
                project_id = self.projects_map[project_filter]

            # Fetch tasks
            tasks = self._service.list_tasks(status=status, project_id=project_id)

            # Clear treeview
            for item in self.treeview.get_children():
                self.treeview.delete(item)

            # Status label mapping
            status_labels = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.IN_PROGRESS: "[~]",
                TaskStatus.DONE: "[x]",
            }

            # Populate treeview
            for task in tasks:
                status_label = status_labels.get(task.status, "?")
                due_date_str = (
                    task.due_date.strftime("%Y-%m-%d") if task.due_date else "—"
                )
                project_name = "—"
                if task.project_id:
                    try:
                        project = self._service.get_project(task.project_id)
                        project_name = project.name
                    except Exception:
                        project_name = task.project_id[:8]

                tags = []
                if task.is_overdue():
                    tags.append("overdue")

                self.treeview.insert(
                    "",
                    "end",
                    iid=task.id,
                    values=(
                        status_label,
                        task.id[:8],
                        task.title,
                        due_date_str,
                        project_name,
                    ),
                    tags=tags,
                )

            # Update status bar
            overdue_count = sum(1 for task in tasks if task.is_overdue())
            self.status_var_label.set(f"Tasks: {len(tasks)} | Overdue: {overdue_count}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")

    def on_filter_changed(self) -> None:
        """Event handler when filter changes."""
        self._populate_treeview()

    def on_refresh_clicked(self) -> None:
        """Event handler for Refresh button."""
        self._populate_project_filter()
        self._populate_treeview()

    def on_new_task_clicked(self) -> None:
        """Event handler for New Task button."""
        try:
            projects = self._service.list_projects()
            projects_list = [{"id": p.id, "name": p.name} for p in projects]

            def add_task_callback(title: str, description: Optional[str], due_date: Optional[datetime], project_id: Optional[str]) -> None:
                try:
                    self._service.add_task(title, description, due_date, project_id)
                    self._refresh_display()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add task: {e}")

            AddTaskDialog(self.root, add_task_callback, projects_list)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open add task dialog: {e}")

    def on_view_clicked(self) -> None:
        """Event handler for View button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            task = self._service.get_task(task_id)
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                "updated_at": task.updated_at.strftime("%Y-%m-%d %H:%M UTC"),
                "due_date": (
                    task.due_date.strftime("%Y-%m-%d") if task.due_date else None
                ),
                "project_id": task.project_id,
            }
            ViewTaskDialog(self.root, task_dict)
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view task: {e}")

    def on_start_clicked(self) -> None:
        """Event handler for Start button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            self._service.start_task(task_id)
            self._refresh_display()
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start task: {e}")

    def on_complete_clicked(self) -> None:
        """Event handler for Complete button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            self._service.complete_task(task_id)
            self._refresh_display()
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete task: {e}")

    def on_reopen_clicked(self) -> None:
        """Event handler for Reopen button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            self._service.reopen_task(task_id)
            self._refresh_display()
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reopen task: {e}")

    def on_delete_clicked(self) -> None:
        """Event handler for Delete button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            task = self._service.get_task(task_id)

            def confirm_callback(confirmed: bool) -> None:
                if confirmed:
                    try:
                        self._service.delete_task(task_id)
                        self._refresh_display()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete task: {e}")

            ConfirmDialog(
                self.root,
                "Delete Task",
                f"Are you sure you want to delete:\n{task.title}?",
                confirm_callback,
            )
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {e}")

    def on_comments_clicked(self) -> None:
        """Event handler for Comments button."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return

        try:
            task = self._service.get_task(task_id)
            CommentsDialog(self.root, task_id, task.title, self._service)
        except TaskNotFoundError:
            messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open comments dialog: {e}")

    def _get_selected_task_id(self) -> Optional[str]:
        """Return task ID of selected row or None."""
        selection = self.treeview.selection()
        if selection:
            return selection[0]
        return None

    def _refresh_display(self) -> None:
        """Internal refresh after mutation."""
        self._populate_project_filter()
        self._populate_treeview()
