"""Tkinter GUI for TODO application."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ..models.task_status import TaskStatus
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage

CEST = ZoneInfo("Europe/Paris")


class TodoGUI:
    """Tkinter GUI for the TODO application."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the GUI with a TodoService."""
        storage = JsonStorage(storage_path) if storage_path else JsonStorage()
        self._service = TodoService(storage)

        self.root = tk.Tk()
        self.root.title("TODO Manager")
        self.root.geometry("900x600")
        self._setup_ui()
        self._refresh_task_list()

    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Task List", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, padx=5)
        self.status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=["all", "pending", "in_progress", "done"],
            state="readonly",
            width=15,
        )
        status_combo.grid(row=0, column=1, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_task_list())

        ttk.Label(filter_frame, text="Project:").grid(row=0, column=2, padx=5)
        self.project_var = tk.StringVar(value="all")
        self._project_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.project_var,
            state="readonly",
            width=15,
        )
        self._project_combo.grid(row=0, column=3, padx=5)
        self._project_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_task_list())
        self._update_project_list()

        # Checkbox for overdue
        self.overdue_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_frame, text="Overdue only", variable=self.overdue_var, command=self._refresh_task_list
        ).grid(row=0, column=4, padx=5)

        # Task list section
        list_frame = ttk.LabelFrame(main_frame, text="Tasks", padding="5")
        list_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 10))
        main_frame.rowconfigure(2, weight=1)

        # Create treeview for tasks
        columns = ("Status", "Title", "Description", "Due Date", "Project", "Comments")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, height=15)
        self.task_tree.column("#0", width=80, heading="ID")
        self.task_tree.column("Status", width=80, heading="Status")
        self.task_tree.column("Title", width=150, heading="Title")
        self.task_tree.column("Description", width=150, heading="Description")
        self.task_tree.column("Due Date", width=150, heading="Due Date")
        self.task_tree.column("Project", width=100, heading="Project")
        self.task_tree.column("Comments", width=70, heading="Comments")

        self.task_tree.heading("#0", text="ID", anchor="w")
        self.task_tree.heading("Status", text="Status", anchor="w")
        self.task_tree.heading("Title", text="Title", anchor="w")
        self.task_tree.heading("Description", text="Description", anchor="w")
        self.task_tree.heading("Due Date", text="Due Date", anchor="w")
        self.task_tree.heading("Project", text="Project", anchor="w")
        self.task_tree.heading("Comments", text="Comments", anchor="w")

        # Add scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.task_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.task_tree.xview)
        self.task_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.task_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        # Bind double-click to edit
        self.task_tree.bind("<Double-1>", self._on_task_double_click)

        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

        ttk.Button(button_frame, text="Add Task", command=self._add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Task", command=self._start_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Complete Task", command=self._complete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reopen Task", command=self._reopen_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Task", command=self._delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Comment", command=self._add_comment_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Comments", command=self._view_comments).pack(side=tk.LEFT, padx=5)

        # Configure tag colors for overdue tasks
        self.task_tree.tag_configure("overdue", background="#ffcccc", foreground="#cc0000")

    def _update_project_list(self) -> None:
        """Update the project filter dropdown."""
        projects = self._service.list_projects()
        project_names = ["all"] + [p.name for p in projects]
        self._project_combo["values"] = project_names

    def _refresh_task_list(self) -> None:
        """Refresh the task list based on current filters."""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Get filter values
        status_str = self.status_var.get()
        status = TaskStatus(status_str) if status_str != "all" else None
        overdue = self.overdue_var.get() or None

        project_name = self.project_var.get()
        project_id = None
        if project_name and project_name != "all":
            projects = self._service.list_projects()
            for p in projects:
                if p.name == project_name:
                    project_id = p.id
                    break

        # Get filtered tasks
        tasks = self._service.list_tasks(status=status, overdue=overdue)

        # Filter by project if selected
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        # Display tasks
        for task in tasks:
            task_id_short = task.id[:8]
            status_val = task.status.value
            description = task.description or ""
            due_str = task.due_date.isoformat() if task.due_date else ""
            project_name = ""
            if task.project_id:
                try:
                    proj = self._service.get_project(task.project_id)
                    project_name = proj.name
                except Exception:
                    project_name = "Unknown"

            # Count comments
            comments = self._service.list_comments(task.id)
            comment_count = len(comments)

            # Apply overdue tag if needed
            tag = "overdue" if task.is_overdue() else ""

            self.task_tree.insert(
                "",
                "end",
                text=task_id_short,
                values=(status_val, task.title, description, due_str, project_name, str(comment_count)),
                tags=(tag,) if tag else (),
                iid=task.id,
            )

    def _get_selected_task_id(self) -> Optional[str]:
        """Get the ID of the selected task."""
        selection = self.task_tree.selection()
        return selection[0] if selection else None

    def _add_task(self) -> None:
        """Open dialog to add a new task."""
        dialog = AddTaskDialog(self.root, self._service)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            self._refresh_task_list()

    def _on_task_double_click(self, event) -> None:
        """Handle double-click on a task to show details."""
        task_id = self._get_selected_task_id()
        if task_id:
            self._show_task_details(task_id)

    def _show_task_details(self, task_id: str) -> None:
        """Show task details in a dialog."""
        try:
            task = self._service.get_task(task_id)
            dialog = TaskDetailsDialog(self.root, task, self._service)
            self.root.wait_window(dialog.dialog)
            self._refresh_task_list()
            self._update_project_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _start_task(self) -> None:
        """Mark selected task as in progress."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            self._service.start_task(task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _complete_task(self) -> None:
        """Mark selected task as done."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            self._service.complete_task(task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reopen_task(self) -> None:
        """Reopen selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            self._service.reopen_task(task_id)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_task(self) -> None:
        """Delete selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            task = self._service.get_task(task_id)
            if messagebox.askyesno("Confirm Delete", f"Delete task '{task.title}'?"):
                self._service.delete_task(task_id)
                self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_comment_dialog(self) -> None:
        """Open dialog to add a comment to a task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            task = self._service.get_task(task_id)
            dialog = AddCommentDialog(self.root, task_id, self._service)
            self.root.wait_window(dialog.dialog)
            self._refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _view_comments(self) -> None:
        """View comments for selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("No Selection", "Please select a task.")
            return
        try:
            comments = self._service.list_comments(task_id)
            if not comments:
                messagebox.showinfo("Comments", "No comments for this task.")
                return
            dialog = ViewCommentsDialog(self.root, task_id, self._service)
            self.root.wait_window(dialog.dialog)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()


class AddTaskDialog:
    """Dialog for adding a new task."""

    def __init__(self, parent: tk.Widget, service: TodoService) -> None:
        """Initialize the dialog."""
        self.service = service
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Task")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Title:").grid(row=0, column=0, sticky="w", pady=5)
        self.title_entry = ttk.Entry(frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=40, height=6)
        self.description_text.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Due Date (optional):").grid(row=2, column=0, sticky="w", pady=5)
        self.due_date_entry = ttk.Entry(frame, width=40)
        self.due_date_entry.grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(frame, text="ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+HH:MM", font=("Arial", 8)).grid(
            row=3, column=1, sticky="w", pady=(0, 10)
        )

        ttk.Label(frame, text="Project:").grid(row=4, column=0, sticky="w", pady=5)
        self.project_var = tk.StringVar(value="none")
        projects = service.list_projects()
        project_names = ["none"] + [p.name for p in projects]
        self.project_combo = ttk.Combobox(frame, textvariable=self.project_var, values=project_names, state="readonly")
        self.project_combo.grid(row=4, column=1, sticky="ew", pady=5)

        frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Add", command=self._add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

        self.title_entry.focus()

    def _add(self) -> None:
        """Add the task."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title cannot be empty.")
            return

        description = self.description_text.get("1.0", tk.END).strip() or None

        due_date = None
        due_date_str = self.due_date_entry.get().strip()
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=CEST)
            except ValueError:
                messagebox.showerror("Error", "Invalid date format.")
                return

        project_name = self.project_var.get()
        project_id = None
        if project_name != "none":
            projects = self.service.list_projects()
            for p in projects:
                if p.name == project_name:
                    project_id = p.id
                    break

        try:
            task = self.service.add_task(title, description)
            if due_date:
                # Update task with due date
                task.due_date = due_date
                self.service._manager._persist()
            if project_id:
                self.service.assign_task_to_project(task.id, project_id)
            self.result = task
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class TaskDetailsDialog:
    """Dialog for viewing and editing task details."""

    def __init__(self, parent: tk.Widget, task, service: TodoService) -> None:
        """Initialize the dialog."""
        self.task = task
        self.service = service
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Task: {task.title}")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Display task info
        ttk.Label(frame, text=f"ID: {task.id}").pack(anchor="w", pady=5)
        ttk.Label(frame, text=f"Status: {task.status.value}").pack(anchor="w", pady=5)
        ttk.Label(frame, text=f"Title: {task.title}", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        if task.description:
            ttk.Label(frame, text=f"Description: {task.description}").pack(anchor="w", pady=5)

        if task.due_date:
            due_str = task.due_date.isoformat()
            overdue_str = " (OVERDUE)" if task.is_overdue() else ""
            ttk.Label(frame, text=f"Due: {due_str}{overdue_str}").pack(anchor="w", pady=5)

        if task.project_id:
            try:
                proj = service.get_project(task.project_id)
                ttk.Label(frame, text=f"Project: {proj.name}").pack(anchor="w", pady=5)
            except Exception:
                pass

        ttk.Label(frame, text=f"Created: {task.created_at.isoformat()}").pack(anchor="w", pady=5)
        ttk.Label(frame, text=f"Updated: {task.updated_at.isoformat()}").pack(anchor="w", pady=5)

        # Edit buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Edit Title", command=self._edit_title).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Description", command=self._edit_description).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _edit_title(self) -> None:
        """Edit task title."""
        new_title = simpledialog.askstring("Edit Title", "New title:", initialvalue=self.task.title)
        if new_title:
            try:
                self.service.update_task(self.task.id, title=new_title)
                self.task.title = new_title
                self.dialog.title(f"Task: {self.task.title}")
                messagebox.showinfo("Success", "Title updated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _edit_description(self) -> None:
        """Edit task description."""
        new_desc = simpledialog.askstring(
            "Edit Description", "New description:", initialvalue=self.task.description or ""
        )
        if new_desc is not None:
            try:
                self.service.update_task(self.task.id, description=new_desc or None)
                self.task.description = new_desc or None
                messagebox.showinfo("Success", "Description updated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))


class AddCommentDialog:
    """Dialog for adding a comment."""

    def __init__(self, parent: tk.Widget, task_id: str, service: TodoService) -> None:
        """Initialize the dialog."""
        self.task_id = task_id
        self.service = service
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Comment")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Comment:").pack(anchor="w", pady=5)
        self.content_text = tk.Text(frame, width=50, height=10)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(frame, text="Author (optional):").pack(anchor="w", pady=5)
        self.author_entry = ttk.Entry(frame, width=50)
        self.author_entry.pack(fill=tk.X, pady=5)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Add", command=self._add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _add(self) -> None:
        """Add the comment."""
        content = self.content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Comment cannot be empty.")
            return

        author = self.author_entry.get().strip() or None

        try:
            self.service.add_comment(self.task_id, content, author)
            messagebox.showinfo("Success", "Comment added.")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class ViewCommentsDialog:
    """Dialog for viewing comments on a task."""

    def __init__(self, parent: tk.Widget, task_id: str, service: TodoService) -> None:
        """Initialize the dialog."""
        self.task_id = task_id
        self.service = service
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Comments")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Get comments
        comments = service.list_comments(task_id)

        if not comments:
            ttk.Label(frame, text="No comments.").pack(anchor="w", pady=5)
        else:
            text = tk.Text(frame, width=60, height=20)
            text.pack(fill=tk.BOTH, expand=True)

            for comment in comments:
                author_str = f" by {comment.author}" if comment.author else ""
                text.insert(tk.END, f"{comment.id[:8]}{author_str}:\n")
                text.insert(tk.END, f"  {comment.content}\n")
                if comment.updated_at:
                    text.insert(tk.END, f"  (edited: {comment.updated_at.isoformat()})\n")
                text.insert(tk.END, "\n")

            text.config(state=tk.DISABLED)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
