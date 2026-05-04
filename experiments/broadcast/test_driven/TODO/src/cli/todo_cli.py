import argparse
import json
import sys
from typing import Optional
from datetime import datetime, timezone, timedelta

from ..models.task import CEST
from ..models.task_status import TaskStatus
from ..services.task_manager import TaskNotFoundError
from ..services.todo_service import TodoService
from ..services.project_service import ProjectService
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
        self._project_service = ProjectService(self._service)
        self._comments_service = CommentsService()
        self._import_export_service = TaskImportExportService(self._service, self._comments_service)

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
        except json.JSONDecodeError as e:
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
            help="Show only overdue tasks",
        )
        p_list.add_argument(
            "--due-before",
            type=str,
            help="Show tasks due before a date (ISO format, CEST timezone)",
        )
        p_list.add_argument(
            "--due-after",
            type=str,
            help="Show tasks due after a date (ISO format, CEST timezone)",
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

        # statistics
        p_stats = sub.add_parser("statistics", help="View task statistics")
        p_stats.set_defaults(func=self._cmd_statistics)

        # export
        p_export = sub.add_parser("export", help="Export tasks and comments to JSON")
        p_export.add_argument("path", help="Output file path")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON")
        p_import.add_argument("path", help="Input file path")
        p_import.set_defaults(func=self._cmd_import)

        # project create
        p_project_create = sub.add_parser("project-create", help="Create a new project")
        p_project_create.add_argument("name", help="Project name")
        p_project_create.set_defaults(func=self._cmd_project_create)

        # project list
        p_project_list = sub.add_parser("project-list", help="List all projects")
        p_project_list.set_defaults(func=self._cmd_project_list)

        # add with project
        p_add.add_argument("-p", "--project", help="Project ID to assign task to")

        # list with project filter
        p_list.add_argument("--project", help="Filter tasks by project ID")

        # update with project
        p_update.add_argument("-p", "--project", help="Assign task to a project")

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        project_id = getattr(args, "project", None)
        task = self._service.add_task(args.title, args.description, project_id=project_id)
        project_info = f" to project {project_id[:8]}" if project_id else ""
        print(f"Added task {task.id[:8]}  {task.title}{project_info}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None

        # Parse due_before if provided
        due_before = None
        if args.due_before:
            try:
                due_before = datetime.fromisoformat(args.due_before)
                if due_before.tzinfo is None or due_before.tzinfo != CEST:
                    print("Error: due_before must be in CEST timezone (UTC+2)", file=sys.stderr)
                    return 1
            except ValueError:
                print("Error: due_before must be in ISO format", file=sys.stderr)
                return 1

        # Parse due_after if provided
        due_after = None
        if args.due_after:
            try:
                due_after = datetime.fromisoformat(args.due_after)
                if due_after.tzinfo is None or due_after.tzinfo != CEST:
                    print("Error: due_after must be in CEST timezone (UTC+2)", file=sys.stderr)
                    return 1
            except ValueError:
                print("Error: due_after must be in ISO format", file=sys.stderr)
                return 1

        project_id = getattr(args, "project", None)
        try:
            tasks = self._service.list_tasks(
                status=status,
                overdue=args.overdue,
                due_before=due_before,
                due_after=due_after,
                project_id=project_id,
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

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
        project_id = getattr(args, "project", None)
        task = self._service.update_task(args.id, title=args.title, description=args.description, project_id=project_id)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_statistics(self, args: argparse.Namespace) -> int:
        stats_svc = TaskStatisticsService(self._service)
        report = stats_svc.compute()
        print(f"Total tasks:           {report.total}")
        print(f"Pending:               {report.count_per_status[TaskStatus.PENDING]}")
        print(f"In Progress:           {report.count_per_status[TaskStatus.IN_PROGRESS]}")
        print(f"Done:                  {report.count_per_status[TaskStatus.DONE]}")
        print(f"Completion rate:       {report.completion_rate:.1f}%")
        print(f"Tasks with due date:   {report.with_due_date_count}")
        print(f"Overdue tasks:         {report.overdue_count}")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        try:
            self._import_export_service.export(args.path)
            print(f"Exported tasks and comments to {args.path}")
            return 0
        except IOError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            self._import_export_service.import_from(args.path)
            print(f"Imported tasks and comments from {args.path}")
            return 0
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_project_create(self, args: argparse.Namespace) -> int:
        try:
            project = self._project_service.create(args.name)
            print(f"Created project {project.id[:8]}  {project.name}")
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_project_list(self, args: argparse.Namespace) -> int:
        projects = self._project_service.list()
        if not projects:
            print("No projects found.")
            return 0
        for project in projects:
            print(f"{project.id[:8]}  {project.name}")
        return 0
