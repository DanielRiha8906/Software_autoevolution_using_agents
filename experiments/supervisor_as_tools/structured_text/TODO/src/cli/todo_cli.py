import argparse
import sys
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from ..models.task_status import TaskStatus
from ..services.comments_service import CommentNotFoundError
from ..services.project_manager import ProjectNotFoundError
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..storage.json_storage import JsonStorage

_STATUS_SYMBOLS = {
    TaskStatus.PENDING: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
}


def _parse_cest_datetime(date_str: str) -> Optional[datetime]:
    """Parse CEST datetime string in format 'YYYY-MM-DD HH:MM' to UTC datetime.

    Args:
        date_str: Datetime string in format "YYYY-MM-DD HH:MM", assumed to be CEST.

    Returns:
        datetime object in UTC, or None if parsing fails.
    """
    try:
        cest = ZoneInfo("Europe/Paris")
        dt_cest = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
        return dt_cest.astimezone(timezone.utc)
    except ValueError:
        return None


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
        except (TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError) as e:
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
        p_add.add_argument("--project", help="Optional project ID")
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
            help="Filter tasks with due date on or before this date (format: YYYY-MM-DD HH:MM, CEST)",
        )
        p_list.add_argument(
            "--due-after",
            help="Filter tasks with due date on or after this date (format: YYYY-MM-DD HH:MM, CEST)",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Show only overdue tasks",
        )
        p_list.add_argument(
            "--project",
            help="Filter tasks by project ID",
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

        # due-date
        p_due = sub.add_parser("due-date", help="Set or clear task due date")
        p_due.add_argument("id", help="Task ID")
        p_due.add_argument("--clear", action="store_true", help="Clear the due date")
        p_due.add_argument("--date", help="Due date in format YYYY-MM-DD HH:MM (CEST)")
        p_due.set_defaults(func=self._cmd_due_date)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # comment-add
        p_comment_add = sub.add_parser("comment-add", help="Add a comment to a task")
        p_comment_add.add_argument("task_id", help="Task ID")
        p_comment_add.add_argument("content", help="Comment content")
        p_comment_add.set_defaults(func=self._cmd_comment_add)

        # comment-list
        p_comment_list = sub.add_parser("comment-list", help="List comments for a task")
        p_comment_list.add_argument("task_id", help="Task ID")
        p_comment_list.set_defaults(func=self._cmd_comment_list)

        # comment-delete
        p_comment_delete = sub.add_parser("comment-delete", help="Delete a comment")
        p_comment_delete.add_argument("comment_id", help="Comment ID")
        p_comment_delete.set_defaults(func=self._cmd_comment_delete)

        # stats
        p_stats = sub.add_parser("stats", help="Show task statistics")
        p_stats.set_defaults(func=self._cmd_stats)

        # export
        p_export = sub.add_parser("export", help="Export all tasks and comments to JSON")
        p_export.add_argument("filepath", help="Path to export file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON")
        p_import.add_argument("filepath", help="Path to import file")
        p_import.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing data (default: error if data exists)",
        )
        p_import.set_defaults(func=self._cmd_import)

        # project-add
        p_project_add = sub.add_parser("project-add", help="Add a new project")
        p_project_add.add_argument("name", help="Project name")
        p_project_add.set_defaults(func=self._cmd_project_add)

        # project-list
        p_project_list = sub.add_parser("project-list", help="List all projects")
        p_project_list.set_defaults(func=self._cmd_project_list)

        # project-delete
        p_project_delete = sub.add_parser("project-delete", help="Delete a project")
        p_project_delete.add_argument("id", help="Project ID")
        p_project_delete.set_defaults(func=self._cmd_project_delete)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        project_id = getattr(args, "project", None)
        task = self._service.add_task(args.title, args.description, project_id)
        project_info = f" to project {project_id[:8]}" if project_id else ""
        print(f"Added task {task.id[:8]}  {task.title}{project_info}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        overdue = getattr(args, "overdue", False)
        project_id = getattr(args, "project", None)

        # Parse due_before and due_after
        due_before = None
        due_after = None

        if getattr(args, "due_before", None):
            due_before = _parse_cest_datetime(args.due_before)
            if due_before is None:
                print(f"Error: Invalid date format for --due-before: {args.due_before}", file=sys.stderr)
                return 1

        if getattr(args, "due_after", None):
            due_after = _parse_cest_datetime(args.due_after)
            if due_after is None:
                print(f"Error: Invalid date format for --due-after: {args.due_after}", file=sys.stderr)
                return 1

        tasks = self._service.list_tasks(
            status=status,
            due_before=due_before,
            due_after=due_after,
            overdue=overdue,
            project_id=project_id,
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
            cest = ZoneInfo("Europe/Paris")
            due_cest = task.due_date.astimezone(cest)
            overdue_marker = " [OVERDUE]" if task.is_overdue() else ""
            print(f"Due:         {due_cest.strftime('%Y-%m-%d %H:%M CEST')}{overdue_marker}")
        else:
            print(f"Due:         (none)")
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

    def _cmd_due_date(self, args: argparse.Namespace) -> int:
        if args.clear:
            task = self._service.set_due_date(args.id, None)
            print(f"Cleared due date for {task.id[:8]}  {task.title}")
        elif args.date:
            # Parse input in CEST and convert to UTC
            cest = ZoneInfo("Europe/Paris")
            due_cest = datetime.strptime(args.date, "%Y-%m-%d %H:%M").replace(tzinfo=cest)
            due_utc = due_cest.astimezone(timezone.utc)
            task = self._service.set_due_date(args.id, due_utc)
            print(f"Set due date for {task.id[:8]}  {task.title}")
        else:
            print("Error: --date YYYY-MM-DD HH:MM or --clear required", file=sys.stderr)
            return 1
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_comment_add(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.task_id, args.content)
        print(f"Added comment {comment.id[:8]} to task {args.task_id[:8]}")
        return 0

    def _cmd_comment_list(self, args: argparse.Namespace) -> int:
        comments = self._service.list_comments(args.task_id)
        if not comments:
            print(f"No comments for task {args.task_id[:8]}")
            return 0
        for comment in comments:
            print(f"[{comment.id[:8]}] {comment.created_at.isoformat()} — {comment.content}")
        return 0

    def _cmd_comment_delete(self, args: argparse.Namespace) -> int:
        self._service.delete_comment(args.comment_id)
        print(f"Deleted comment {args.comment_id[:8]}")
        return 0

    def _cmd_stats(self, args: argparse.Namespace) -> int:
        stats = self._service.get_statistics()
        avg_days_str = f"{stats.avg_days_to_completion:.1f}" if stats.avg_days_to_completion is not None else "—"
        print("Task Statistics")
        print("===============================")
        print(f"Total tasks:            {stats.total_count}")
        print(f"  Pending:              {stats.pending_count}")
        print(f"  In Progress:          {stats.in_progress_count}")
        print(f"  Done:                 {stats.done_count}")
        print(f"Completion Rate:        {stats.completion_rate:.1f}%")
        print(f"Overdue:                {stats.overdue_count}")
        print(f"With due date:          {stats.tasks_with_due_date}")
        print(f"Avg days to completion: {avg_days_str}")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        try:
            task_count, comment_count = self._service.export_tasks(args.filepath)
            print(f"Exported {task_count} task(s) and {comment_count} comment(s) to {args.filepath}")
            return 0
        except (ValueError, OSError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            task_count, comment_count, _ = self._service.import_tasks(args.filepath, args.overwrite)
            print(f"Imported {task_count} task(s) and {comment_count} comment(s) from {args.filepath}")
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_project_add(self, args: argparse.Namespace) -> int:
        project = self._service.add_project(args.name)
        print(f"Added project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_list(self, args: argparse.Namespace) -> int:
        projects = self._service.list_projects()
        if not projects:
            print("No projects found.")
            return 0
        for project in projects:
            print(f"{project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_delete(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        self._service.delete_project(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0
