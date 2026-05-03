import argparse
import sys
from datetime import datetime
from typing import Optional

from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.comments_service import CommentNotFoundError
from ..services.todo_service import TodoService
from ..services.statistics_service import StatisticsService
from ..services.import_export_service import ImportExportService, ImportExportValidationError
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
        self._stats_service = StatisticsService(storage)
        self._import_export_service = ImportExportService(storage)

    def run(self, argv: Optional[list[str]] = None) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)
        if not hasattr(args, "func"):
            parser.print_help()
            return 0
        try:
            return args.func(args)
        except (TaskNotFoundError, CommentNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except (ValueError, ImportExportValidationError) as e:
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
        p_add.add_argument("--due-date", help="Due date in ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)")
        p_add.set_defaults(func=self._cmd_add)

        # list
        p_list = sub.add_parser("list", help="List tasks")
        p_list.add_argument(
            "--status",
            choices=["pending", "in_progress", "done"],
            help="Filter by status",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Show only overdue tasks",
        )
        p_list.add_argument(
            "--due-before",
            help="Show tasks due before this datetime (ISO 8601 format)",
        )
        p_list.add_argument(
            "--due-after",
            help="Show tasks due after this datetime (ISO 8601 format)",
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
        p_update.add_argument("--due-date", help="Due date in ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)")
        p_update.set_defaults(func=self._cmd_update)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # comment add
        p_comment_add = sub.add_parser("comment-add", help="Add a comment to a task")
        p_comment_add.add_argument("task_id", help="Task ID")
        p_comment_add.add_argument("content", help="Comment content")
        p_comment_add.add_argument("-a", "--author", help="Optional author name")
        p_comment_add.set_defaults(func=self._cmd_comment_add)

        # comment list
        p_comment_list = sub.add_parser("comment-list", help="List comments for a task")
        p_comment_list.add_argument("task_id", help="Task ID")
        p_comment_list.set_defaults(func=self._cmd_comment_list)

        # comment delete
        p_comment_delete = sub.add_parser("comment-delete", help="Delete a comment")
        p_comment_delete.add_argument("comment_id", help="Comment ID")
        p_comment_delete.set_defaults(func=self._cmd_comment_delete)

        # comment update
        p_comment_update = sub.add_parser("comment-update", help="Update a comment")
        p_comment_update.add_argument("comment_id", help="Comment ID")
        p_comment_update.add_argument("content", help="New comment content")
        p_comment_update.set_defaults(func=self._cmd_comment_update)

        # stats
        p_stats = sub.add_parser("stats", help="View task statistics")
        p_stats.set_defaults(func=self._cmd_stats)

        # export
        p_export = sub.add_parser("export", help="Export all tasks and comments to a JSON file")
        p_export.add_argument("filepath", help="Path to the output JSON file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from a JSON file")
        p_import.add_argument("filepath", help="Path to the input JSON file")
        p_import.add_argument("--overwrite", action="store_true", help="Overwrite existing tasks/comments with same IDs")
        p_import.set_defaults(func=self._cmd_import)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        due_date = None
        if args.due_date:
            try:
                due_date = datetime.fromisoformat(args.due_date)
            except ValueError as e:
                print(f"Error: Invalid due date format. Use ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)", file=sys.stderr)
                return 1
        task = self._service.add_task(args.title, args.description, due_date)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        due_before = None
        due_after = None

        if args.due_before:
            try:
                due_before = datetime.fromisoformat(args.due_before)
            except ValueError:
                print(f"Error: Invalid due-before format. Use ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)", file=sys.stderr)
                return 1

        if args.due_after:
            try:
                due_after = datetime.fromisoformat(args.due_after)
            except ValueError:
                print(f"Error: Invalid due-after format. Use ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)", file=sys.stderr)
                return 1

        tasks = self._service.list_tasks(
            status=status,
            overdue=args.overdue,
            due_before=due_before,
            due_after=due_after,
        )
        if not tasks:
            print("No tasks found.")
            return 0
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            overdue_str = " (OVERDUE)" if task.is_overdue() else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}{overdue_str}")
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
            overdue_str = " (OVERDUE)" if task.is_overdue() else ""
            print(f"Due date:    {task.due_date.isoformat()}{overdue_str}")
        else:
            print(f"Due date:    —")
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
            except ValueError as e:
                print(f"Error: Invalid due date format. Use ISO 8601 format (e.g., 2024-12-31T15:00:00+02:00)", file=sys.stderr)
                return 1
        task = self._service.update_task(args.id, title=args.title, description=args.description, due_date=due_date)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_comment_add(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.task_id, args.content, args.author)
        print(f"Added comment {comment.id[:8]} to task {comment.task_id[:8]}")
        return 0

    def _cmd_comment_list(self, args: argparse.Namespace) -> int:
        comments = self._service.list_comments(args.task_id)
        if not comments:
            print(f"No comments for task {args.task_id[:8]}")
            return 0
        for comment in comments:
            author_str = f" by {comment.author}" if comment.author else ""
            created_str = comment.created_at.isoformat()
            print(f"{comment.id[:8]}{author_str} at {created_str}")
            print(f"  {comment.content}")
        return 0

    def _cmd_comment_delete(self, args: argparse.Namespace) -> int:
        comment = self._service.get_comment(args.comment_id)
        self._service.delete_comment(args.comment_id)
        print(f"Deleted comment {comment.id[:8]}")
        return 0

    def _cmd_comment_update(self, args: argparse.Namespace) -> int:
        updated = self._service.update_comment(args.comment_id, args.content)
        print(f"Updated comment {updated.id[:8]}")
        return 0

    def _cmd_stats(self, args: argparse.Namespace) -> int:
        stats = self._stats_service.compute_statistics()
        print("\nTask Statistics")
        print("=" * 40)
        print(f"Total tasks:              {stats.total_task_count}")
        print(f"Pending:                  {stats.pending_count}")
        print(f"In progress:              {stats.in_progress_count}")
        print(f"Done:                     {stats.done_count}")
        print(f"Overdue:                  {stats.overdue_count}")
        print(f"With due date:            {stats.tasks_with_due_date_count}")
        print(f"Completion rate:          {stats.completion_rate:.1%}")
        print("=" * 40)
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        try:
            export_data = self._import_export_service.export_to_file(args.filepath)
            num_tasks = len(export_data.get("tasks", []))
            num_comments = len(export_data.get("comments", []))
            print(f"Exported {num_tasks} task(s) and {num_comments} comment(s) to {args.filepath}")
            return 0
        except IOError as e:
            print(f"Error: Failed to export: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            result = self._import_export_service.import_from_file(args.filepath, overwrite=args.overwrite)
            added_tasks = len(result["added_tasks"])
            skipped_tasks = len(result["skipped_tasks"])
            added_comments = len(result["added_comments"])
            skipped_comments = len(result["skipped_comments"])
            print(f"Import complete: {added_tasks} task(s), {added_comments} comment(s) added")
            if skipped_tasks or skipped_comments:
                print(f"  ({skipped_tasks} task(s), {skipped_comments} comment(s) skipped - duplicates/invalid)")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ImportExportValidationError as e:
            print(f"Error: Invalid import file: {e}", file=sys.stderr)
            return 1
        except IOError as e:
            print(f"Error: Failed to import: {e}", file=sys.stderr)
            return 1
