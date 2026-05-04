import argparse
import sys
from datetime import datetime
from typing import Optional

from ..models.task_status import TaskStatus
from ..formatters.task_formatter import TaskFormatter
from ..services.task_manager import TaskNotFoundError
from ..services.project_service import ProjectService, ProjectNotFoundError
from ..services.task_statistics_service import TaskStatisticsService
from ..services.todo_service import TodoService
from ..services.comments_service import CommentsService
from ..services.task_import_export_service import TaskImportExportService
from ..storage.json_storage import JsonStorage


class TodoCLI:
    def __init__(self, storage_path: Optional[str] = None) -> None:
        storage = JsonStorage(storage_path) if storage_path else JsonStorage()
        self._service = TodoService(storage)
        self._project_service = ProjectService(storage)
        self._comments_service = CommentsService(self._service, storage)
        self._import_export_service = TaskImportExportService(self._service, self._comments_service)

    def run(self, argv: Optional[list[str]] = None) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)
        if not hasattr(args, "func"):
            parser.print_help()
            return 0
        try:
            return args.func(args)
        except (TaskNotFoundError, ProjectNotFoundError) as e:
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
        p_add.add_argument("-p", "--project", help="Project ID (optional)")
        p_add.set_defaults(func=self._cmd_add)

        # list
        p_list = sub.add_parser("list", help="List tasks")
        p_list.add_argument(
            "--status",
            choices=["pending", "in_progress", "done"],
            help="Filter by status",
        )
        p_list.add_argument("--due-before", help="Filter tasks with due_date before cutoff (ISO format, CEST timezone)")
        p_list.add_argument("--due-after", help="Filter tasks with due_date after cutoff (ISO format, CEST timezone)")
        p_list.add_argument("--overdue", action="store_true", help="Filter only overdue tasks")
        p_list.add_argument("-p", "--project", help="Filter by project ID")
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
        p_update.add_argument("-p", "--project", help="New project ID")
        p_update.set_defaults(func=self._cmd_update)

        # delete
        p_delete = sub.add_parser("delete", help="Delete a task")
        p_delete.add_argument("id", help="Task ID")
        p_delete.set_defaults(func=self._cmd_delete)

        # statistics
        p_stats = sub.add_parser("statistics", help="Show task statistics")
        p_stats.set_defaults(func=self._cmd_statistics)

        # export
        p_export = sub.add_parser("export", help="Export tasks and comments to JSON file")
        p_export.add_argument("filepath", help="Path to export file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON file")
        p_import.add_argument("filepath", help="Path to import file")
        p_import.set_defaults(func=self._cmd_import)

        # project subcommands
        p_project = sub.add_parser("project", help="Manage projects")
        project_subs = p_project.add_subparsers(title="project commands")

        p_proj_create = project_subs.add_parser("create", help="Create a new project")
        p_proj_create.add_argument("name", help="Project name")
        p_proj_create.add_argument("--description", help="Project description (optional)")
        p_proj_create.set_defaults(func=self._cmd_project_create)

        p_proj_list = project_subs.add_parser("list", help="List all projects")
        p_proj_list.set_defaults(func=self._cmd_project_list)

        p_proj_show = project_subs.add_parser("show", help="Show project details")
        p_proj_show.add_argument("id", help="Project ID")
        p_proj_show.set_defaults(func=self._cmd_project_show)

        p_proj_delete = project_subs.add_parser("delete", help="Delete a project")
        p_proj_delete.add_argument("id", help="Project ID")
        p_proj_delete.set_defaults(func=self._cmd_project_delete)

        p_proj_update = project_subs.add_parser("update", help="Update a project")
        p_proj_update.add_argument("id", help="Project ID")
        p_proj_update.add_argument("--name", help="New project name")
        p_proj_update.add_argument("--description", help="New project description")
        p_proj_update.set_defaults(func=self._cmd_project_update)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        task = self._service.add_task(args.title, args.description, project_id=args.project)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        due_before = None
        due_after = None

        if args.due_before:
            try:
                due_before = datetime.fromisoformat(args.due_before)
            except ValueError as e:
                print(f"Error parsing --due-before: {e}", file=sys.stderr)
                return 1

        if args.due_after:
            try:
                due_after = datetime.fromisoformat(args.due_after)
            except ValueError as e:
                print(f"Error parsing --due-after: {e}", file=sys.stderr)
                return 1

        try:
            tasks = self._service.list_tasks(
                status=status,
                due_before=due_before,
                due_after=due_after,
                overdue=args.overdue,
                project_id=args.project,
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        if not tasks:
            print("No tasks found.")
            return 0
        for task in tasks:
            sym = TaskFormatter.get_status_symbol(task.status)
            desc = f"  {task.description}" if task.description else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}")
        return 0

    def _cmd_show(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        print(f"ID:          {task.id}")
        print(f"Title:       {task.title}")
        print(f"Description: {task.description or '—'}")
        print(f"Status:      {task.status.value}")
        print(f"Project ID:  {task.project_id or '—'}")
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
        task = self._service.update_task(args.id, title=args.title, description=args.description, project_id=args.project)
        print(f"Updated {task.id[:8]}  {task.title}")
        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        self._service.delete_task(args.id)
        print(f"Deleted {task.id[:8]}  {task.title}")
        return 0

    def _cmd_statistics(self, args: argparse.Namespace) -> int:
        stats_service = TaskStatisticsService(self._service)
        stats = stats_service.compute()

        print("\nTask Statistics")
        print("=" * 40)
        print(f"Total tasks:       {stats.total}")
        print(f"Pending:           {stats.count_per_status.get(TaskStatus.PENDING, 0)}")
        print(f"In Progress:       {stats.count_per_status.get(TaskStatus.IN_PROGRESS, 0)}")
        print(f"Done:              {stats.count_per_status.get(TaskStatus.DONE, 0)}")
        print(f"With due date:     {stats.with_due_date_count}")
        print(f"Overdue:           {stats.overdue_count}")
        print(f"Completion rate:   {stats.completion_rate:.1f}%")
        print("=" * 40 + "\n")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        try:
            self._import_export_service.export(args.filepath)
            print(f"Exported to {args.filepath}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            imported_tasks, imported_comments = self._import_export_service.import_from(args.filepath)
            print(f"Imported {len(imported_tasks)} task(s) and {len(imported_comments)} comment(s)")
            return 0
        except FileNotFoundError:
            print(f"Error: File not found: {args.filepath}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _cmd_project_create(self, args: argparse.Namespace) -> int:
        project = self._project_service.create(args.name, description=args.description)
        print(f"Created project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_list(self, args: argparse.Namespace) -> int:
        projects = self._project_service.list_all()
        if not projects:
            print("No projects found.")
            return 0
        for project in projects:
            desc = f"  {project.description}" if project.description else ""
            print(f"  {project.id[:8]}  {project.name}{desc}")
        return 0

    def _cmd_project_show(self, args: argparse.Namespace) -> int:
        project = self._project_service.get(args.id)
        print(f"ID:          {project.id}")
        print(f"Name:        {project.name}")
        print(f"Description: {project.description or '—'}")
        print(f"Created:     {project.created_at.isoformat()}")
        return 0

    def _cmd_project_delete(self, args: argparse.Namespace) -> int:
        project = self._project_service.get(args.id)
        self._project_service.delete(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_update(self, args: argparse.Namespace) -> int:
        project = self._project_service.update(args.id, name=args.name, description=args.description)
        print(f"Updated project {project.id[:8]}  {project.name}")
        return 0
