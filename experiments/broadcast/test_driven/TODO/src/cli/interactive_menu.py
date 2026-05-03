import os
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..services.project_service import ProjectService
from ..services.statistics_service import TaskStatisticsService
from ..services.comments_service import CommentsService
from ..services.import_export_service import TaskImportExportService
from ..storage.json_storage import JsonStorage

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
        self._project_service = ProjectService(self._service)
        self._comments_service = CommentsService()
        self._import_export_service = TaskImportExportService(self._service, self._comments_service)

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
                self._do_statistics()
            elif choice == "8":
                self._do_export()
            elif choice == "9":
                self._do_import()
            elif choice == "10":
                self._do_project_list()
            elif choice == "11":
                self._do_project_create()
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
        print("  7. View statistics")
        print("  8. Export to JSON")
        print("  9. Import from JSON")
        print("  10. List projects")
        print("  11. Create project")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  Filter options:")
        print("  1. By status")
        print("  2. Overdue only")
        print("  0. All tasks")
        raw = input("  > ").strip()

        status = None
        overdue = False

        if raw == "1":
            _clear()
            print("  Filter by status:")
            print("  1. pending")
            print("  2. in progress")
            print("  3. done")
            print("  0. Back")
            raw = input("  > ").strip()
            status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
            status = status_map.get(raw)
        elif raw == "2":
            overdue = True

        _clear()
        try:
            tasks = self._service.list_tasks(status=status, overdue=overdue)
        except ValueError as e:
            print(f"  Error: {e}")
            input("  Press Enter to continue...")
            return

        if status:
            label = f"[{_STATUS_NAME[status]}]"
        elif overdue:
            label = "[overdue]"
        else:
            label = "[all]"
        print(f"  Tasks {label}\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                print(f"  {_task_line(task)}{desc}")
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

    def _do_statistics(self) -> None:
        _clear()
        print("  Task Statistics\n")
        stats_svc = TaskStatisticsService(self._service)
        report = stats_svc.compute()
        print(f"  Total tasks:           {report.total}")
        print(f"  Pending:               {report.count_per_status[TaskStatus.PENDING]}")
        print(f"  In Progress:           {report.count_per_status[TaskStatus.IN_PROGRESS]}")
        print(f"  Done:                  {report.count_per_status[TaskStatus.DONE]}")
        print(f"  Completion rate:       {report.completion_rate:.1f}%")
        print(f"  Tasks with due date:   {report.with_due_date_count}")
        print(f"  Overdue tasks:         {report.overdue_count}")
        print()
        input("  Press Enter to continue...")

    def _do_export(self) -> None:
        _clear()
        print("  Export tasks and comments\n")
        path = _prompt("Export file path")
        if not path:
            print("  Path cannot be empty.")
            input("  Press Enter to continue...")
            return
        try:
            self._import_export_service.export(path)
            print(f"\n  Exported to {path}")
        except IOError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_import(self) -> None:
        _clear()
        print("  Import tasks and comments\n")
        path = _prompt("Import file path")
        if not path:
            print("  Path cannot be empty.")
            input("  Press Enter to continue...")
            return
        try:
            self._import_export_service.import_from(path)
            print(f"\n  Imported from {path}")
        except (FileNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_project_list(self) -> None:
        _clear()
        print("  Projects\n")
        projects = self._project_service.list()
        if not projects:
            print("  (no projects yet)")
        else:
            for project in projects:
                print(f"  {project.id[:8]}  {project.name}")
        print()
        input("  Press Enter to continue...")

    def _do_project_create(self) -> None:
        _clear()
        print("  Create new project\n")
        name = _prompt("Project name")
        if not name:
            input("  Project name cannot be empty. Press Enter...")
            return
        try:
            project = self._project_service.create(name)
            print(f"\n  Created: {project.id[:8]}  {project.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")
