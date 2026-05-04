import os
from typing import Optional

from ..layers.models.task import Task
from ..layers.models.project import Project
from ..layers.models.task_status import TaskStatus
from ..layers.repositories import TaskNotFoundError
from ..layers.repositories import ProjectNotFoundError
from ..layers.repositories import CommentNotFoundError
from ..layers.services.todo_service import TodoService
from ..layers.services.statistics_service import StatisticsService
from ..layers.services.import_export_service import ImportExportService, ImportExportValidationError
from ..layers.storage.json_storage import JsonStorage

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
        self._stats_service = StatisticsService(storage)
        self._import_export_service = ImportExportService(storage)

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
                self._do_manage_comments(tasks)
            elif choice == "8":
                self._do_view_statistics()
            elif choice == "9":
                self._do_manage_projects()
            elif choice in ("b", "B"):
                self._do_export()
            elif choice in ("c", "C"):
                self._do_import()
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
        print("  7. Manage comments")
        print("  8. View statistics")
        print("  9. Manage projects")
        print("  B. Export tasks and comments")
        print("  C. Import tasks and comments")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  Filter options:")
        print("  1. By status")
        print("  2. Overdue tasks")
        print("  3. All tasks")
        print("  0. Cancel")
        print()
        choice = input("  > ").strip()

        status = None
        overdue = False
        label = "[all]"

        if choice == "1":
            _clear()
            print("  Filter by status:")
            print("  1. pending")
            print("  2. in progress")
            print("  3. done")
            print("  0. All")
            raw = input("  > ").strip()
            status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
            status = status_map.get(raw)
            if status:
                label = f"[{_STATUS_NAME[status]}]"
        elif choice == "2":
            overdue = True
            label = "[overdue]"
        elif choice == "0":
            return

        _clear()
        tasks = self._service.list_tasks(status=status, overdue=overdue)
        print(f"  Tasks {label}\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                overdue_str = " (OVERDUE)" if task.is_overdue() else ""
                print(f"  {_task_line(task)}{desc}{overdue_str}")
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
        try:
            task = self._service.add_task(title, description)
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

        try:
            updated = self._service.update_task(task.id, title=new_title or None, description=new_desc)
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
            print(f"  Task: {task.title}\n")
            comments = self._service.list_comments(task.id)
            if comments:
                print("  Comments:")
                for comment in comments:
                    author_str = f" by {comment.author}" if comment.author else ""
                    print(f"    {comment.id[:8]}{author_str}")
                    print(f"      {comment.content}")
            else:
                print("  (no comments)")
            print()
            print("  1. Add comment")
            print("  2. Edit comment")
            print("  3. Delete comment")
            print("  0. Back")
            print()
            choice = input("  > ").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._do_add_comment(task)
            elif choice == "2":
                if comments:
                    self._do_edit_comment(comments)
            elif choice == "3":
                if comments:
                    self._do_delete_comment(comments)

    def _do_add_comment(self, task: Task) -> None:
        _clear()
        print(f"  Add comment to: {task.title}\n")
        content = _prompt("Comment")
        if not content:
            input("  Comment cannot be empty. Press Enter...")
            return
        author = _prompt("Author (optional)") or None

        try:
            comment = self._service.add_comment(task.id, content, author)
            print(f"\n  Added comment {comment.id[:8]}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_edit_comment(self, comments) -> None:
        _clear()
        print("  Edit comment — pick one:\n")
        options = []
        for comment in comments:
            author_str = f" by {comment.author}" if comment.author else ""
            options.append(f"{comment.id[:8]}{author_str}")
        idx = _pick("Select", options)
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Current: {comment.content}\n")
        new_content = _prompt("New content", default=comment.content)
        if not new_content:
            input("  Content cannot be empty. Press Enter...")
            return

        try:
            updated = self._service.update_comment(comment.id, new_content)
            print(f"\n  Updated comment {updated.id[:8]}")
        except (CommentNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_comment(self, comments) -> None:
        _clear()
        print("  Delete comment — pick one:\n")
        options = []
        for comment in comments:
            author_str = f" by {comment.author}" if comment.author else ""
            options.append(f"{comment.id[:8]}{author_str}")
        idx = _pick("Select", options)
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Delete comment: {comment.content[:50]}...")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_comment(comment.id)
            print(f"  Deleted comment {comment.id[:8]}")
        except CommentNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_view_statistics(self) -> None:
        _clear()
        stats = self._stats_service.compute_statistics()
        print("\n  Task Statistics\n")
        print(f"  Total tasks:              {stats.total_task_count}")
        print(f"  Pending:                  {stats.pending_count}")
        print(f"  In progress:              {stats.in_progress_count}")
        print(f"  Done:                     {stats.done_count}")
        print(f"  Overdue:                  {stats.overdue_count}")
        print(f"  With due date:            {stats.tasks_with_due_date_count}")
        print(f"  Completion rate:          {stats.completion_rate:.1%}")
        print()
        input("  Press Enter to continue...")

    def _do_export(self) -> None:
        _clear()
        print("  Export Tasks and Comments\n")
        filepath = _prompt("Output file path")
        if not filepath:
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            result = self._import_export_service.export_to_file(filepath)
            num_tasks = len(result.get("tasks", []))
            num_comments = len(result.get("comments", []))
            print(f"\n  Successfully exported {num_tasks} task(s) and {num_comments} comment(s)")
            print(f"  to {filepath}")
        except IOError as e:
            print(f"\n  Error: Failed to export: {e}")
        input("  Press Enter to continue...")

    def _do_import(self) -> None:
        _clear()
        print("  Import Tasks and Comments\n")
        filepath = _prompt("Input file path")
        if not filepath:
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        _clear()
        print("  Import options:\n")
        print("  1. Add new tasks/comments (skip duplicates)")
        print("  2. Overwrite existing tasks/comments with same IDs")
        print("  0. Cancel")
        print()
        choice = input("  > ").strip()

        if choice == "0":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        overwrite = choice == "2"

        try:
            result = self._import_export_service.import_from_file(filepath, overwrite=overwrite)
            added_tasks = len(result["added_tasks"])
            added_comments = len(result["added_comments"])
            skipped_tasks = len(result["skipped_tasks"])
            skipped_comments = len(result["skipped_comments"])

            _clear()
            print("  Import complete:\n")
            print(f"  Added:   {added_tasks} task(s), {added_comments} comment(s)")
            if skipped_tasks or skipped_comments:
                print(f"  Skipped: {skipped_tasks} task(s), {skipped_comments} comment(s)")
                print("    (duplicates or invalid entries)")
        except FileNotFoundError as e:
            print(f"\n  Error: {e}")
        except ImportExportValidationError as e:
            print(f"\n  Error: Invalid import file: {e}")
        except IOError as e:
            print(f"\n  Error: Failed to import: {e}")
        input("  Press Enter to continue...")

    def _do_manage_projects(self) -> None:
        while True:
            _clear()
            print("  Manage Projects\n")
            projects = self._service.list_projects()
            if projects:
                print("  Projects:")
                for project in projects:
                    print(f"    {project.id[:8]}  {project.name}")
            else:
                print("  (no projects yet)")
            print()
            print("  1. Create project")
            print("  2. View project")
            print("  3. Update project")
            print("  4. Delete project")
            print("  0. Back")
            print()
            choice = input("  > ").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._do_create_project()
            elif choice == "2":
                if projects:
                    self._do_view_project(projects)
            elif choice == "3":
                if projects:
                    self._do_update_project(projects)
            elif choice == "4":
                if projects:
                    self._do_delete_project(projects)

    def _do_create_project(self) -> None:
        _clear()
        print("  Create Project\n")
        name = _prompt("Project name")
        if not name:
            input("  Project name cannot be empty. Press Enter...")
            return

        try:
            project = self._service.add_project(name)
            print(f"\n  Created: {project.id[:8]}  {project.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_view_project(self, projects: list[Project]) -> None:
        _clear()
        print("  View project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]

        _clear()
        print(f"  Project: {project.name}\n")
        print(f"  ID: {project.id}\n")

        tasks = self._service.list_tasks(project_id=project.id)
        if tasks:
            print(f"  Tasks ({len(tasks)}):")
            for task in tasks:
                sym = _STATUS_LABEL[task.status]
                desc = f"  {task.description}" if task.description else ""
                print(f"    {sym} {task.id[:8]}  {task.title}{desc}")
        else:
            print("  (no tasks in this project)")

        print()
        input("  Press Enter to continue...")

    def _do_update_project(self, projects: list[Project]) -> None:
        _clear()
        print("  Update project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]

        _clear()
        print(f"  Editing: {project.name}\n")
        new_name = _prompt("New name", default=project.name)
        if not new_name:
            input("  Project name cannot be empty. Press Enter...")
            return

        try:
            updated = self._service.update_project(project.id, new_name)
            print(f"\n  Updated: {updated.id[:8]}  {updated.name}")
        except (ProjectNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_project(self, projects: list[Project]) -> None:
        _clear()
        print("  Delete project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]

        _clear()
        print(f"  Delete: {project.name}")
        print("  Tasks in this project will become unassigned.")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_project(project.id)
            print(f"  Deleted: {project.id[:8]}  {project.name}")
        except ProjectNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")
