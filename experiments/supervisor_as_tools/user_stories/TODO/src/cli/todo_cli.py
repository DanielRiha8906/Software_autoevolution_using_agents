import argparse
import sys
from typing import Optional

from ..models.task_status import TaskStatus
from ..services.comments_service import CommentNotFoundError
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage
from ..utils.datetime_utils import parse_datetime_or_iso_string

_STATUS_SYMBOLS = {
    TaskStatus.PENDING: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
}


class TodoCLI:
    def __init__(self, storage_path: Optional[str] = None) -> None:
        storage = JsonStorage(storage_path) if storage_path else JsonStorage()
        self._service = TodoService(storage)

    def run(self, argv: Optional[list[str]] = None) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)
        if not hasattr(args, "func"):
            parser.print_help()
            return 0
        try:
            return args.func(args)
        except TaskNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except CommentNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
        prog="todo",
        description=(
        "Simple TODO manager.\n\n"
        "Task IDs are UUIDs.\nIn CLI commands you can use a unique prefix "
        "\n(e.g. first 8 characters shown in 'list')."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        )
        sub = parser.add_subparsers(title="commands")

        # add
        p_add = sub.add_parser("add", help="Add a new task")
        p_add.add_argument("title", help="Task title")
        p_add.add_argument("-d", "--description", help="Optional description")
        p_add.add_argument("--due-date", help="Due date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+02:00)")
        p_add.set_defaults(func=self._cmd_add)

        # list
        p_list = sub.add_parser("list", help="List tasks")
        p_list.add_argument(
            "--status",
            choices=["pending", "in_progress", "done"],
            help="Filter by status",
        )
        p_list.add_argument(
            "--due-before",
            help="Filter to tasks due on or before this date (ISO 8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+02:00)",
        )
        p_list.add_argument(
            "--due-after",
            help="Filter to tasks due on or after this date (ISO 8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+02:00)",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Filter to overdue tasks only (past due date and not completed)",
        )
        p_list.set_defaults(func=self._cmd_list)

        # show
        p_show = sub.add_parser("show", help="Show task details")
        p_show.add_argument("id", help="Task ID")
        p_show.set_defaults(func=self._cmd_show)

        # start
        p_start = sub.add_parser("start", help="Mark task as in-progress")
        p_start.add_argument("id", help="Task ID")
        p_start.set_defaults(func=self._cmd_start)

        # done
        p_done = sub.add_parser("done", help="Mark task as done")
        p_done.add_argument("id", help="Task ID")
        p_done.set_defaults(func=self._cmd_done)

        # reopen
        p_reopen = sub.add_parser("reopen", help="Reopen a task")
        p_reopen.add_argument("id", help="Task ID")
        p_reopen.set_defaults(func=self._cmd_reopen)

        # update
        p_update = sub.add_parser("update", help="Update task title or description")
        p_update.add_argument("id", help="Task ID")
        p_update.add_argument("-t", "--title", help="New title")
        p_update.add_argument("-d", "--description", help="New description")
        p_update.add_argument("--due-date", help="Due date (ISO 8601 format)")
        p_update.set_defaults(func=self._cmd_update)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # mark-in-progress
        p_mark_in_progress = sub.add_parser("mark-in-progress", help="Mark task as in-progress")
        p_mark_in_progress.add_argument("id", help="Task ID")
        p_mark_in_progress.set_defaults(func=self._cmd_mark_in_progress)

        # mark-done
        p_mark_done = sub.add_parser("mark-done", help="Mark task as done")
        p_mark_done.add_argument("id", help="Task ID")
        p_mark_done.set_defaults(func=self._cmd_mark_done)

        # is-pending
        p_is_pending = sub.add_parser("is-pending", help="Check if task is pending")
        p_is_pending.add_argument("id", help="Task ID")
        p_is_pending.set_defaults(func=self._cmd_is_pending)

        # is-in-progress
        p_is_in_progress = sub.add_parser("is-in-progress", help="Check if task is in-progress")
        p_is_in_progress.add_argument("id", help="Task ID")
        p_is_in_progress.set_defaults(func=self._cmd_is_in_progress)

        # is-completed
        p_is_completed = sub.add_parser("is-completed", help="Check if task is completed")
        p_is_completed.add_argument("id", help="Task ID")
        p_is_completed.set_defaults(func=self._cmd_is_completed)

        # is-overdue
        p_is_overdue = sub.add_parser("is-overdue", help="Check if task is overdue")
        p_is_overdue.add_argument("id", help="Task ID")
        p_is_overdue.set_defaults(func=self._cmd_is_overdue)

        # add-comment
        p_add_comment = sub.add_parser("add-comment", help="Add a comment to a task")
        p_add_comment.add_argument("task_id", help="Task ID")
        p_add_comment.add_argument("--content", required=True, help="Comment content")
        p_add_comment.add_argument("--long", action="store_true", help="Show full IDs")
        p_add_comment.set_defaults(func=self._cmd_add_comment)

        # list-comments
        p_list_comments = sub.add_parser("list-comments", help="List comments for a task")
        p_list_comments.add_argument("task_id", help="Task ID")
        p_list_comments.add_argument("--long", action="store_true", help="Show full IDs")
        p_list_comments.set_defaults(func=self._cmd_list_comments)

        # show-comment
        p_show_comment = sub.add_parser("show-comment", help="Show comment details")
        p_show_comment.add_argument("id", help="Comment ID")
        p_show_comment.add_argument("--long", action="store_true", help="Show full ID")
        p_show_comment.set_defaults(func=self._cmd_show_comment)

        # update-comment
        p_update_comment = sub.add_parser("update-comment", help="Update a comment")
        p_update_comment.add_argument("id", help="Comment ID")
        p_update_comment.add_argument("--content", required=True, help="New comment content")
        p_update_comment.add_argument("--long", action="store_true", help="Show full ID")
        p_update_comment.set_defaults(func=self._cmd_update_comment)

        # delete-comment
        p_delete_comment = sub.add_parser("delete-comment", help="Delete a comment")
        p_delete_comment.add_argument("id", help="Comment ID")
        p_delete_comment.set_defaults(func=self._cmd_delete_comment)

        # report
        p_report = sub.add_parser("report", help="View task summary report")
        p_report.set_defaults(func=self._cmd_report)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        due_date = None
        if hasattr(args, 'due_date') and args.due_date:
            try:
                due_date = parse_datetime_or_iso_string(args.due_date)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
        task = self._service.add_task(args.title, args.description, due_date)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None

        # Parse and validate date filters
        due_before = None
        due_after = None
        if hasattr(args, 'due_before') and args.due_before:
            try:
                due_before = parse_datetime_or_iso_string(args.due_before)
            except ValueError as e:
                print(f"Error parsing --due-before: {e}", file=sys.stderr)
                return 1

        if hasattr(args, 'due_after') and args.due_after:
            try:
                due_after = parse_datetime_or_iso_string(args.due_after)
            except ValueError as e:
                print(f"Error parsing --due-after: {e}", file=sys.stderr)
                return 1

        # Validate date range
        if due_before is not None and due_after is not None and due_after > due_before:
            print("Error: --due-after cannot be after --due-before", file=sys.stderr)
            return 1

        overdue_only = hasattr(args, 'overdue') and args.overdue

        tasks = self._service.list_tasks(
            status=status,
            due_before=due_before,
            due_after=due_after,
            overdue_only=overdue_only,
        )
        if not tasks:
            print("No tasks found.")
            return 0
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}")
        return 0

    def _cmd_show(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        print(f"ID:          {task.id}")
        print(f"Title:       {task.title}")
        print(f"Description: {task.description or '—'}")
        print(f"Status:      {task.status.value}")
        print(f"Created:     {task.created_at.isoformat()}")
        print(f"Updated:     {task.updated_at.isoformat()}")
        if task.due_date:
            print(f"Due:         {task.due_date.strftime('%Y-%m-%d %H:%M %Z')}")
        else:
            print(f"Due:         —")
        return 0

    def _cmd_start(self, args: argparse.Namespace) -> int:
        task = self._service.start_task(args.id)
        print(f"Started {task.id[:8]}  {task.title}")
        return 0

    def _cmd_done(self, args: argparse.Namespace) -> int:
        task = self._service.complete_task(args.id)
        print(f"Completed {task.id[:8]}  {task.title}")
        return 0

    def _cmd_reopen(self, args: argparse.Namespace) -> int:
        task = self._service.reopen_task(args.id)
        print(f"Reopened {task.id[:8]}  {task.title}")
        return 0

    def _cmd_update(self, args: argparse.Namespace) -> int:
        due_date = None
        if hasattr(args, 'due_date') and args.due_date:
            try:
                due_date = parse_datetime_or_iso_string(args.due_date)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
        task = self._service.update_task(args.id, title=args.title, description=args.description, due_date=due_date)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_mark_in_progress(self, args: argparse.Namespace) -> int:
        task = self._service.mark_in_progress(args.id)
        print(f"Started {task.id[:8]}  {task.title}")
        return 0

    def _cmd_mark_done(self, args: argparse.Namespace) -> int:
        task = self._service.mark_done(args.id)
        print(f"Completed {task.id[:8]}  {task.title}")
        return 0

    def _cmd_is_pending(self, args: argparse.Namespace) -> int:
        result = self._service.is_pending(args.id)
        print("true" if result else "false")
        return 0

    def _cmd_is_in_progress(self, args: argparse.Namespace) -> int:
        result = self._service.is_in_progress(args.id)
        print("true" if result else "false")
        return 0

    def _cmd_is_completed(self, args: argparse.Namespace) -> int:
        result = self._service.is_completed(args.id)
        print("true" if result else "false")
        return 0

    def _cmd_is_overdue(self, args: argparse.Namespace) -> int:
        result = self._service.is_overdue(args.id)
        print("true" if result else "false")
        return 0

    # ── Comment commands ───────────────────────────────────────────────────

    def _cmd_add_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.task_id, args.content)
        comment_id = comment.id if hasattr(args, 'long') and args.long else comment.id[:8]
        print(f"Added comment {comment_id}")
        return 0

    def _cmd_list_comments(self, args: argparse.Namespace) -> int:
        comments = self._service.list_task_comments(args.task_id)
        if not comments:
            print("No comments found.")
            return 0
        for comment in comments:
            comment_id = comment.id if hasattr(args, 'long') and args.long else comment.id[:8]
            print(f"{comment_id}  {comment.content[:50]}")
        return 0

    def _cmd_show_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.get_comment(args.id)
        comment_id = comment.id if hasattr(args, 'long') and args.long else comment.id
        print(f"ID:        {comment_id}")
        print(f"Task ID:   {comment.task_id[:8]}")
        print(f"Content:   {comment.content}")
        print(f"Author:    {comment.author or '—'}")
        print(f"Created:   {comment.created_at.isoformat()}")
        print(f"Updated:   {comment.updated_at.isoformat()}")
        return 0

    def _cmd_update_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.update_comment(args.id, args.content)
        comment_id = comment.id if hasattr(args, 'long') and args.long else comment.id[:8]
        print(f"Updated comment {comment_id}")
        return 0

    def _cmd_delete_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.get_comment(args.id)
        self._service.delete_comment(args.id)
        comment_id = comment.id[:8]
        print(f"Deleted comment {comment_id}")
        return 0

    def _cmd_report(self, args: argparse.Namespace) -> int:
        report = self._service.generate_summary_report()
        print("\n  Task Summary Report\n")
        for line in str(report).split("\n"):
            print(f"  {line}")
        print()
        return 0
