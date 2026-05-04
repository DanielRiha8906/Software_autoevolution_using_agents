import argparse
import sys
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ..models.task_status import TaskStatus
from ..services.comments_service import CommentNotFoundError
from ..services.import_export_service import ImportExportService
from ..services.project_manager import ProjectNotFoundError
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
        self._import_export = ImportExportService(self._service._manager, self._service._comments_service)

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
        except (ValueError, FileNotFoundError) as e:
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
            "--due-before",
            help="Filter tasks with due date before this ISO datetime (e.g., 2026-12-31T23:59:59+01:00)",
        )
        p_list.add_argument(
            "--due-after",
            help="Filter tasks with due date after this ISO datetime (e.g., 2026-01-01T00:00:00+01:00)",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Filter to show only overdue tasks",
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

        # is-pending
        p_is_pending = sub.add_parser("is-pending", help="Check if task is pending")
        p_is_pending.add_argument("id", help="Task ID")
        p_is_pending.set_defaults(func=self._cmd_is_pending)

        # is-in-progress
        p_is_in_progress = sub.add_parser("is-in-progress", help="Check if task is in progress")
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
        p_add_comment.add_argument("content", help="Comment content")
        p_add_comment.add_argument("-a", "--author", help="Comment author")
        p_add_comment.set_defaults(func=self._cmd_add_comment)

        # list-comments
        p_list_comments = sub.add_parser("list-comments", help="List comments for a task")
        p_list_comments.add_argument("task_id", help="Task ID")
        p_list_comments.set_defaults(func=self._cmd_list_comments)

        # delete-comment
        p_delete_comment = sub.add_parser("delete-comment", help="Delete a comment")
        p_delete_comment.add_argument("comment_id", help="Comment ID")
        p_delete_comment.set_defaults(func=self._cmd_delete_comment)

        # edit-comment
        p_edit_comment = sub.add_parser("edit-comment", help="Edit a comment")
        p_edit_comment.add_argument("comment_id", help="Comment ID")
        p_edit_comment.add_argument("content", help="New comment content")
        p_edit_comment.set_defaults(func=self._cmd_edit_comment)

        # report
        p_report = sub.add_parser("report", help="Display task summary report")
        p_report.set_defaults(func=self._cmd_report)

        # export
        p_export = sub.add_parser("export", help="Export tasks and comments to JSON file")
        p_export.add_argument("filepath", help="Path to export JSON file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON file")
        p_import.add_argument("filepath", help="Path to import JSON file")
        p_import.add_argument("--merge", action="store_true", default=True, help="Merge with existing data (default)")
        p_import.set_defaults(func=self._cmd_import)

        # project commands
        # create-project
        p_create_project = sub.add_parser("create-project", help="Create a new project")
        p_create_project.add_argument("name", help="Project name")
        p_create_project.set_defaults(func=self._cmd_create_project)

        # list-projects
        p_list_projects = sub.add_parser("list-projects", help="List all projects")
        p_list_projects.set_defaults(func=self._cmd_list_projects)

        # show-project
        p_show_project = sub.add_parser("show-project", help="Show project details")
        p_show_project.add_argument("id", help="Project ID")
        p_show_project.set_defaults(func=self._cmd_show_project)

        # update-project
        p_update_project = sub.add_parser("update-project", help="Update a project's name")
        p_update_project.add_argument("id", help="Project ID")
        p_update_project.add_argument("name", help="New project name")
        p_update_project.set_defaults(func=self._cmd_update_project)

        # delete-project
        p_delete_project = sub.add_parser("delete-project", help="Delete a project")
        p_delete_project.add_argument("id", help="Project ID")
        p_delete_project.set_defaults(func=self._cmd_delete_project)

        # list-tasks-by-project
        p_list_tasks_by_project = sub.add_parser("list-tasks-by-project", help="List tasks in a project")
        p_list_tasks_by_project.add_argument("project_id", help="Project ID")
        p_list_tasks_by_project.set_defaults(func=self._cmd_list_tasks_by_project)

        # assign-task-to-project
        p_assign_task = sub.add_parser("assign-task-to-project", help="Assign a task to a project")
        p_assign_task.add_argument("task_id", help="Task ID")
        p_assign_task.add_argument("project_id", help="Project ID")
        p_assign_task.set_defaults(func=self._cmd_assign_task_to_project)

        # unassign-task-from-project
        p_unassign_task = sub.add_parser("unassign-task-from-project", help="Remove a task from a project")
        p_unassign_task.add_argument("task_id", help="Task ID")
        p_unassign_task.set_defaults(func=self._cmd_unassign_task_from_project)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        task = self._service.add_task(args.title, args.description)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None
        due_before = None
        due_after = None
        overdue = None

        if args.due_before:
            try:
                due_before = datetime.fromisoformat(args.due_before)
            except ValueError:
                print(f"Error: Invalid ISO datetime format for --due-before: {args.due_before}", file=sys.stderr)
                return 1

        if args.due_after:
            try:
                due_after = datetime.fromisoformat(args.due_after)
            except ValueError:
                print(f"Error: Invalid ISO datetime format for --due-after: {args.due_after}", file=sys.stderr)
                return 1

        if args.overdue:
            overdue = True

        tasks = self._service.list_tasks(status=status, due_before=due_before, due_after=due_after, overdue=overdue)
        if not tasks:
            print("No tasks found.")
            return 0
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            due_str = f" (due: {task.due_date.isoformat()})" if task.due_date else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}{due_str}")
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
            print(f"Due:         {task.due_date.isoformat()}")
            print(f"Overdue:     {'Yes' if task.is_overdue() else 'No'}")
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

    def _cmd_is_pending(self, args: argparse.Namespace) -> int:
        is_pending = self._service.is_task_pending(args.id)
        print(f"{'Yes' if is_pending else 'No'}")
        return 0

    def _cmd_is_in_progress(self, args: argparse.Namespace) -> int:
        is_in_progress = self._service.is_task_in_progress(args.id)
        print(f"{'Yes' if is_in_progress else 'No'}")
        return 0

    def _cmd_is_completed(self, args: argparse.Namespace) -> int:
        is_completed = self._service.is_task_completed(args.id)
        print(f"{'Yes' if is_completed else 'No'}")
        return 0

    def _cmd_is_overdue(self, args: argparse.Namespace) -> int:
        is_overdue = self._service.is_task_overdue(args.id)
        print(f"{'Yes' if is_overdue else 'No'}")
        return 0

    def _cmd_add_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.task_id, args.content, args.author)
        print(f"Added comment {comment.id[:8]} to task {args.task_id[:8]}")
        return 0

    def _cmd_list_comments(self, args: argparse.Namespace) -> int:
        comments = self._service.list_comments(args.task_id)
        if not comments:
            print(f"No comments for task {args.task_id[:8]}")
            return 0
        for comment in comments:
            author_str = f" by {comment.author}" if comment.author else ""
            print(f"  {comment.id[:8]}{author_str}:")
            print(f"    {comment.content}")
            if comment.updated_at:
                print(f"    (edited: {comment.updated_at.isoformat()})")
        return 0

    def _cmd_delete_comment(self, args: argparse.Namespace) -> int:
        self._service.delete_comment(args.comment_id)
        print(f"Deleted comment {args.comment_id[:8]}")
        return 0

    def _cmd_edit_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.edit_comment(args.comment_id, args.content)
        print(f"Updated comment {comment.id[:8]}")
        return 0

    def _cmd_report(self, args: argparse.Namespace) -> int:
        report = self._service.generate_report()
        print("Task Summary Report")
        print("=" * 40)
        print(f"Total tasks: {report.total_tasks}")
        print(f"Pending: {report.pending_count}")
        print(f"In progress: {report.in_progress_count}")
        print(f"Done: {report.done_count}")
        print(f"Overdue: {report.overdue_count}")
        print(f"With due date: {report.with_due_date_count}")
        print(f"Completion rate: {report.completion_rate:.1f}%")
        if report.avg_days_to_completion is not None:
            print(f"Avg days to completion: {report.avg_days_to_completion:.2f}")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        count = self._import_export.export_to_file(args.filepath)
        print(f"Exported {count} items to {args.filepath}")
        return 0

    def _cmd_import(self, args: argparse.Namespace) -> int:
        summary = self._import_export.import_from_file(args.filepath, merge=args.merge)
        print(f"Import Summary:")
        print(summary)
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
            print(f"  {project.id[:8]}  {project.name}")
        return 0

    def _cmd_show_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        print(f"ID:         {project.id}")
        print(f"Name:       {project.name}")
        print(f"Created:    {project.created_at.isoformat()}")
        return 0

    def _cmd_update_project(self, args: argparse.Namespace) -> int:
        project = self._service.update_project(args.id, args.name)
        print(f"Updated project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_delete_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        self._service.delete_project(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_list_tasks_by_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.project_id)
        tasks = self._service.list_tasks_by_project(args.project_id)
        if not tasks:
            print(f"No tasks in project '{project.name}'.")
            return 0
        print(f"Tasks in project '{project.name}':")
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}")
        return 0

    def _cmd_assign_task_to_project(self, args: argparse.Namespace) -> int:
        task = self._service.assign_task_to_project(args.task_id, args.project_id)
        project = self._service.get_project(args.project_id)
        print(f"Assigned task {task.id[:8]} to project '{project.name}'")
        return 0

    def _cmd_unassign_task_from_project(self, args: argparse.Namespace) -> int:
        task = self._service.unassign_task_from_project(args.task_id)
        print(f"Unassigned task {task.id[:8]} from project")
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
            print(f"  {project.id[:8]}  {project.name}")
        return 0

    def _cmd_show_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        print(f"ID:    {project.id}")
        print(f"Name:  {project.name}")
        return 0

    def _cmd_update_project(self, args: argparse.Namespace) -> int:
        project = self._service.update_project(args.id, args.name)
        print(f"Updated project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_delete_project(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        self._service.delete_project(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_list_tasks_by_project(self, args: argparse.Namespace) -> int:
        tasks = self._service.list_tasks_by_project(args.project_id)
        if not tasks:
            print("No tasks in this project.")
            return 0
        for task in tasks:
            sym = _STATUS_SYMBOLS[task.status]
            desc = f"  {task.description}" if task.description else ""
            print(f"{sym} {task.id[:8]}  {task.title}{desc}")
        return 0

    def _cmd_assign_task_to_project(self, args: argparse.Namespace) -> int:
        task = self._service.assign_task_to_project(args.task_id, args.project_id)
        print(f"Assigned task {task.id[:8]} to project {args.project_id[:8]}")
        return 0

    def _cmd_unassign_task_from_project(self, args: argparse.Namespace) -> int:
        task = self._service.unassign_task_from_project(args.task_id)
        print(f"Unassigned task {task.id[:8]} from project")
        return 0
