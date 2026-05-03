import os
from datetime import datetime
from typing import Optional

from ..models.task import Task
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
                self._do_check_status(tasks)
            elif choice == "7":
                self._do_delete(tasks)
            elif choice == "8":
                self._do_manage_comments(tasks)
            elif choice == "9":
                self._do_filter_by_date()
            elif choice == "10":
                self._do_show_report()
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
        print("  1. List / filter tasks by status")
        print("  2. Add task")
        print("  3. Show task details")
        print("  4. Change status  (start / done / reopen)")
        print("  5. Update task    (title / description)")
        print("  6. Check task status (pending / in progress / completed / overdue)")
        print("  7. Delete task")
        print("  8. Manage comments")
        print("  9. Filter tasks by date/overdue")
        print("  10. View task summary report")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  Filter by status:")
        print("  1. pending")
        print("  2. in progress")
        print("  3. done")
        print("  0. All statuses")
        raw = input("  > ").strip()
        status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
        status = status_map.get(raw)

        _clear()
        print("  Additional filters:")
        print("  1. Show only overdue tasks")
        print("  2. Filter by due date range")
        print("  0. No additional filters")
        filter_choice = input("  > ").strip()

        due_before = None
        due_after = None
        overdue = None

        if filter_choice == "1":
            overdue = True
        elif filter_choice == "2":
            _clear()
            print("  Due date filters:\n")
            due_after_str = _prompt("Due after (ISO datetime, e.g., 2026-01-01T00:00:00+01:00)", "")
            if due_after_str:
                try:
                    due_after = datetime.fromisoformat(due_after_str)
                except ValueError:
                    print("  Invalid ISO datetime format, ignoring...")
                    input("  Press Enter to continue...")
                    return

            due_before_str = _prompt("Due before (ISO datetime, e.g., 2026-12-31T23:59:59+01:00)", "")
            if due_before_str:
                try:
                    due_before = datetime.fromisoformat(due_before_str)
                except ValueError:
                    print("  Invalid ISO datetime format, ignoring...")
                    input("  Press Enter to continue...")
                    return

        _clear()
        tasks = self._service.list_tasks(status=status, due_before=due_before, due_after=due_after, overdue=overdue)
        filter_labels = []
        if status:
            filter_labels.append(_STATUS_NAME[status])
        if overdue:
            filter_labels.append("overdue")
        if due_before or due_after:
            filter_labels.append("date range")
        label = f"[{' + '.join(filter_labels)}]" if filter_labels else "[all]"
        print(f"  Tasks {label}\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                due_str = f" (due: {task.due_date.isoformat()})" if task.due_date else ""
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

    def _do_check_status(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Check status — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}\n")
        is_pending = self._service.is_task_pending(task.id)
        is_in_progress = self._service.is_task_in_progress(task.id)
        is_completed = self._service.is_task_completed(task.id)
        is_overdue = self._service.is_task_overdue(task.id)

        print(f"  Is pending:      {is_pending}")
        print(f"  Is in progress:  {is_in_progress}")
        print(f"  Is completed:    {is_completed}")
        print(f"  Is overdue:      {is_overdue}")
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

    def _do_manage_comments(self, tasks: list[Task]) -> None:
        """Manage comments for a selected task."""
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
                    print(f"    {comment.id[:8]}{author_str}:")
                    print(f"      {comment.content}")
                    if comment.updated_at:
                        print(f"      (edited)")
            else:
                print("  (no comments yet)")
            print()
            print("  1. Add comment")
            print("  2. Edit comment")
            print("  3. Delete comment")
            print("  0. Back")
            print()

            choice = input("  > ").strip().lower()
            if choice == "0":
                break
            elif choice == "1":
                self._do_add_comment(task.id)
            elif choice == "2":
                self._do_edit_comment(task.id)
            elif choice == "3":
                self._do_delete_comment(task.id)
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_add_comment(self, task_id: str) -> None:
        _clear()
        print(f"  Add comment\n")
        author = _prompt("Author (optional)")
        content = _prompt("Comment content")
        if not content:
            input("  Comment cannot be empty. Press Enter...")
            return
        try:
            self._service.add_comment(task_id, content, author or None)
            print(f"\n  Added comment")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_edit_comment(self, task_id: str) -> None:
        _clear()
        print(f"  Edit comment\n")
        comments = self._service.list_comments(task_id)
        if not comments:
            input("  No comments. Press Enter...")
            return
        print("  Edit comment — pick one:\n")
        idx = _pick("Select", [f"{c.id[:8]} — {c.content[:50]}" for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Editing comment:\n")
        new_content = _prompt("New content", default=comment.content)
        if not new_content:
            input("  Comment cannot be empty. Press Enter...")
            return
        try:
            self._service.edit_comment(comment.id, new_content)
            print(f"\n  Updated comment")
        except CommentNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_comment(self, task_id: str) -> None:
        _clear()
        print(f"  Delete comment\n")
        comments = self._service.list_comments(task_id)
        if not comments:
            input("  No comments. Press Enter...")
            return
        print("  Delete comment — pick one:\n")
        idx = _pick("Select", [f"{c.id[:8]} — {c.content[:50]}" for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Delete: {comment.content[:60]}")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_comment(comment.id)
            print(f"  Deleted comment")
        except CommentNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_filter_by_date(self) -> None:
        """Filter tasks by date range and/or overdue status."""
        _clear()
        print("  Filter by date/overdue\n")

        # Ask about filtering options
        print("  Filter options (leave blank to skip):")
        print("  1. Due date before (ISO format, e.g., 2026-12-31T23:59:59+01:00)")
        print("  2. Due date after (ISO format, e.g., 2026-01-01T00:00:00+01:00)")
        print("  3. Show only overdue tasks")
        print()

        before_str = _prompt("Due before (optional)")
        after_str = _prompt("Due after (optional)")
        overdue_str = input("  Show only overdue? (y/N): ").strip().lower()

        before = None
        after = None
        overdue = None

        if before_str:
            try:
                before = datetime.fromisoformat(before_str)
            except ValueError:
                print("  Error: Invalid datetime format for 'before'")
                input("  Press Enter to continue...")
                return

        if after_str:
            try:
                after = datetime.fromisoformat(after_str)
            except ValueError:
                print("  Error: Invalid datetime format for 'after'")
                input("  Press Enter to continue...")
                return

        if overdue_str == "y":
            overdue = True

        _clear()
        tasks = self._service.list_tasks(before=before, after=after, overdue=overdue)
        label_parts = []
        if before:
            label_parts.append(f"before {before.isoformat()}")
        if after:
            label_parts.append(f"after {after.isoformat()}")
        if overdue:
            label_parts.append("overdue")

        label = f"[{', '.join(label_parts)}]" if label_parts else "[all]"
        print(f"  Tasks {label}\n")

        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                due_str = f" (due: {task.due_date.isoformat()})" if task.due_date else ""
                print(f"  {_task_line(task)}{desc}{due_str}")
        print()
        input("  Press Enter to continue...")

    def _do_show_report(self) -> None:
        """Display task summary report."""
        _clear()
        report = self._service.generate_report()
        print("  Task Summary Report\n")
        print(f"  Total tasks:              {report.total_tasks}")
        print(f"  Pending:                  {report.pending_count}")
        print(f"  In progress:              {report.in_progress_count}")
        print(f"  Done:                     {report.done_count}")
        print(f"  Overdue:                  {report.overdue_count}")
        print(f"  With due date:            {report.with_due_date_count}")
        print(f"  Completion rate:          {report.completion_rate:.1f}%")
        if report.avg_days_to_completion is not None:
            print(f"  Avg days to completion:   {report.avg_days_to_completion:.2f}")
        print()
        input("  Press Enter to continue...")
