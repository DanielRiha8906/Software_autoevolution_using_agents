import argparse
import sys
from datetime import datetime
from typing import Optional

from ..models.task_status import TaskStatus
from ..services.comment_manager import CommentNotFoundError
from ..services.import_export_service import ImportExportError
from ..services.task_manager import TaskNotFoundError
from ..services.project_manager import ProjectNotFoundError
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
        except (TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError, ImportExportError) as e:
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
            "--due-after",
            help="Filter tasks with due_date >= this date (ISO8601 string, e.g. 2026-05-15)",
        )
        p_list.add_argument(
            "--due-before",
            help="Filter tasks with due_date <= this date (ISO8601 string, e.g. 2026-05-15)",
        )
        p_list.add_argument(
            "--overdue",
            action="store_true",
            help="Show only overdue tasks",
        )
        p_list.add_argument(
            "--not-overdue",
            action="store_true",
            help="Show only non-overdue tasks",
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

        # is-completed
        p_is_completed = sub.add_parser("is-completed", help="Check if task is completed")
        p_is_completed.add_argument("id", help="Task ID")
        p_is_completed.set_defaults(func=self._cmd_is_completed)

        # check-overdue
        p_check_overdue = sub.add_parser("check-overdue", help="Check if task is overdue")
        p_check_overdue.add_argument("id", help="Task ID")
        p_check_overdue.set_defaults(func=self._cmd_check_overdue)

        # add-comment
        p_add_comment = sub.add_parser("add-comment", help="Add a comment to a task")
        p_add_comment.add_argument("task_id", help="Task ID")
        p_add_comment.add_argument("content", help="Comment content")
        p_add_comment.add_argument("-a", "--author", help="Optional author name")
        p_add_comment.set_defaults(func=self._cmd_add_comment)

        # show-comments
        p_show_comments = sub.add_parser("show-comments", help="Show comments on a task")
        p_show_comments.add_argument("task_id", help="Task ID")
        p_show_comments.set_defaults(func=self._cmd_show_comments)

        # delete-comment
        p_delete_comment = sub.add_parser("delete-comment", help="Delete a comment")
        p_delete_comment.add_argument("comment_id", help="Comment ID")
        p_delete_comment.set_defaults(func=self._cmd_delete_comment)

        # stats
        p_stats = sub.add_parser("stats", help="Show task statistics")
        p_stats.set_defaults(func=self._cmd_stats)

        # export
        p_export = sub.add_parser("export", help="Export tasks and comments to JSON")
        p_export.add_argument("filepath", help="Path to write the JSON export file")
        p_export.set_defaults(func=self._cmd_export)

        # import
        p_import = sub.add_parser("import", help="Import tasks and comments from JSON")
        p_import.add_argument("filepath", help="Path to the JSON import file")
        p_import.add_argument(
            "--mode",
            choices=["fail", "skip", "replace"],
            default="fail",
            help="How to handle ID conflicts: fail (default), skip, or replace",
        )
        p_import.set_defaults(func=self._cmd_import)

        # project create
        p_project_create = sub.add_parser("project-create", help="Create a new project")
        p_project_create.add_argument("name", help="Project name")
        p_project_create.set_defaults(func=self._cmd_project_create)

        # project list
        p_project_list = sub.add_parser("project-list", help="List all projects")
        p_project_list.set_defaults(func=self._cmd_project_list)

        # project show
        p_project_show = sub.add_parser("project-show", help="Show project details")
        p_project_show.add_argument("id", help="Project ID")
        p_project_show.set_defaults(func=self._cmd_project_show)

        # project update
        p_project_update = sub.add_parser("project-update", help="Update project name")
        p_project_update.add_argument("id", help="Project ID")
        p_project_update.add_argument("-n", "--name", required=True, help="New project name")
        p_project_update.set_defaults(func=self._cmd_project_update)

        # project delete
        p_project_delete = sub.add_parser("project-delete", help="Delete a project")
        p_project_delete.add_argument("id", help="Project ID")
        p_project_delete.set_defaults(func=self._cmd_project_delete)

        # assign
        p_assign = sub.add_parser("assign", help="Assign a task to a project")
        p_assign.add_argument("task_id", help="Task ID")
        p_assign.add_argument("project_id", help="Project ID")
        p_assign.set_defaults(func=self._cmd_assign)

        # unassign
        p_unassign = sub.add_parser("unassign", help="Unassign a task from its project")
        p_unassign.add_argument("task_id", help="Task ID")
        p_unassign.set_defaults(func=self._cmd_unassign)

        return parser

    def _cmd_add(self, args: argparse.Namespace) -> int:
        task = self._service.add_task(args.title, args.description)
        print(f"Added task {task.id[:8]}  {task.title}")
        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        status = TaskStatus(args.status) if args.status else None

        # Parse due_after and due_before using datetime.fromisoformat()
        due_after = None
        due_before = None
        if args.due_after:
            try:
                due_after = datetime.fromisoformat(args.due_after)
            except ValueError as e:
                print(f"Error: Invalid due_after date format: {e}", file=sys.stderr)
                return 1

        if args.due_before:
            try:
                due_before = datetime.fromisoformat(args.due_before)
            except ValueError as e:
                print(f"Error: Invalid due_before date format: {e}", file=sys.stderr)
                return 1

        # Determine overdue filter
        overdue = None
        if args.overdue and args.not_overdue:
            print("Error: Cannot use both --overdue and --not-overdue", file=sys.stderr)
            return 1
        if args.overdue:
            overdue = True
        elif args.not_overdue:
            overdue = False

        tasks = self._service.list_tasks(
            status=status,
            due_after=due_after,
            due_before=due_before,
            overdue=overdue,
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

    def _cmd_is_completed(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        if task.is_completed():
            print(f"{task.id[:8]}  {task.title}")
            print("Status: completed")
            return 0
        else:
            print(f"{task.id[:8]}  {task.title}")
            print("Status: not completed")
            return 0

    def _cmd_check_overdue(self, args: argparse.Namespace) -> int:
        task = self._service.get_task(args.id)
        if task.is_overdue():
            print(f"{task.id[:8]}  {task.title}")
            print("Status: overdue")
            return 0
        else:
            print(f"{task.id[:8]}  {task.title}")
            print("Status: not overdue")
            return 0

    def _cmd_add_comment(self, args: argparse.Namespace) -> int:
        comment = self._service.add_comment(args.task_id, args.content, args.author)
        print(f"Added comment {comment.id[:8]} to task {args.task_id[:8]}")
        return 0

    def _cmd_show_comments(self, args: argparse.Namespace) -> int:
        comments = self._service.get_comments(args.task_id)
        if not comments:
            print(f"No comments on task {args.task_id[:8]}")
            return 0
        print(f"Comments on task {args.task_id[:8]}:\n")
        for comment in comments:
            author = f" ({comment.author})" if comment.author else ""
            print(f"  {comment.id[:8]}{author}")
            print(f"  {comment.created_at.isoformat()}")
            print(f"  {comment.content}")
            print()
        return 0

    def _cmd_delete_comment(self, args: argparse.Namespace) -> int:
        comment = self._service._comment_manager.get(args.comment_id)
        self._service.delete_comment(args.comment_id)
        print(f"Deleted comment {comment.id[:8]}")
        return 0

    def _cmd_stats(self, args: argparse.Namespace) -> int:
        stats = self._service.get_statistics()
        print(f"Task Statistics:")
        print(f"  Total:           {stats.total_count}")
        print(f"  Pending:         {stats.pending_count}")
        print(f"  In Progress:     {stats.in_progress_count}")
        print(f"  Done:            {stats.done_count}")
        print(f"  Overdue:         {stats.overdue_count}")
        print(f"  With due date:   {stats.with_due_date_count}")
        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        tasks_exported, comments_exported, projects_exported = self._service.export_tasks_and_comments(args.filepath)
        print(f"Exported {tasks_exported} task(s), {comments_exported} comment(s), and {projects_exported} project(s) to {args.filepath}")
        return 0

    def _cmd_import(self, args: argparse.Namespace) -> int:
        tasks_imported, comments_imported, projects_imported, conflicts = self._service.import_tasks_and_comments(
            args.filepath, mode=args.mode
        )
        print(f"Imported {tasks_imported} task(s), {comments_imported} comment(s), and {projects_imported} project(s) from {args.filepath}")
        if conflicts > 0:
            if args.mode == "fail":
                print(f"Warning: {conflicts} conflict(s) skipped (mode=fail)")
            elif args.mode == "skip":
                print(f"Skipped {conflicts} conflicting record(s) (mode=skip)")
            elif args.mode == "replace":
                print(f"Replaced {conflicts} existing record(s) (mode=replace)")
        return 0

    def _cmd_project_create(self, args: argparse.Namespace) -> int:
        project = self._service.create_project(args.name)
        print(f"Created project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_list(self, args: argparse.Namespace) -> int:
        projects = self._service.list_projects()
        if not projects:
            print("No projects found.")
            return 0
        for project in projects:
            print(f"  {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_show(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        print(f"ID:         {project.id}")
        print(f"Name:       {project.name}")
        print(f"Created:    {project.created_at.isoformat()}")
        return 0

    def _cmd_project_update(self, args: argparse.Namespace) -> int:
        project = self._service.update_project(args.id, args.name)
        print(f"Updated project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_project_delete(self, args: argparse.Namespace) -> int:
        project = self._service.get_project(args.id)
        self._service.delete_project(args.id)
        print(f"Deleted project {project.id[:8]}  {project.name}")
        return 0

    def _cmd_assign(self, args: argparse.Namespace) -> int:
        task = self._service.assign_task_to_project(args.task_id, args.project_id)
        print(f"Assigned task {task.id[:8]} to project {args.project_id[:8]}")
        return 0

    def _cmd_unassign(self, args: argparse.Namespace) -> int:
        task = self._service.unassign_task_from_project(args.task_id)
        print(f"Unassigned task {task.id[:8]} from project")
        return 0
