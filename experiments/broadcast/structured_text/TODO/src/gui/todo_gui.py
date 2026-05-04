"""Graphical user interface for the TODO manager using tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage
from ..services.base_repositories import TaskNotFoundError, ProjectNotFoundError


class TodoGUI:
    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.service = TodoService(JsonStorage(storage_path) if storage_path else None)
        self.root = tk.Tk()
        self.root.title("TODO Manager")
        self.root.geometry("900x600")

        self.selected_task: Optional[Task] = None
        self.current_status_filter: Optional[TaskStatus] = None
        self.current_project_filter: Optional[str] = None

        self._setup_ui()
        self._refresh_tasks()

    def _setup_ui(self) -> None:
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Filter panel
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding=5)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

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
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        ttk.Label(filter_frame, text="Project:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.project_var = tk.StringVar(value="All")
        self.project_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.project_var,
            state="readonly",
            width=15,
        )
        self.project_combo.grid(row=0, column=3, sticky=tk.W, padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        clear_btn = ttk.Button(filter_frame, text="Clear Filters", command=self._clear_filters)
        clear_btn.grid(row=0, column=4, padx=5)

        # Task list with tree view
        list_frame = ttk.LabelFrame(main_frame, text="Tasks", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tree view with scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.task_tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Title", "Status", "Due Date", "Project"),
            show="headings",
            yscrollcommand=tree_scroll.set,
            height=15,
        )
        tree_scroll.config(command=self.task_tree.yview)

        self.task_tree.column("ID", width=50)
        self.task_tree.column("Title", width=250)
        self.task_tree.column("Status", width=100)
        self.task_tree.column("Due Date", width=150)
        self.task_tree.column("Project", width=150)

        for col in self.task_tree["columns"]:
            self.task_tree.heading(col, text=col)

        self.task_tree.pack(fill=tk.BOTH, expand=True)
        self.task_tree.bind("<<TreeviewSelect>>", self._on_task_select)
        self.task_tree.bind("<Double-1>", lambda e: self._view_task())

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="Add Task", command=self._add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View", command=self._view_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Change Status", command=self._change_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self._delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Manage Projects", command=self._manage_projects).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var_label = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var_label, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))

    def _refresh_projects(self) -> None:
        projects = self.service._project_manager.list_all()
        project_names = ["All"] + [p.name for p in projects]
        self.project_combo["values"] = project_names

    def _apply_filters(self) -> None:
        status_map = {"Pending": TaskStatus.PENDING, "In Progress": TaskStatus.IN_PROGRESS, "Done": TaskStatus.DONE}
        self.current_status_filter = status_map.get(self.status_var.get())
        project_name = self.project_var.get()
        self.current_project_filter = None

        if project_name != "All":
            projects = self.service._project_manager.list_all()
            for p in projects:
                if p.name == project_name:
                    self.current_project_filter = p.id
                    break

        self._refresh_tasks()

    def _clear_filters(self) -> None:
        self.status_var.set("All")
        self.project_var.set("All")
        self.current_status_filter = None
        self.current_project_filter = None
        self._refresh_tasks()

    def _refresh_tasks(self) -> None:
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        tasks = self.service.list_tasks(status=self.current_status_filter, project_id=self.current_project_filter)

        for task in tasks:
            project_name = ""
            if task.project_id:
                try:
                    project = self.service._project_manager.get(task.project_id)
                    project_name = project.name
                except ProjectNotFoundError:
                    project_name = "Unknown"

            due_date_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date"
            short_id = task.id[:8]

            tags = ("overdue",) if task.is_overdue() else ()
            self.task_tree.insert("", tk.END, iid=task.id, values=(short_id, task.title, task.status.value, due_date_str, project_name), tags=tags)

        # Configure tag colors
        self.task_tree.tag_configure("overdue", background="lightcoral")

        self._update_status_bar()
        self._refresh_projects()

    def _on_task_select(self, event) -> None:
        selection = self.task_tree.selection()
        if selection:
            self.selected_task = self.service.get_task(selection[0])

    def _update_status_bar(self) -> None:
        tasks = self.service.list_tasks()
        overdue = sum(1 for t in tasks if t.is_overdue())
        status = f"Total: {len(tasks)} | Overdue: {overdue}"
        self.status_var_label.set(status)

    def _add_task(self) -> None:
        dialog = AddTaskDialog(self.root, self.service)
        if dialog.result:
            self._refresh_tasks()

    def _view_task(self) -> None:
        if not self.selected_task:
            messagebox.showwarning("No Selection", "Please select a task first")
            return

        dialog = ViewTaskDialog(self.root, self.selected_task, self.service)
        if dialog.updated:
            self._refresh_tasks()

    def _change_status(self) -> None:
        if not self.selected_task:
            messagebox.showwarning("No Selection", "Please select a task first")
            return

        dialog = ChangeStatusDialog(self.root, self.selected_task, self.service)
        if dialog.updated:
            self._refresh_tasks()

    def _delete_task(self) -> None:
        if not self.selected_task:
            messagebox.showwarning("No Selection", "Please select a task first")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete task '{self.selected_task.title}'?"):
            self.service.delete_task(self.selected_task.id)
            self.selected_task = None
            self._refresh_tasks()

    def _manage_projects(self) -> None:
        dialog = ManageProjectsDialog(self.root, self.service)
        if dialog.updated:
            self._refresh_tasks()

    def run(self) -> None:
        self.root.mainloop()


class AddTaskDialog:
    def __init__(self, parent: tk.Tk, service: TodoService) -> None:
        self.result = False
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Task")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.title_var, width=30).grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(frame, width=30, height=5)
        self.desc_text.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Due Date (YYYY-MM-DD HH:MM):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.due_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.due_var, width=30).grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Project:").grid(row=3, column=0, sticky=tk.W, pady=5)
        projects = service._project_manager.list_all()
        project_names = ["None"] + [p.name for p in projects]
        self.project_var = tk.StringVar(value="None")
        ttk.Combobox(frame, textvariable=self.project_var, values=project_names, width=28, state="readonly").grid(row=3, column=1, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        try:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Title cannot be empty")
                return

            desc = self.desc_text.get("1.0", tk.END).strip() or None
            due_date = None

            if self.due_var.get().strip():
                due_date = datetime.strptime(self.due_var.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

            project_id = None
            if self.project_var.get() != "None":
                projects = self.service._project_manager.list_all()
                for p in projects:
                    if p.name == self.project_var.get():
                        project_id = p.id
                        break

            self.service.add_task(title, description=desc, due_date=due_date, project_id=project_id)
            self.result = True
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")


class ViewTaskDialog:
    def __init__(self, parent: tk.Tk, task: Task, service: TodoService) -> None:
        self.updated = False
        self.task = task
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Task: {task.title}")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar(value=task.title)
        ttk.Entry(frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=task.status.value).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Description:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(frame, width=40, height=5)
        self.desc_text.insert("1.0", task.description or "")
        self.desc_text.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Due Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
        due_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date"
        self.due_var = tk.StringVar(value=due_str)
        ttk.Entry(frame, textvariable=self.due_var, width=40).grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Project:").grid(row=4, column=0, sticky=tk.W, pady=5)
        project_name = "None"
        if task.project_id:
            try:
                project = service._project_manager.get(task.project_id)
                project_name = project.name
            except ProjectNotFoundError:
                project_name = "Unknown"
        ttk.Label(frame, text=project_name).grid(row=4, column=1, sticky=tk.W, pady=5)

        # Comments section
        ttk.Label(frame, text="Comments:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        comments = service.list_comments(task.id)
        comments_text = "\n".join([f"- {c.content}" for c in comments]) if comments else "No comments"
        ttk.Label(frame, text=f"{len(comments)} comments", relief=tk.SUNKEN).grid(row=5, column=1, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Update", command=self._update).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _update(self) -> None:
        try:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Title cannot be empty")
                return

            desc = self.desc_text.get("1.0", tk.END).strip() or None
            due_date = None

            if self.due_var.get().strip() and self.due_var.get().strip() != "No due date":
                due_date = datetime.strptime(self.due_var.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

            self.service.update_task(self.task.id, title=title, description=desc, due_date=due_date)
            self.updated = True
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")


class ChangeStatusDialog:
    def __init__(self, parent: tk.Tk, task: Task, service: TodoService) -> None:
        self.updated = False
        self.task = task
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Status")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Change status for: {task.title}").pack(pady=10)
        ttk.Label(frame, text="New Status:").pack()

        self.status_var = tk.StringVar(value=task.status.value)
        for status in TaskStatus:
            ttk.Radiobutton(frame, text=status.value, variable=self.status_var, value=status.value).pack(anchor=tk.W, padx=20)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        status_value = self.status_var.get()
        status_map = {s.value: s for s in TaskStatus}
        new_status = status_map.get(status_value)

        if new_status == TaskStatus.PENDING:
            self.service.reopen_task(self.task.id)
        elif new_status == TaskStatus.IN_PROGRESS:
            self.service.start_task(self.task.id)
        elif new_status == TaskStatus.DONE:
            self.service.complete_task(self.task.id)

        self.updated = True
        self.dialog.destroy()


class ManageProjectsDialog:
    def __init__(self, parent: tk.Tk, service: TodoService) -> None:
        self.updated = False
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Projects")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Project list
        list_frame = ttk.LabelFrame(frame, text="Projects", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.project_list = tk.Listbox(list_frame, yscrollcommand=scroll.set)
        scroll.config(command=self.project_list.yview)
        self.project_list.pack(fill=tk.BOTH, expand=True)

        self._refresh_list()

        # Add project
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(add_frame, text="New Project:").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.name_var, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_frame, text="Add", command=self._add_project).pack(side=tk.LEFT, padx=5)

        # Delete button
        ttk.Button(frame, text="Delete Selected", command=self._delete_project).pack(pady=10)

    def _refresh_list(self) -> None:
        self.project_list.delete(0, tk.END)
        projects = self.service._project_manager.list_all()
        for p in projects:
            self.project_list.insert(tk.END, p.name)

    def _add_project(self) -> None:
        name = self.name_var.get().strip()
        if name:
            try:
                self.service._project_manager.add(name)
                self.name_var.set("")
                self._refresh_list()
                self.updated = True
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def _delete_project(self) -> None:
        selection = self.project_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a project")
            return

        project_name = self.project_list.get(selection[0])
        projects = self.service._project_manager.list_all()
        project_id = None
        for p in projects:
            if p.name == project_name:
                project_id = p.id
                break

        if project_id:
            try:
                self.service._project_manager.delete(project_id)
                self._refresh_list()
                self.updated = True
            except ProjectNotFoundError:
                messagebox.showerror("Error", "Project not found")
