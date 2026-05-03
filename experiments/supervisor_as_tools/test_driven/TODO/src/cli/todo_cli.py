import argparse
import sys
from typing import Optional
from datetime import datetime

from ..models.task_status import TaskStatus
from ..models.task import CEST
from ..models.task_statistics import TaskStatistics
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..services.statistics_service import TaskStatisticsService
from ..services.comments_service import CommentsService
from ..services.import_export_service import TaskImportExportService
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
        self._comments_service = CommentsService(self._service)
        self._import_export = TaskImportExportService(self._service, self._comments_service)

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
            help="Filter to show only overdue tasks",
        )
        p_list.add_argument(
            "--due-before",
            type=str,
            help="List tasks due before this date (ISO 8601 format with CEST timezone, e.g., 2025-12-31T23:59:59+02:00)",
        )
        p_list.add_argument(
            "--due-after",
            type=str,
            help="List tasks due after this date (ISO 8601 format with CEST timezone, e.g., 2025-01-01T00:00:00+02:00)",
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
        p_update.set_defaults(func=self._cmd_update)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # stats
        p_stats = sub.add_parser("stats", help="View task statistics")
        p_stats.set_defaults(func=self._cmd_stats)

        # export
        p_export = sub.add_parser("export", help="Export tasks and comments to JSON")
        p_export.add_argument("filepath", help="Path to export file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON")
        p_import.add_argument("filepath", help="Path to import file")
        p_import.set_defaults(func=self._cmd_import)

        return parser

    def _parse_datetime_cest(self, date_str: str) -> datetime:
        """Parse ISO 8601 string to CEST datetime, with validation."""
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 format: {date_str}") from e

        # Validate CEST
        if dt.tzinfo is None:
            raise ValueError(f"Datetime must include timezone: {date_str}")
        if dt.tzinfo != CEST:
            raise ValueError(f"Timezone must be CEST (UTC+2), got {dt.tzinfo}")
        return dt

    def _cmd_add(self, args: argparse.Namespace) -> int:
        task = self._service.add_task(args.title, args.description)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = None
        if args.status:
            status = TaskStatus(args.status)

        overdue = args.overdue if args.overdue else None

        due_before = None
        if args.due_before:
            due_before = self._parse_datetime_cest(args.due_before)

        due_after = None
        if args.due_after:
            due_after = self._parse_datetime_cest(args.due_after)

        tasks = self._service.list_tasks(
            status=status,
            overdue=overdue,
            due_before=due_before,
            due_after=due_after
        )

        # Format and print output
        if tasks:
            for task in tasks:
                sym = _STATUS_SYMBOLS[task.status]
                desc = f"  {task.description}" if task.description else ""
                due_str = f"  Due: {task.due_date.isoformat()}" if task.due_date else ""
                print(f"{sym} {task.id[:8]}  {task.title}{desc}{due_str}")
        else:
            print("No tasks found.")

        return 0

    def _cmd_show(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        print(f"ID:          {task.id}")
        print(f"Title:       {task.title}")
        print(f"Description: {task.description or '—'}")
        print(f"Status:      {task.status.value}")
        print(f"Created:     {task.created_at.isoformat()}")
        print(f"Updated:     {task.updated_at.isoformat()}")
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
        task = self._service.update_task(args.id, title=args.title, description=args.description)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_stats(self, args: argparse.Namespace) -> int:
        stats_service = TaskStatisticsService(self._service)
        report = stats_service.compute()
        self._print_statistics_report(report)
        return 0

    def _print_statistics_report(self, report: TaskStatistics) -> None:
        """Print formatted statistics report."""
        print("Task Statistics")
        print("=" * 40)
        print(f"Total tasks:           {report.total}")
        print(f"Pending:               {report.count_per_status[TaskStatus.PENDING]}")
        print(f"In progress:           {report.count_per_status[TaskStatus.IN_PROGRESS]}")
        print(f"Done:                  {report.count_per_status[TaskStatus.DONE]}")
        print(f"Overdue:               {report.overdue_count}")
        print(f"With due date:         {report.with_due_date_count}")
        print(f"Completion rate:       {report.completion_rate:.1f}%")

    def _cmd_export(self, args: argparse.Namespace) -> int:
        try:
            self._import_export.export(args.filepath)
            print(f"Exported to {args.filepath}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            imported_tasks, imported_comments = self._import_export.import_from(args.filepath)
            print(f"Imported {len(imported_tasks)} tasks and {len(imported_comments)} comments")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
