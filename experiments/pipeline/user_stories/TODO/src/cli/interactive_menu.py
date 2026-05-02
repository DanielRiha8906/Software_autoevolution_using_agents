import os
from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
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
                self._do_set_due_date(tasks)
            elif choice == "7":
                self._do_delete(tasks)
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
        print("  6. Set due date")
        print("  7. Delete task")
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

        _clear()
        tasks = self._service.list_tasks(status)
        label = f"[{_STATUS_NAME[status]}]" if status else "[all]"
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
        due_date_str = _prompt("Due date (optional, ISO 8601, e.g., 2026-05-02T15:30:00+02:00)") or None
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                print(f"\n  Error: Invalid date format. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
                input("  Press Enter to continue...")
                return
        try:
            task = self._service.add_task(title, description, due_date)
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
        due_date_str = task.due_date.isoformat() if task.due_date else "—"
        print(f"  Due date:    {due_date_str}")
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
        due_date_default = task.due_date.isoformat() if task.due_date else ""
        new_due_date_str = _prompt("New due date (ISO 8601)", default=due_date_default) or None
        new_due_date = None
        if new_due_date_str:
            try:
                new_due_date = datetime.fromisoformat(new_due_date_str)
            except ValueError:
                print(f"\n  Error: Invalid date format. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
                input("  Press Enter to continue...")
                return

        try:
            updated = self._service.update_task(task.id, title=new_title or None, description=new_desc, due_date=new_due_date)
            print(f"\n  Updated: {_task_line(updated)}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_set_due_date(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Set due date — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}  (current: {task.due_date.isoformat() if task.due_date else 'no due date'})\n")
        due_date_str = _prompt("New due date (ISO 8601, or leave blank to clear)") or None
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                print(f"\n  Error: Invalid date format. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
                input("  Press Enter to continue...")
                return

        try:
            updated = self._service.set_due_date(task.id, due_date)
            due_date_display = updated.due_date.isoformat() if updated.due_date else "cleared"
            print(f"\n  Updated: {_task_line(updated)} (due: {due_date_display})")
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
