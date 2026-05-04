import os
from typing import Optional

from ..models.project import Project
from ..models.task import Task
from ..models.task_status import TaskStatus
from ..services.project_manager import ProjectNotFoundError
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage
from ..utils.datetime_utils import parse_datetime_or_iso_string

_STATUS_LABEL = {
    TaskStatus.PENDING: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
}

_STATUS_NAME = {
    TaskStatus.PENDING: "pending",
    TaskStatus.IN_PROGRESS: "in progress",
    TaskStatus.DONE: "done",
}


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(label: str, default: Optional[str] = None) -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"  {label}{hint}: ").strip()
    return value if value else (default or "")


def _pick(prompt: str, options: list[str]) -> Optional[int]:
    """Print numbered options, return 0-based index or None on cancel."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("  0. Cancel")
    raw = input(f"  {prompt}: ").strip()
    if not raw.isdigit():
        return None
    n = int(raw)
    if n == 0 or n > len(options):
        return None
    return n - 1


def _task_line(task: Task) -> str:
    sym = _STATUS_LABEL[task.status]
    return f"{sym} {task.id[:8]}  {task.title}"


class InteractiveMenu:
    def __init__(self, storage_path: Optional[str] = None) -> None:
        storage = JsonStorage(storage_path) if storage_path else JsonStorage()
        self._service = TodoService(storage)

    def run(self) -> None:
        while True:
            _clear()
            self._print_header()
            tasks = self._service.list_tasks()
            self._print_task_list(tasks)
            self._print_main_menu()

            choice = input("  > ").strip().lower()

            if choice in ("0", "q", "quit", "exit"):
                _clear()
                break
            elif choice == "1":
                self._do_list()
            elif choice == "2":
                self._do_add()
            elif choice == "3":
                self._do_show(tasks)
            elif choice == "4":
                self._do_change_status(tasks)
            elif choice == "5":
                self._do_update(tasks)
            elif choice == "6":
                self._do_delete(tasks)
            elif choice == "7":
                self._do_check_status(tasks)
            elif choice == "8":
                self._do_manage_comments(tasks)
            elif choice == "9":
                self._do_manage_projects()
            elif choice == "10":
                self._do_summary_report()
            elif choice == "11":
                self._do_import_export()
            elif choice == "12":
                self._do_launch_gui()
            else:
                input("  Unknown option. Press Enter to continue...")

    # ── display helpers ────────────────────────────────────────────────────

    def _print_header(self) -> None:
        print("╔══════════════════════════════════╗")
        print("║          TODO  Manager           ║")
        print("╚══════════════════════════════════╝")
        print()

    def _print_task_list(self, tasks: list[Task]) -> None:
        if not tasks:
            print("  (no tasks yet)")
        else:
            for task in tasks:
                print(f"  {_task_line(task)}")
        print()

    def _print_main_menu(self) -> None:
        print("  1. List / filter tasks")
        print("  2. Add task")
        print("  3. Show task details")
        print("  4. Change status  (start / done / reopen)")
        print("  5. Update task    (title / description)")
        print("  6. Delete task")
        print("  7. Check task status")
        print("  8. Manage comments")
        print("  9. Manage projects")
        print("  10. View summary report")
        print("  11. Import / Export")
        print("  12. Launch GUI")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  Filter by status (leave blank for all):")
        print("  1. pending")
        print("  2. in progress")
        print("  3. done")
        print("  0. All")
        raw = input("  > ").strip()
        status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
        status = status_map.get(raw)

        # Date range filtering
        due_before = None
        due_after = None
        overdue_only = False

        _clear()
        print("  Filter by date range (leave blank for no filter):")
        print("  1. Show overdue tasks only")
        print("  2. Show tasks due before a date")
        print("  3. Show tasks due after a date")
        print("  4. Show tasks in a date range")
        print("  0. No date filter")
        date_choice = input("  > ").strip()

        if date_choice == "1":
            overdue_only = True
        elif date_choice == "2":
            due_before_str = _prompt("Due before date (ISO 8601)")
            if due_before_str:
                try:
                    due_before = parse_datetime_or_iso_string(due_before_str)
                except ValueError as e:
                    print(f"\n  Error: {e}")
                    input("  Press Enter to continue...")
                    return
        elif date_choice == "3":
            due_after_str = _prompt("Due after date (ISO 8601)")
            if due_after_str:
                try:
                    due_after = parse_datetime_or_iso_string(due_after_str)
                except ValueError as e:
                    print(f"\n  Error: {e}")
                    input("  Press Enter to continue...")
                    return
        elif date_choice == "4":
            due_after_str = _prompt("Due after date (ISO 8601)")
            due_before_str = _prompt("Due before date (ISO 8601)")
            if due_after_str:
                try:
                    due_after = parse_datetime_or_iso_string(due_after_str)
                except ValueError as e:
                    print(f"\n  Error: {e}")
                    input("  Press Enter to continue...")
                    return
            if due_before_str:
                try:
                    due_before = parse_datetime_or_iso_string(due_before_str)
                except ValueError as e:
                    print(f"\n  Error: {e}")
                    input("  Press Enter to continue...")
                    return
            # Validate range
            if due_after is not None and due_before is not None and due_after > due_before:
                print("\n  Error: due after date cannot be after due before date")
                input("  Press Enter to continue...")
                return

        _clear()
        tasks = self._service.list_tasks(
            status=status,
            due_before=due_before,
            due_after=due_after,
            overdue_only=overdue_only,
        )
        label_parts = []
        if status:
            label_parts.append(_STATUS_NAME[status])
        if overdue_only:
            label_parts.append("overdue")
        if due_before:
            label_parts.append(f"due before {due_before.strftime('%Y-%m-%d')}")
        if due_after:
            label_parts.append(f"due after {due_after.strftime('%Y-%m-%d')}")
        label = f"[{', '.join(label_parts)}]" if label_parts else "[all]"
        print(f"  Tasks {label}\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                due = f"  (due: {task.due_date.strftime('%Y-%m-%d')})" if task.due_date else ""
                print(f"  {_task_line(task)}{desc}{due}")
        print()
        input("  Press Enter to continue...")

    def _do_add(self) -> None:
        _clear()
        print("  Add new task\n")
        title = _prompt("Title")
        if not title:
            input("  Title cannot be empty. Press Enter...")
            return
        description = _prompt("Description (optional)") or None
        due_date_str = _prompt("Due date (optional, ISO 8601)") or None
        due_date = None
        if due_date_str:
            try:
                due_date = parse_datetime_or_iso_string(due_date_str)
            except ValueError as e:
                print(f"\n  Error: {e}")
                input("  Press Enter to continue...")
                return
        project_id = None
        print("  \n  Assign to project? (y/n, default: n)")
        if input("  > ").strip().lower() == "y":
            projects = self._service.list_projects()
            if not projects:
                print("  No projects available.")
            else:
                _clear()
                print("  Select project:\n")
                idx = _pick("  > ", [f"{p.id[:8]}  {p.name}" for p in projects])
                if idx is not None:
                    project_id = projects[idx].id
        try:
            task = self._service.add_task(title, description, due_date, project_id)
            print(f"\n  Added: {_task_line(task)}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_show(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Show details — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]
        _clear()
        print(f"  ID:          {task.id}")
        print(f"  Title:       {task.title}")
        print(f"  Description: {task.description or '—'}")
        print(f"  Status:      {task.status.value}")
        print(f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if task.due_date:
            print(f"  Due:         {task.due_date.strftime('%Y-%m-%d %H:%M CEST')}")
        else:
            print(f"  Due:         —")
        print()
        input("  Press Enter to continue...")

    def _do_change_status(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Change status — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}  (current: {task.status.value})\n")
        action_idx = _pick("New status", ["start  (in progress)", "done", "reopen  (pending)"])
        if action_idx is None:
            return

        try:
            actions = [self._service.start_task, self._service.complete_task, self._service.reopen_task]
            updated = actions[action_idx](task.id)
            print(f"\n  Updated: {_task_line(updated)}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_update(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Update task — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Editing: {task.title}\n")
        new_title = _prompt("New title", default=task.title)
        new_desc = _prompt("New description", default=task.description or "")
        new_desc = new_desc if new_desc else None
        due_date_str = _prompt("New due date (optional, ISO 8601)", default=task.due_date.isoformat() if task.due_date else "")
        new_due_date = None
        if due_date_str:
            try:
                new_due_date = parse_datetime_or_iso_string(due_date_str)
            except ValueError as e:
                print(f"\n  Error: {e}")
                input("  Press Enter to continue...")
                return

        try:
            updated = self._service.update_task(task.id, title=new_title or None, description=new_desc, due_date=new_due_date)
            print(f"\n  Updated: {_task_line(updated)}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Delete task — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Delete: {task.title}")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_task(task.id)
            print(f"  Deleted: {task.id[:8]}  {task.title}")
        except TaskNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_check_status(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Check task status — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Status: {task.title}\n")
        print(f"  Pending:      {task.is_pending()}")
        print(f"  In progress:  {task.is_in_progress()}")
        print(f"  Completed:    {task.is_completed()}")
        print(f"  Overdue:      {task.is_overdue()}")
        print()
        input("  Press Enter to continue...")

    def _do_manage_comments(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Manage comments — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        while True:
            _clear()
            print(f"  Managing comments for: {task.title}\n")
            comments = self._service.list_task_comments(task.id)
            if comments:
                for i, comment in enumerate(comments, 1):
                    preview = comment.content[:40] + ("..." if len(comment.content) > 40 else "")
                    print(f"  {i}. {preview}")
            else:
                print("  (no comments yet)")
            print()
            print("  1. Add comment")
            print("  2. View comment details")
            print("  3. Edit comment")
            print("  4. Delete comment")
            print("  0. Back")
            print()

            choice = input("  > ").strip().lower()

            if choice in ("0", "q"):
                break
            elif choice == "1":
                self._do_add_comment(task.id)
            elif choice == "2":
                self._do_show_comment_details(task.id)
            elif choice == "3":
                self._do_edit_comment(task.id)
            elif choice == "4":
                self._do_delete_comment(task.id)
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_add_comment(self, task_id: str) -> None:
        _clear()
        print("  Add comment\n")
        content = _prompt("Comment content")
        if not content:
            input("  Content cannot be empty. Press Enter...")
            return

        try:
            from ..services.task_manager import TaskNotFoundError
            comment = self._service.add_comment(task_id, content)
            print(f"\n  Added comment {comment.id[:8]}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_show_comment_details(self, task_id: str) -> None:
        _clear()
        comments = self._service.list_task_comments(task_id)
        if not comments:
            input("  No comments. Press Enter...")
            return

        print("  View comment — pick one:\n")
        idx = _pick("Select", [c.content[:50] for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  ID:       {comment.id[:8]}")
        print(f"  Content:  {comment.content}")
        print(f"  Author:   {comment.author or '—'}")
        print(f"  Created:  {comment.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Updated:  {comment.updated_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()
        input("  Press Enter to continue...")

    def _do_edit_comment(self, task_id: str) -> None:
        _clear()
        comments = self._service.list_task_comments(task_id)
        if not comments:
            input("  No comments. Press Enter...")
            return

        print("  Edit comment — pick one:\n")
        idx = _pick("Select", [c.content[:50] for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Editing comment\n")
        new_content = _prompt("New content", default=comment.content)
        if not new_content:
            input("  Content cannot be empty. Press Enter...")
            return

        try:
            updated = self._service.update_comment(comment.id, new_content)
            print(f"\n  Updated comment {updated.id[:8]}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_comment(self, task_id: str) -> None:
        _clear()
        comments = self._service.list_task_comments(task_id)
        if not comments:
            input("  No comments. Press Enter...")
            return

        print("  Delete comment — pick one:\n")
        idx = _pick("Select", [c.content[:50] for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Delete comment")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_comment(comment.id)
            print(f"  Deleted comment {comment.id[:8]}")
        except Exception as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_summary_report(self) -> None:
        _clear()
        report = self._service.generate_summary_report()
        print("  Task Summary Report\n")
        for line in str(report).split("\n"):
            print(f"  {line}")
        print()
        input("  Press Enter to continue...")

    def _do_manage_projects(self) -> None:
        """Project management submenu."""
        while True:
            _clear()
            print("  Manage Projects\n")
            projects = self._service.list_projects()
            if projects:
                for project in projects:
                    desc = f"  {project.description}" if project.description else ""
                    print(f"  {project.id[:8]}  {project.name}{desc}")
            else:
                print("  (no projects yet)")
            print()
            print("  1. Add project")
            print("  2. Show project details")
            print("  3. Update project")
            print("  4. Delete project")
            print("  0. Back")
            print()

            choice = input("  > ").strip().lower()

            if choice in ("0", "q"):
                break
            elif choice == "1":
                self._do_project_add()
            elif choice == "2":
                self._do_project_show(projects)
            elif choice == "3":
                self._do_project_update(projects)
            elif choice == "4":
                self._do_project_delete(projects)
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_project_add(self) -> None:
        _clear()
        print("  Add new project\n")
        name = _prompt("Name")
        if not name:
            input("  Name cannot be empty. Press Enter...")
            return
        description = _prompt("Description (optional)") or None
        try:
            project = self._service.add_project(name, description)
            print(f"\n  Added: {project.id[:8]}  {project.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_project_show(self, projects: list[Project]) -> None:
        _clear()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Select project:\n")
        idx = _pick("  > ", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  Project: {project.name}\n")
        print(f"  ID:          {project.id}")
        print(f"  Name:        {project.name}")
        print(f"  Description: {project.description or '—'}")
        print(f"  Created:     {project.created_at.isoformat()}")
        print(f"  Updated:     {project.updated_at.isoformat()}")
        tasks = self._service.list_tasks(project_id=project.id)
        print(f"\n  Tasks in project: {len(tasks)}")
        if tasks:
            for task in tasks[:10]:
                print(f"    {_task_line(task)}")
            if len(tasks) > 10:
                print(f"    ... and {len(tasks) - 10} more")
        print()
        input("  Press Enter to continue...")

    def _do_project_update(self, projects: list[Project]) -> None:
        _clear()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Select project:\n")
        idx = _pick("  > ", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  Update project: {project.name}\n")
        new_name = _prompt("New name (leave blank to keep current)", project.name) or project.name
        new_description = _prompt("New description (leave blank to keep current)", project.description or "") or project.description
        try:
            updated = self._service.update_project(project.id, new_name, new_description)
            print(f"\n  Updated: {updated.id[:8]}  {updated.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_project_delete(self, projects: list[Project]) -> None:
        _clear()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Select project to delete:\n")
        idx = _pick("  > ", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  Delete project: {project.name}\n")
        print("  Are you sure? (y/n)")
        if input("  > ").strip().lower() == "y":
            try:
                self._service.delete_project(project.id)
                print(f"\n  Deleted: {project.id[:8]}  {project.name}")
            except ProjectNotFoundError as e:
                print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_import_export(self) -> None:
        """Import/Export submenu."""
        while True:
            _clear()
            print("  Import / Export\n")
            print("  1. Export tasks and comments to file")
            print("  2. Import tasks and comments from file")
            print("  0. Back")
            print()

            choice = input("  > ").strip().lower()

            if choice in ("0", "q"):
                break
            elif choice == "1":
                self._do_export_menu()
            elif choice == "2":
                self._do_import_menu()
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_export_menu(self) -> None:
        """Prompt for export file path and execute."""
        _clear()
        print("  Export tasks and comments\n")
        file_path = _prompt("Output file path")
        if not file_path:
            input("  Path cannot be empty. Press Enter...")
            return

        try:
            count = self._service.export_to_json(file_path)
            print(f"\n  Exported {count} tasks to {file_path}")
        except (FileNotFoundError, ValueError, OSError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_import_menu(self) -> None:
        """Prompt for import file path and execute."""
        _clear()
        print("  Import tasks and comments\n")
        file_path = _prompt("Input file path")
        if not file_path:
            input("  Path cannot be empty. Press Enter...")
            return

        try:
            tasks_imp, tasks_skip, comments_imp, comments_skip = \
                self._service.import_from_json(file_path, "skip")
            _clear()
            print("  Import Summary\n")
            print(f"  Tasks imported:      {tasks_imp}")
            print(f"  Tasks skipped:       {tasks_skip}")
            print(f"  Comments imported:   {comments_imp}")
            print(f"  Comments skipped:    {comments_skip}")
        except (FileNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        print()
        input("  Press Enter to continue...")

    def _do_launch_gui(self) -> None:
        """Launch the tkinter GUI."""
        _clear()
        print("  Launching GUI...\n")
        try:
            from ..gui import gui_main
            gui_main.launch_gui()
        except Exception as e:
            _clear()
            print(f"  Error: Failed to launch GUI: {e}")
            input("  Press Enter to continue...")
