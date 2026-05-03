import os
import re
from datetime import datetime, timezone
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
            elif choice == "8":
                self._do_manage_comments(tasks)
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
        print("  8. Manage comments")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        """Display filter submenu and list tasks with selected filters."""
        status = None
        before = None
        after = None
        overdue_only = False

        while True:
            _clear()
            print("  Filter tasks:\n")
            print("  1. Filter by status")
            print("  2. Filter by due date range")
            print("  3. Filter by week")
            print("  4. Filter by month")
            print("  5. Filter by year")
            print("  6. Show only overdue tasks")
            print("  7. View results")
            print("  0. Back")
            print()
            choice = input("  > ").strip().lower()

            if choice in ("0", "q", "quit"):
                return
            elif choice == "1":
                status = self._do_pick_status()
            elif choice == "2":
                before, after = self._do_pick_due_date_range()
            elif choice == "3":
                tasks_week = self._do_pick_week(status)
                if tasks_week is not None:
                    self._display_task_list(tasks_week, "week filter")
            elif choice == "4":
                tasks_month = self._do_pick_month(status)
                if tasks_month is not None:
                    self._display_task_list(tasks_month, "month filter")
            elif choice == "5":
                tasks_year = self._do_pick_year(status)
                if tasks_year is not None:
                    self._display_task_list(tasks_year, "year filter")
            elif choice == "6":
                overdue_only = not overdue_only
                print(f"  Overdue filter: {'enabled' if overdue_only else 'disabled'}")
                input("  Press Enter to continue...")
            elif choice == "7":
                tasks = self._service.list_tasks(
                    status=status, before=before, after=after, overdue_only=overdue_only
                )
                self._display_task_list_with_summary(tasks, status, before, after, overdue_only)

    def _do_pick_status(self) -> Optional[TaskStatus]:
        """Prompt user to pick a status filter."""
        _clear()
        print("  Filter by status:\n")
        print("  1. pending")
        print("  2. in progress")
        print("  3. done")
        print("  0. No status filter")
        print()
        raw = input("  > ").strip()
        status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
        return status_map.get(raw)

    def _do_pick_due_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Prompt user for due date range (before/after)."""
        _clear()
        print("  Filter by due date range:\n")
        before_str = _prompt("Due before (ISO 8601, or leave blank)") or None
        before = None
        if before_str:
            try:
                before = datetime.fromisoformat(before_str)
            except ValueError:
                print("  Error: Invalid date format. Use ISO 8601 (e.g., 2026-05-15T23:59:59+00:00)")
                input("  Press Enter to continue...")
                return None, None

        after_str = _prompt("Due after (ISO 8601, or leave blank)") or None
        after = None
        if after_str:
            try:
                after = datetime.fromisoformat(after_str)
            except ValueError:
                print("  Error: Invalid date format. Use ISO 8601 (e.g., 2026-05-01T00:00:00+00:00)")
                input("  Press Enter to continue...")
                return None, None

        if before or after:
            print("  Date range filter set.")
        else:
            print("  No date range filter applied.")
        input("  Press Enter to continue...")
        return before, after

    def _do_pick_week(self, status: Optional[TaskStatus]) -> Optional[list[Task]]:
        """Prompt user for ISO 8601 week and return filtered tasks."""
        _clear()
        print("  Filter by ISO 8601 week:\n")
        week_str = _prompt("Week (YYYY-Www, e.g., 2026-W20)") or None
        if not week_str:
            return None

        match = re.match(r'^(\d{4})-W(\d{2})$', week_str)
        if not match:
            print("  Error: Invalid format. Use YYYY-Www (e.g., 2026-W20)")
            input("  Press Enter to continue...")
            return None

        try:
            year = int(match.group(1))
            week = int(match.group(2))
            return self._service.list_tasks_by_week(year, week, status)
        except ValueError as e:
            print(f"  Error: {e}")
            input("  Press Enter to continue...")
            return None

    def _do_pick_month(self, status: Optional[TaskStatus]) -> Optional[list[Task]]:
        """Prompt user for month (YYYY-MM) and return filtered tasks."""
        _clear()
        print("  Filter by month:\n")
        month_str = _prompt("Month (YYYY-MM, e.g., 2026-05)") or None
        if not month_str:
            return None

        match = re.match(r'^(\d{4})-(\d{2})$', month_str)
        if not match:
            print("  Error: Invalid format. Use YYYY-MM (e.g., 2026-05)")
            input("  Press Enter to continue...")
            return None

        try:
            year = int(match.group(1))
            month = int(match.group(2))
            return self._service.list_tasks_by_month(year, month, status)
        except ValueError as e:
            print(f"  Error: {e}")
            input("  Press Enter to continue...")
            return None

    def _do_pick_year(self, status: Optional[TaskStatus]) -> Optional[list[Task]]:
        """Prompt user for year (YYYY) and return filtered tasks."""
        _clear()
        print("  Filter by year:\n")
        year_str = _prompt("Year (YYYY, e.g., 2026)") or None
        if not year_str:
            return None

        match = re.match(r'^(\d{4})$', year_str)
        if not match:
            print("  Error: Invalid format. Use YYYY (e.g., 2026)")
            input("  Press Enter to continue...")
            return None

        try:
            year = int(match.group(1))
            return self._service.list_tasks_by_year(year, status)
        except ValueError as e:
            print(f"  Error: {e}")
            input("  Press Enter to continue...")
            return None

    def _display_task_list(self, tasks: list[Task], label: str) -> None:
        """Display a list of tasks with label."""
        _clear()
        print(f"  Tasks ({label})\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                due_str = ""
                if task.due_date:
                    due_str = f"  (due: {task.due_date.strftime('%Y-%m-%d')})"
                print(f"  {_task_line(task)}{desc}{due_str}")
        print()
        input("  Press Enter to continue...")

    def _display_task_list_with_summary(
        self,
        tasks: list[Task],
        status: Optional[TaskStatus],
        before: Optional[datetime],
        after: Optional[datetime],
        overdue_only: bool,
    ) -> None:
        """Display filtered tasks with filter summary."""
        _clear()
        print("  Filtered Tasks\n")
        if status:
            print(f"  Status: {_STATUS_NAME[status]}")
        if after:
            print(f"  Due after: {after.strftime('%Y-%m-%d')}")
        if before:
            print(f"  Due before: {before.strftime('%Y-%m-%d')}")
        if overdue_only:
            print("  Showing: only overdue")
        print()

        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                due_str = ""
                if task.due_date:
                    due_str = f"  (due: {task.due_date.strftime('%Y-%m-%d')})"
                print(f"  {_task_line(task)}{desc}{due_str}")
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
        self._do_manage_existing_comment(task)

    def _do_manage_existing_comment(self, task: Task) -> None:
        while True:
            _clear()
            print(f"  Manage comments for: {task.title}\n")
            comments = self._service.get_comments(task.id)
            if not comments:
                print("  (no comments yet)")
            else:
                for comment in comments:
                    author_str = f" — {comment.author}" if comment.author else ""
                    print(f"  {comment.id[:8]}{author_str}: {comment.content[:50]}")
            print()
            print("  1. Add comment")
            print("  2. View / edit / delete comment")
            print("  0. Back")
            print()
            choice = input("  > ").strip().lower()

            if choice in ("0", "q", "quit"):
                return
            elif choice == "1":
                self._do_add_comment(task)
            elif choice == "2":
                if not comments:
                    input("  No comments. Press Enter...")
                    continue
                self._do_pick_comment(task)

    def _do_add_comment(self, task: Task) -> None:
        _clear()
        print(f"  Add comment to: {task.title}\n")
        content = _prompt("Comment content")
        if not content:
            input("  Content cannot be empty. Press Enter...")
            return
        author = _prompt("Author (optional)") or None
        try:
            comment = self._service.add_comment(task.id, content, author)
            print(f"\n  Added comment {comment.id[:8]}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_pick_comment(self, task: Task) -> None:
        _clear()
        print(f"  Pick a comment to view/edit/delete:\n")
        comments = self._service.get_comments(task.id)
        comment_options = [
            f"{c.id[:8]} — {c.content[:40]}" for c in comments
        ]
        idx = _pick("Select", comment_options)
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        author_str = f"Author: {comment.author}" if comment.author else "Author: (none)"
        print(f"  Comment: {comment.id}\n")
        print(f"  {author_str}")
        print(f"  Created: {comment.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if comment.updated_at:
            print(f"  Updated: {comment.updated_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"\n  Content:\n  {comment.content}\n")
        print("  1. Edit comment")
        print("  2. Delete comment")
        print("  0. Back")
        choice = input("  > ").strip().lower()

        if choice == "1":
            self._do_edit_comment_content(task, comment)
        elif choice == "2":
            _clear()
            print(f"  Delete comment: {comment.id[:8]}")
            confirm = input("  Are you sure? (y/N): ").strip().lower()
            if confirm != "y":
                print("  Cancelled.")
                input("  Press Enter to continue...")
                return
            try:
                self._service.delete_comment(task.id, comment.id)
                print("  Deleted comment.")
            except ValueError as e:
                print(f"  Error: {e}")
            input("  Press Enter to continue...")

    def _do_edit_comment_content(self, task: Task, comment) -> None:
        _clear()
        print(f"  Edit comment: {comment.id[:8]}\n")
        new_content = _prompt("New content", default=comment.content)
        if not new_content:
            input("  Content cannot be empty. Press Enter...")
            return
        try:
            updated = self._service.edit_comment(task.id, comment.id, new_content)
            print(f"\n  Updated comment")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")
