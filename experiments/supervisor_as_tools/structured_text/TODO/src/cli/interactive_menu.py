import os
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..services.comments_service import CommentNotFoundError
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
                self._do_stats()
            elif choice == "8":
                self._do_manage_comments()
            elif choice == "9":
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
        print("  7. View statistics")
        print("  8. Manage comments")
        print("  9. Delete task")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  List Tasks — Choose filter option:\n")
        print("  1. Filter by status")
        print("  2. Filter by due date range")
        print("  3. Show only overdue tasks")
        print("  4. Combine filters (status + date range + overdue)")
        print("  0. Show all tasks")
        print()
        choice = input("  > ").strip()

        if choice == "0":
            status = None
            due_after = None
            due_before = None
            overdue = False
        elif choice == "1":
            _clear()
            print("  Filter by status:\n")
            print("  1. pending")
            print("  2. in progress")
            print("  3. done")
            print("  0. All")
            raw = input("  > ").strip()
            status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
            status = status_map.get(raw)
            due_after = None
            due_before = None
            overdue = False
        elif choice == "2":
            _clear()
            print("  Filter by due date range\n")
            print("  Enter dates in format: YYYY-MM-DD HH:MM (in CEST)")
            print("  Leave blank for no bound\n")
            after_str = _prompt("Due after (start)")
            before_str = _prompt("Due before (end)")

            due_after = None
            due_before = None
            status = None
            overdue = False

            if after_str:
                try:
                    cest = ZoneInfo("Europe/Paris")
                    due_after = datetime.strptime(after_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
                    due_after = due_after.astimezone(timezone.utc)
                except ValueError:
                    _clear()
                    print("  Error: Invalid date format for due_after")
                    input("  Press Enter to continue...")
                    return

            if before_str:
                try:
                    cest = ZoneInfo("Europe/Paris")
                    due_before = datetime.strptime(before_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
                    due_before = due_before.astimezone(timezone.utc)
                except ValueError:
                    _clear()
                    print("  Error: Invalid date format for due_before")
                    input("  Press Enter to continue...")
                    return
        elif choice == "3":
            _clear()
            print("  Show only overdue tasks\n")
            print("  1. All overdue")
            print("  2. Overdue pending")
            print("  3. Overdue in progress")
            print("  0. Back")
            raw = input("  > ").strip()
            status_map = {"1": None, "2": TaskStatus.PENDING, "3": TaskStatus.IN_PROGRESS}
            status = status_map.get(raw)
            if raw == "0" or status is None and raw != "1":
                return
            due_after = None
            due_before = None
            overdue = True
        elif choice == "4":
            _clear()
            print("  Combine filters\n")

            # Status filter
            print("  1. Filter by status:")
            print("    1. pending")
            print("    2. in progress")
            print("    3. done")
            print("    0. All")
            raw = input("    > ").strip()
            status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
            status = status_map.get(raw)

            # Overdue filter
            print("\n  2. Show only overdue? (y/N): ", end="")
            overdue = input().strip().lower() == "y"

            # Date range filter
            due_after = None
            due_before = None
            if not overdue:
                print("\n  3. Filter by due date range?")
                print("    Enter dates in format: YYYY-MM-DD HH:MM (in CEST)")
                print("    Leave blank for no bound\n")
                after_str = _prompt("Due after (start)", default="")
                before_str = _prompt("Due before (end)", default="")

                if after_str:
                    try:
                        cest = ZoneInfo("Europe/Paris")
                        due_after = datetime.strptime(after_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
                        due_after = due_after.astimezone(timezone.utc)
                    except ValueError:
                        _clear()
                        print("  Error: Invalid date format for due_after")
                        input("  Press Enter to continue...")
                        return

                if before_str:
                    try:
                        cest = ZoneInfo("Europe/Paris")
                        due_before = datetime.strptime(before_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
                        due_before = due_before.astimezone(timezone.utc)
                    except ValueError:
                        _clear()
                        print("  Error: Invalid date format for due_before")
                        input("  Press Enter to continue...")
                        return
        else:
            return

        _clear()
        tasks = self._service.list_tasks(status=status, due_before=due_before, due_after=due_after, overdue=overdue)
        filters_applied = []
        if status:
            filters_applied.append(_STATUS_NAME[status])
        if due_after or due_before:
            filters_applied.append("date range")
        if overdue:
            filters_applied.append("overdue")

        filter_label = f" [{', '.join(filters_applied)}]" if filters_applied else " [all]"
        print(f"  Tasks{filter_label}\n")
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
        if task.due_date:
            cest = ZoneInfo("Europe/Paris")
            due_cest = task.due_date.astimezone(cest)
            overdue_marker = " [OVERDUE]" if task.is_overdue() else ""
            print(f"  Due:         {due_cest.strftime('%Y-%m-%d %H:%M CEST')}{overdue_marker}")
        else:
            print(f"  Due:         (none)")
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
        print(f"  Task: {task.title}\n")
        print("  Enter due date in format: YYYY-MM-DD HH:MM (in CEST)")
        print("  Leave blank to clear due date\n")
        due_str = _prompt("Due date")

        if not due_str:
            # Clear due date
            try:
                updated = self._service.set_due_date(task.id, None)
                print(f"\n  Cleared due date for: {_task_line(updated)}")
            except (TaskNotFoundError, ValueError) as e:
                print(f"\n  Error: {e}")
        else:
            try:
                # Parse input in CEST and convert to UTC
                cest = ZoneInfo("Europe/Paris")
                due_cest = datetime.strptime(due_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
                due_utc = due_cest.astimezone(timezone.utc)
                updated = self._service.set_due_date(task.id, due_utc)
                print(f"\n  Set due date for: {_task_line(updated)}")
            except ValueError as e:
                print(f"\n  Error: Invalid date format or date is in the past. {e}")
            except TaskNotFoundError as e:
                print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_manage_comments(self) -> None:
        """Main menu for comment management."""
        while True:
            _clear()
            print("  Manage Comments\n")
            print("  1. View comments for a task")
            print("  2. Add comment to a task")
            print("  3. Delete a comment")
            print("  0. Back")
            print()
            choice = input("  > ").strip().lower()

            if choice in ("0", "q", "quit", "back"):
                return
            elif choice == "1":
                self._do_view_comments()
            elif choice == "2":
                self._do_add_comment()
            elif choice == "3":
                self._do_delete_comment()
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_view_comments(self) -> None:
        """View comments for a selected task."""
        _clear()
        tasks = self._service.list_tasks()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  View comments — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Comments for: {task.title}\n")
        try:
            comments = self._service.list_comments(task.id)
            if not comments:
                print("  (no comments yet)")
            else:
                for comment in comments:
                    print(f"  [{comment.id[:8]}] {comment.created_at.isoformat()}")
                    print(f"    {comment.content}")
        except TaskNotFoundError as e:
            print(f"  Error: {e}")
        print()
        input("  Press Enter to continue...")

    def _do_add_comment(self) -> None:
        """Add a comment to a selected task."""
        _clear()
        tasks = self._service.list_tasks()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Add comment — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Add comment to: {task.title}\n")
        content = _prompt("Comment content")
        if not content:
            input("  Comment cannot be empty. Press Enter...")
            return

        try:
            comment = self._service.add_comment(task.id, content)
            print(f"\n  Added comment: {comment.id[:8]}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_comment(self) -> None:
        """Delete a selected comment."""
        _clear()
        tasks = self._service.list_tasks()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Delete comment — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Comments for: {task.title}\n")
        try:
            comments = self._service.list_comments(task.id)
            if not comments:
                print("  (no comments)")
                input("  Press Enter to continue...")
                return
            comment_lines = [f"[{c.id[:8]}] {c.created_at.isoformat()} — {c.content[:40]}" for c in comments]
            cidx = _pick("Select comment to delete", comment_lines)
            if cidx is None:
                return
            comment = comments[cidx]

            _clear()
            print(f"  Delete comment: {comment.content[:60]}")
            confirm = input("  Are you sure? (y/N): ").strip().lower()
            if confirm != "y":
                print("  Cancelled.")
                input("  Press Enter to continue...")
                return

            self._service.delete_comment(comment.id)
            print(f"  Deleted comment: {comment.id[:8]}")
        except (TaskNotFoundError, CommentNotFoundError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_stats(self) -> None:
        _clear()
        stats = self._service.get_statistics()
        avg_days_str = f"{stats.avg_days_to_completion:.1f}" if stats.avg_days_to_completion is not None else "—"
        print("  Task Statistics")
        print("  ===============================")
        print(f"  Total tasks:            {stats.total_count}")
        print(f"    Pending:              {stats.pending_count}")
        print(f"    In Progress:          {stats.in_progress_count}")
        print(f"    Done:                 {stats.done_count}")
        print(f"  Completion Rate:        {stats.completion_rate:.1f}%")
        print(f"  Overdue:                {stats.overdue_count}")
        print(f"  With due date:          {stats.tasks_with_due_date}")
        print(f"  Avg days to completion: {avg_days_str}")
        print()
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
