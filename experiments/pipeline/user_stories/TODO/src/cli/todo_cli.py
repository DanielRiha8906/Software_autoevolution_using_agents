import argparse
import sys
import re
from datetime import datetime
from typing import Optional

from ..models.task_status import TaskStatus
from ..models.project import Project
from ..services import TaskNotFoundError, ProjectNotFoundError
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
        except ProjectNotFoundError as e:
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
        p_add.add_argument("--project", help="Project ID to assign task to")
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
            help="Due date before or on (ISO 8601, e.g., 2026-05-15T23:59:59+00:00)",
        )
        p_list.add_argument(
            "--due-after",
            help="Due date on or after (ISO 8601, e.g., 2026-05-01T00:00:00+00:00)",
        )
        p_list.add_argument(
            "--week",
            help="Due in ISO 8601 week (e.g., 2026-W20)",
        )
        p_list.add_argument(
            "--month",
            help="Due in month (e.g., 2026-05)",
        )
        p_list.add_argument(
            "--year",
            help="Due in year (e.g., 2026)",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Show only overdue tasks",
        )
        p_list.add_argument(
            "--project",
            help="Filter by project ID",
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
        p_update.add_argument("--project", help="Project ID to move task to (or none to unassign)")
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

        # report
        p_report = sub.add_parser("report", help="Generate task summary report")
        p_report.set_defaults(func=self._cmd_report)

        # export
        p_export = sub.add_parser("export", help="Export all tasks to JSON file")
        p_export.add_argument("--file", help="Output file path (default: ~/.todo_export.json)")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks from JSON file")
        p_import.add_argument("--file", required=True, help="Input file path (required)")
        p_import.add_argument(
            "--strategy",
            choices=["skip", "replace"],
            default="skip",
            help="Duplicate handling strategy (default: skip)",
        )
        p_import.set_defaults(func=self._cmd_import)

        # create-project
        p_create_project = sub.add_parser("create-project", help="Create a new project")
        p_create_project.add_argument("name", help="Project name")
        p_create_project.set_defaults(func=self._cmd_create_project)

        # list-projects
        p_list_projects = sub.add_parser("list-projects", help="List all projects")
        p_list_projects.set_defaults(func=self._cmd_list_projects)

        # delete-project
        p_delete_project = sub.add_parser("delete-project", help="Delete a project")
        p_delete_project.add_argument("id", help="Project ID")
        p_delete_project.set_defaults(func=self._cmd_delete_project)

        return parser

    def _parse_and_list_by_week(self, week_str: str, status: Optional[TaskStatus]) -> list:
        """Parse YYYY-Www format and return tasks for that week.

        Args:
            week_str: Week string (e.g., "2026-W20").
            status: Optional status filter.

        Returns:
            list[Task]: Tasks due in the specified week.

        Raises:
            ValueError: If format is invalid.
        """
        match = re.match(r'^(\d{4})-W(\d{2})$', week_str)
        if not match:
            raise ValueError(
                f"Invalid week format: {week_str}. Use YYYY-Www (e.g., 2026-W20)"
            )
        year = int(match.group(1))
        week = int(match.group(2))
        try:
            return self._service.list_tasks_by_week(year, week, status)
        except ValueError as e:
            raise ValueError(f"Invalid week: {e}")

    def _parse_and_list_by_month(self, month_str: str, status: Optional[TaskStatus]) -> list:
        """Parse YYYY-MM format and return tasks for that month.

        Args:
            month_str: Month string (e.g., "2026-05").
            status: Optional status filter.

        Returns:
            list[Task]: Tasks due in the specified month.

        Raises:
            ValueError: If format is invalid.
        """
        match = re.match(r'^(\d{4})-(\d{2})$', month_str)
        if not match:
            raise ValueError(
                f"Invalid month format: {month_str}. Use YYYY-MM (e.g., 2026-05)"
            )
        year = int(match.group(1))
        month = int(match.group(2))
        try:
            return self._service.list_tasks_by_month(year, month, status)
        except ValueError as e:
            raise ValueError(f"Invalid month: {e}")

    def _parse_and_list_by_year(self, year_str: str, status: Optional[TaskStatus]) -> list:
        """Parse YYYY format and return tasks for that year.

        Args:
            year_str: Year string (e.g., "2026").
            status: Optional status filter.

        Returns:
            list[Task]: Tasks due in the specified year.

        Raises:
            ValueError: If format is invalid.
        """
        match = re.match(r'^(\d{4})$', year_str)
        if not match:
            raise ValueError(
                f"Invalid year format: {year_str}. Use YYYY (e.g., 2026)"
            )
        year = int(match.group(1))
        return self._service.list_tasks_by_year(year, status)

    def _cmd_add(self, args: argparse.Namespace) -> int:
        due_date = None
        if args.due_date:
            try:
                due_date = datetime.fromisoformat(args.due_date)
            except ValueError:
                raise ValueError(f"Invalid date format: {args.due_date}. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)")
        task = self._service.add_task(args.title, args.description, due_date)

        # Assign to project if specified
        if getattr(args, "project", None):
            project = self._service.get_project(args.project)  # Resolve prefix to full ID
            task = self._service.move_task_to_project(task.id, project.id)
            print(f"Added task {task.id[:8]}  {task.title} to project {project.id[:8]}")
        else:
            print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        before = None
        after = None
        overdue_only = getattr(args, "overdue", False)

        # Parse date range arguments
        due_before = getattr(args, "due_before", None)
        if due_before:
            try:
                before = datetime.fromisoformat(due_before)
            except ValueError:
                raise ValueError(
                    f"Invalid --due-before format: {due_before}. Use ISO 8601 (e.g., 2026-05-15T23:59:59+00:00)"
                )

        due_after = getattr(args, "due_after", None)
        if due_after:
            try:
                after = datetime.fromisoformat(due_after)
            except ValueError:
                raise ValueError(
                    f"Invalid --due-after format: {due_after}. Use ISO 8601 (e.g., 2026-05-01T00:00:00+00:00)"
                )

        # Handle period filters (week/month/year)
        week = getattr(args, "week", None)
        month = getattr(args, "month", None)
        year_arg = getattr(args, "year", None)
        project_id_arg = getattr(args, "project", None)

        # Handle project filter
        if project_id_arg:
            project = self._service.get_project(project_id_arg)  # Resolve prefix to full ID
            tasks = self._service.list_tasks_by_project(project.id)
        elif week:
            tasks = self._parse_and_list_by_week(week, status)
        elif month:
            tasks = self._parse_and_list_by_month(month, status)
        elif year_arg:
            tasks = self._parse_and_list_by_year(year_arg, status)
        else:
            tasks = self._service.list_tasks(status=status, before=before, after=after, overdue_only=overdue_only)

        if not tasks:
            print("No tasks found.")
            return 0
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            due_str = ""
            if task.due_date:
                due_str = f"  (due: {task.due_date.isoformat()})"
            proj_str = f"  [project: {task.project_id[:8]}]" if task.project_id else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}{due_str}{proj_str}")
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

        # Handle project assignment if specified
        if getattr(args, "project", None) is not None:
            project_id_arg = args.project if args.project else None
            if project_id_arg:
                project = self._service.get_project(project_id_arg)  # Resolve prefix to full ID
                task = self._service.move_task_to_project(task.id, project.id)
                print(f"Updated {task.id[:8]}  {task.title} assigned to project {project.id[:8]}")
            else:
                task = self._service.move_task_to_project(task.id, None)
                print(f"Updated {task.id[:8]}  {task.title} (unassigned from project)")
        else:
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

    def _cmd_create_project(self, args: argparse.Namespace) -> int:
        project = self._service.create_project(args.name)
        print(f"Created project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_list_projects(self, args: argparse.Namespace) -> int:
        projects = self._service.list_projects()
        if not projects:
            print("No projects found.")
            return 0
        for project in projects:
            tasks = self._service.list_tasks_by_project(project.id)
            task_count = len(tasks)
            print(f"{project.id[:8]}  {project.name}  ({task_count} task{'s' if task_count != 1 else ''})")
        return 0

    def _cmd_delete_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        self._service.delete_project(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_report(self, args: argparse.Namespace) -> int:
        report = self._service.generate_report()
        print("Task Summary Report")
        print()
        print(f"Total tasks:       {report.total_count}")
        print(f"  Pending:        {report.pending_count}")
        print(f"  In progress:    {report.in_progress_count}")
        print(f"  Done:           {report.done_count}")
        print()
        print(f"With due date:     {report.due_date_set_count}")
        print(f"Overdue:           {report.overdue_count}")
        print()
        completion_pct = report.completion_rate * 100
        print(f"Completion rate:   {completion_pct:.1f}%")
        if report.avg_days_to_completion is not None:
            print(f"Avg days to completion: {report.avg_days_to_completion:.1f}")
        else:
            print("Avg days to completion: N/A")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        file_path = getattr(args, "file", None)
        try:
            count = self._service.export_tasks(file_path)
            output_path = file_path or (
                str(__import__("pathlib").Path.home() / ".todo_export.json")
            )
            print(f"Exported {count} task(s) to {output_path}")
            return 0
        except OSError as e:
            print(f"Error: Failed to export tasks: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        file_path = args.file
        strategy = getattr(args, "strategy", "skip")
        try:
            result = self._service.import_tasks(file_path, strategy)
            print(f"Import complete:")
            print(f"  Imported: {result['imported_count']}")
            print(f"  Skipped:  {result['skipped_count']}")
            if result["errors"]:
                print(f"  Errors:   {len(result['errors'])}")
                for error in result["errors"][:5]:  # Show first 5 errors
                    if "error" in error:
                        print(f"    - {error['error']}")
                if len(result["errors"]) > 5:
                    print(f"    ... and {len(result['errors']) - 5} more error(s)")
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"Error: Failed to read file: {e}", file=sys.stderr)
            return 1
