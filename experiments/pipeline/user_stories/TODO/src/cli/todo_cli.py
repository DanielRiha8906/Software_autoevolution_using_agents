import argparse
import sys
from datetime import datetime
from typing import Optional

from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage

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
        p_add.add_argument("--due-date", help="Due date (ISO 8601 format, e.g., 2026-05-02T15:30:00+02:00)")
        p_add.set_defaults(func=self._cmd_add)

        # list
        p_list = sub.add_parser("list", help="List tasks")
        p_list.add_argument(
            "--status",
            choices=["pending", "in_progress", "done"],
            help="Filter by status",
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
        p_update.add_argument("--due-date", help="Due date (ISO 8601 format, e.g., 2026-05-02T15:30:00+02:00)")
        p_update.set_defaults(func=self._cmd_update)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # due-date
        p_due_date = sub.add_parser("due-date", help="Set due date on a task")
        p_due_date.add_argument("id", help="Task ID")
        p_due_date.add_argument("--date", help="Due date (ISO 8601 format, e.g., 2026-05-02T15:30:00+02:00)")
        p_due_date.set_defaults(func=self._cmd_due_date)

        # add-comment
        p_add_comment = sub.add_parser("add-comment", help="Add a comment to a task")
        p_add_comment.add_argument("id", help="Task ID")
        p_add_comment.add_argument("content", help="Comment content")
        p_add_comment.add_argument("-a", "--author", help="Optional author name")
        p_add_comment.set_defaults(func=self._cmd_add_comment)

        # list-comments
        p_list_comments = sub.add_parser("list-comments", help="List comments for a task")
        p_list_comments.add_argument("id", help="Task ID")
        p_list_comments.set_defaults(func=self._cmd_list_comments)

        # delete-comment
        p_delete_comment = sub.add_parser("delete-comment", help="Delete a comment from a task")
        p_delete_comment.add_argument("task_id", help="Task ID")
        p_delete_comment.add_argument("comment_id", help="Comment ID")
        p_delete_comment.set_defaults(func=self._cmd_delete_comment)

        # edit-comment
        p_edit_comment = sub.add_parser("edit-comment", help="Edit a comment on a task")
        p_edit_comment.add_argument("task_id", help="Task ID")
        p_edit_comment.add_argument("comment_id", help="Comment ID")
        p_edit_comment.add_argument("content", help="New comment content")
        p_edit_comment.set_defaults(func=self._cmd_edit_comment)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        due_date = None
        if args.due_date:
            try:
                due_date = datetime.fromisoformat(args.due_date)
            except ValueError:
                raise ValueError(f"Invalid date format: {args.due_date}. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
        task = self._service.add_task(args.title, args.description, due_date)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        tasks = self._service.list_tasks(status)
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
        print(f"Due date:    {task.due_date.isoformat() if task.due_date else '—'}")
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
        if args.due_date:
            try:
                due_date = datetime.fromisoformat(args.due_date)
            except ValueError:
                raise ValueError(f"Invalid date format: {args.due_date}. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
        task = self._service.update_task(args.id, title=args.title, description=args.description, due_date=due_date)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_due_date(self, args: argparse.Namespace) -> int:
        due_date = None
        if args.date:
            try:
                due_date = datetime.fromisoformat(args.date)
            except ValueError:
                raise ValueError(f"Invalid date format: {args.date}. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
        task = self._service.set_due_date(args.id, due_date)
        due_date_str = task.due_date.isoformat() if task.due_date else "—"
        print(f"Set due date for {task.id[:8]}  {task.title}: {due_date_str}")
        return 0

    def _cmd_add_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.id, args.content, args.author)
        author_str = f" by {comment.author}" if comment.author else ""
        print(f"Added comment {comment.id[:8]}{author_str}: {comment.content}")
        return 0

    def _cmd_list_comments(self, args: argparse.Namespace) -> int:
        comments = self._service.get_comments(args.id)
        task = self._service.get_task(args.id)
        print(f"Comments for {task.id[:8]}  {task.title}\n")
        if not comments:
            print("  (no comments)")
            return 0
        for comment in comments:
            author_str = f" — {comment.author}" if comment.author else " — (no author)"
            print(f"  {comment.id[:8]}{author_str}")
            print(f"    {comment.content}")
            print(f"    Created: {comment.created_at.isoformat()}")
            if comment.updated_at:
                print(f"    Updated: {comment.updated_at.isoformat()}")
            print()
        return 0

    def _cmd_delete_comment(self, args: argparse.Namespace) -> int:
        comment = None
        comments = self._service.get_comments(args.task_id)
        for c in comments:
            if c.id == args.comment_id or c.id.startswith(args.comment_id):
                comment = c
                break
        if comment is None:
            raise ValueError(f"Comment '{args.comment_id}' not found")
        self._service.delete_comment(args.task_id, comment.id)
        print(f"Deleted comment {comment.id[:8]}")
        return 0

    def _cmd_edit_comment(self, args: argparse.Namespace) -> int:
        comment = None
        comments = self._service.get_comments(args.task_id)
        for c in comments:
            if c.id == args.comment_id or c.id.startswith(args.comment_id):
                comment = c
                break
        if comment is None:
            raise ValueError(f"Comment '{args.comment_id}' not found")
        updated = self._service.edit_comment(args.task_id, comment.id, args.content)
        print(f"Edited comment {updated.id[:8]}: {updated.content}")
        return 0
