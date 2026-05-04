import os
from datetime import datetime
from typing import Optional

from ..container import Container
from ..exceptions import (
    TaskNotFoundError,
    CommentNotFoundError,
    ProjectNotFoundError,
    ImportExportError,
)
from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..services.todo_service import TodoService

_STATUS_LABEL = {
    TaskStatus.PENDING: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
}

_STATUS_NAME = {
    TaskStatus.PENDING: "pending",
    TaskStatus.IN_PROGRESS: "in progress",
    TaskStatus.DONE: "done",
}


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(label: str, default: Optional[str] = None) -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"  {label}{hint}: ").strip()
    return value if value else (default or "")


def _pick(prompt: str, options: list[str]) -> Optional[int]:
    """Print numbered options, return 0-based index or None on cancel."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("  0. Cancel")
    raw = input(f"  {prompt}: ").strip()
    if not raw.isdigit():
        return None
    n = int(raw)
    if n == 0 or n > len(options):
        return None
    return n - 1


def _task_line(task: Task) -> str:
    sym = _STATUS_LABEL[task.status]
    return f"{sym} {task.id[:8]}  {task.title}"


class InteractiveMenu:
    def __init__(self, service: Optional[TodoService] = None, storage_path: Optional[str] = None) -> None:
        """Initialize InteractiveMenu with optional service or storage path.

        Args:
            service: TodoService instance (if provided, storage_path is ignored)
            storage_path: Path to task storage file (if service not provided)
        """
        if service is not None:
            self._service = service
        else:
            container = Container(storage_path)
            self._service = container.get_todo_service()

    def run(self) -> None:
        while True:
            _clear()
            self._print_header()
            tasks = self._service.list_tasks()
            self._print_task_list(tasks)
            self._print_main_menu()

            choice = input("  > ").strip().lower()

            if choice in ("0", "q", "quit", "exit"):
                _clear()
                break
            elif choice == "1":
                self._do_list()
            elif choice == "2":
                self._do_add()
            elif choice == "3":
                self._do_show(tasks)
            elif choice == "4":
                self._do_change_status(tasks)
            elif choice == "5":
                self._do_update(tasks)
            elif choice == "6":
                self._do_delete(tasks)
            elif choice == "7":
                self._do_check_completed(tasks)
            elif choice == "8":
                self._do_check_overdue(tasks)
            elif choice == "9":
                self._do_manage_comments(tasks)
            elif choice == "10":
                self._do_statistics()
            elif choice == "11":
                self._do_import_export()
            elif choice == "12":
                self._do_manage_projects()
            else:
                input("  Unknown option. Press Enter to continue...")

    # ── display helpers ────────────────────────────────────────────────────

    def _print_header(self) -> None:
        print("╔══════════════════════════════════╗")
        print("║          TODO  Manager           ║")
        print("╚══════════════════════════════════╝")
        print()

    def _print_task_list(self, tasks: list[Task]) -> None:
        if not tasks:
            print("  (no tasks yet)")
        else:
            for task in tasks:
                print(f"  {_task_line(task)}")
        print()

    def _print_main_menu(self) -> None:
        print("  1. List / filter tasks")
        print("  2. Add task")
        print("  3. Show task details")
        print("  4. Change status  (start / done / reopen)")
        print("  5. Update task    (title / description)")
        print("  6. Delete task")
        print("  7. Check if task is completed")
        print("  8. Check if task is overdue")
        print("  9. Manage comments")
        print("  10. View statistics")
        print("  11. Import / export")
        print("  12. Manage projects")
        print("  0. Quit")
        print()

    # ── actions ────────────────────────────────────────────────────────────

    def _do_list(self) -> None:
        _clear()
        print("  Filter by status (leave blank for all):")
        print("  1. pending")
        print("  2. in progress")
        print("  3. done")
        print("  0. All")
        raw = input("  > ").strip()
        status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
        status = status_map.get(raw)

        # Ask for date filtering
        _clear()
        print("  Filter by due date (leave blank for no date filter):")
        due_after_str = _prompt("Due on or after (YYYY-MM-DD)") or None
        due_after = None
        if due_after_str:
            try:
                due_after = datetime.fromisoformat(due_after_str)
            except ValueError:
                print(f"  Error: Invalid date format '{due_after_str}'. Using no date filter.")
                due_after = None

        due_before_str = _prompt("Due on or before (YYYY-MM-DD)") or None
        due_before = None
        if due_before_str:
            try:
                due_before = datetime.fromisoformat(due_before_str)
            except ValueError:
                print(f"  Error: Invalid date format '{due_before_str}'. Using no date filter.")
                due_before = None

        # Ask for overdue filtering
        _clear()
        print("  Filter by overdue status:")
        print("  1. Overdue only")
        print("  2. Not overdue only")
        print("  0. All (default)")
        overdue_raw = input("  > ").strip()
        overdue_map = {"1": True, "2": False}
        overdue = overdue_map.get(overdue_raw)

        _clear()
        tasks = self._service.list_tasks(
            status=status,
            due_after=due_after,
            due_before=due_before,
            overdue=overdue,
        )

        # Build label showing which filters are active
        filters = []
        if status:
            filters.append(_STATUS_NAME[status])
        if due_after:
            filters.append(f"due≥{due_after.strftime('%Y-%m-%d')}")
        if due_before:
            filters.append(f"due≤{due_before.strftime('%Y-%m-%d')}")
        if overdue is True:
            filters.append("overdue")
        elif overdue is False:
            filters.append("not-overdue")

        label = f"[{', '.join(filters)}]" if filters else "[all]"
        print(f"  Tasks {label}\n")
        if not tasks:
            print("  (none)")
        else:
            for task in tasks:
                desc = f"  — {task.description}" if task.description else ""
                print(f"  {_task_line(task)}{desc}")
        print()
        input("  Press Enter to continue...")

    def _do_add(self) -> None:
        _clear()
        print("  Add new task\n")
        title = _prompt("Title")
        if not title:
            input("  Title cannot be empty. Press Enter...")
            return
        description = _prompt("Description (optional)") or None
        try:
            task = self._service.add_task(title, description)
            print(f"\n  Added: {_task_line(task)}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_show(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Show details — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]
        _clear()
        print(f"  ID:          {task.id}")
        print(f"  Title:       {task.title}")
        print(f"  Description: {task.description or '—'}")
        print(f"  Status:      {task.status.value}")
        print(f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()
        input("  Press Enter to continue...")

    def _do_change_status(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Change status — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}  (current: {task.status.value})\n")
        action_idx = _pick("New status", ["start  (in progress)", "done", "reopen  (pending)"])
        if action_idx is None:
            return

        try:
            actions = [self._service.start_task, self._service.complete_task, self._service.reopen_task]
            updated = actions[action_idx](task.id)
            print(f"\n  Updated: {_task_line(updated)}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_update(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Update task — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Editing: {task.title}\n")
        new_title = _prompt("New title", default=task.title)
        new_desc = _prompt("New description", default=task.description or "")
        new_desc = new_desc if new_desc else None

        try:
            updated = self._service.update_task(task.id, title=new_title or None, description=new_desc)
            print(f"\n  Updated: {_task_line(updated)}")
        except (TaskNotFoundError, ValueError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Delete task — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Delete: {task.title}")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_task(task.id)
            print(f"  Deleted: {task.id[:8]}  {task.title}")
        except TaskNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_check_completed(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Check if completed — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}\n")
        if task.is_completed():
            print("  Status: completed")
        else:
            print("  Status: not completed")
        input("  Press Enter to continue...")

    def _do_check_overdue(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Check if overdue — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        _clear()
        print(f"  Task: {task.title}\n")
        if task.is_overdue():
            print("  Status: overdue")
        else:
            print("  Status: not overdue")
        input("  Press Enter to continue...")

    def _do_manage_comments(self, tasks: list[Task]) -> None:
        _clear()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Manage comments — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        while True:
            _clear()
            print(f"  Task: {task.title}\n")
            comments = self._service.get_comments(task.id)
            self._print_comment_list(comments)
            self._print_comment_menu()

            choice = input("  > ").strip().lower()
            if choice in ("0", "q", "quit", "exit", "back"):
                break
            elif choice == "1":
                self._do_view_comments(comments)
            elif choice == "2":
                self._do_add_comment(task)
            elif choice == "3":
                self._do_delete_comment(comments)
            else:
                input("  Unknown option. Press Enter to continue...")

    def _print_comment_list(self, comments: list[TaskComment]) -> None:
        if not comments:
            print("  (no comments yet)")
        else:
            for comment in comments:
                author = f" — {comment.author}" if comment.author else ""
                print(f"  {comment.id[:8]}{author}: {comment.content[:50]}")
        print()

    def _print_comment_menu(self) -> None:
        print("  1. View all comments")
        print("  2. Add comment")
        print("  3. Delete comment")
        print("  0. Back")
        print()

    def _do_view_comments(self, comments: list[TaskComment]) -> None:
        _clear()
        if not comments:
            print("  No comments.\n")
            input("  Press Enter to continue...")
            return
        print("  Comments:\n")
        for comment in comments:
            author = f" ({comment.author})" if comment.author else ""
            print(f"  {comment.id[:8]}{author}")
            print(f"  Created: {comment.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"  {comment.content}")
            print()
        input("  Press Enter to continue...")

    def _do_add_comment(self, task: Task) -> None:
        _clear()
        print(f"  Add comment to: {task.title}\n")
        content = _prompt("Comment")
        if not content:
            input("  Comment cannot be empty. Press Enter...")
            return
        author = _prompt("Author (optional)") or None
        try:
            self._service.add_comment(task.id, content, author)
            print(f"\n  Added comment.")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_comment(self, comments: list[TaskComment]) -> None:
        _clear()
        if not comments:
            input("  No comments to delete. Press Enter...")
            return
        print("  Delete comment — pick one:\n")
        idx = _pick("Select", [f"{c.id[:8]}: {c.content[:40]}" for c in comments])
        if idx is None:
            return
        comment = comments[idx]

        _clear()
        print(f"  Delete: {comment.content[:60]}")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

        try:
            self._service.delete_comment(comment.id)
            print(f"  Deleted comment {comment.id[:8]}")
        except CommentNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_statistics(self) -> None:
        _clear()
        stats = self._service.get_statistics()
        print("  Task Statistics\n")
        print(f"  Total tasks:           {stats.total_count}")
        print(f"  Pending:               {stats.pending_count}")
        print(f"  In Progress:           {stats.in_progress_count}")
        print(f"  Done:                  {stats.done_count}")
        print(f"  Overdue (active):      {stats.overdue_count}")
        print(f"  With due date:         {stats.with_due_date_count}")
        print()
        input("  Press Enter to continue...")

    def _do_import_export(self) -> None:
        """Handle import/export submenu."""
        while True:
            _clear()
            print("  Import / Export\n")
            print("  1. Export tasks and comments")
            print("  2. Import tasks and comments")
            print("  0. Back\n")

            choice = input("  > ").strip().lower()

            if choice == "0":
                break
            elif choice == "1":
                self._do_export()
            elif choice == "2":
                self._do_import()
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_export(self) -> None:
        """Export tasks, comments, and projects to a JSON file."""
        _clear()
        print("  Export Tasks, Comments, and Projects\n")
        filepath = _prompt("Enter file path to export to")
        if not filepath:
            input("  No path provided. Press Enter to continue...")
            return

        try:
            tasks_exported, comments_exported, projects_exported = self._service.export_tasks_and_comments(filepath)
            print()
            print(f"  Successfully exported {tasks_exported} task(s), {comments_exported} comment(s), and {projects_exported} project(s)")
            print(f"  to: {filepath}")
        except ImportExportError as e:
            print()
            print(f"  Error: {e}")
        except Exception as e:
            print()
            print(f"  Unexpected error: {e}")

        input("  Press Enter to continue...")

    def _do_import(self) -> None:
        """Import tasks, comments, and projects from a JSON file."""
        _clear()
        print("  Import Tasks, Comments, and Projects\n")
        filepath = _prompt("Enter file path to import from")
        if not filepath:
            input("  No path provided. Press Enter to continue...")
            return

        print()
        print("  How to handle ID conflicts?")
        print("  1. fail   - Stop if any IDs already exist (default)")
        print("  2. skip   - Skip conflicting records, keep existing data")
        print("  3. replace - Overwrite existing records with imported data\n")

        mode_choice = input("  > ").strip().lower()
        mode_map = {"1": "fail", "2": "skip", "3": "replace"}
        mode = mode_map.get(mode_choice, "fail")

        try:
            tasks_imported, comments_imported, projects_imported, conflicts = self._service.import_tasks_and_comments(
                filepath, mode=mode
            )
            print()
            print(f"  Successfully imported {tasks_imported} task(s), {comments_imported} comment(s), and {projects_imported} project(s)")
            if conflicts > 0:
                if mode == "fail":
                    print(f"  Warning: {conflicts} conflict(s) detected (mode=fail)")
                elif mode == "skip":
                    print(f"  Skipped {conflicts} conflicting record(s) (mode=skip)")
                elif mode == "replace":
                    print(f"  Replaced {conflicts} existing record(s) (mode=replace)")
        except ImportExportError as e:
            print()
            print(f"  Error: {e}")
        except Exception as e:
            print()
            print(f"  Unexpected error: {e}")

        input("  Press Enter to continue...")

    def _do_manage_projects(self) -> None:
        """Handle project management submenu."""
        while True:
            _clear()
            print("  Manage Projects\n")
            projects = self._service.list_projects()
            if projects:
                for project in projects:
                    print(f"  {project.id[:8]}  {project.name}")
            else:
                print("  (no projects yet)")
            print()
            print("  1. Create project")
            print("  2. Show project details")
            print("  3. Update project")
            print("  4. Delete project")
            print("  5. Assign task to project")
            print("  6. Unassign task from project")
            print("  0. Back\n")

            choice = input("  > ").strip().lower()

            if choice == "0":
                break
            elif choice == "1":
                self._do_create_project()
            elif choice == "2":
                self._do_show_project()
            elif choice == "3":
                self._do_update_project()
            elif choice == "4":
                self._do_delete_project()
            elif choice == "5":
                self._do_assign_task()
            elif choice == "6":
                self._do_unassign_task()
            else:
                input("  Unknown option. Press Enter to continue...")

    def _do_create_project(self) -> None:
        """Create a new project."""
        _clear()
        print("  Create Project\n")
        name = _prompt("Project name")
        if not name:
            input("  Project name cannot be empty. Press Enter...")
            return
        try:
            project = self._service.create_project(name)
            print(f"\n  Created project: {project.id[:8]}  {project.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_show_project(self) -> None:
        """Show project details."""
        _clear()
        projects = self._service.list_projects()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Show project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  ID:         {project.id}")
        print(f"  Name:       {project.name}")
        print(f"  Created:    {project.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()
        # Show tasks in this project
        tasks = self._service.list_tasks_by_project(project.id)
        if tasks:
            print("  Tasks in this project:")
            for task in tasks:
                print(f"    {_task_line(task)}")
        else:
            print("  (no tasks in this project)")
        print()
        input("  Press Enter to continue...")

    def _do_update_project(self) -> None:
        """Update a project name."""
        _clear()
        projects = self._service.list_projects()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Update project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  Update project: {project.name}\n")
        new_name = _prompt("New name", default=project.name)
        if not new_name:
            input("  Name cannot be empty. Press Enter...")
            return
        try:
            updated = self._service.update_project(project.id, new_name)
            print(f"\n  Updated project to: {updated.name}")
        except ValueError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_delete_project(self) -> None:
        """Delete a project."""
        _clear()
        projects = self._service.list_projects()
        if not projects:
            input("  No projects. Press Enter...")
            return
        print("  Delete project — pick one:\n")
        idx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if idx is None:
            return
        project = projects[idx]
        _clear()
        print(f"  Delete project: {project.name}")
        confirm = input("  Are you sure? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return
        try:
            self._service.delete_project(project.id)
            print(f"  Deleted project: {project.name}")
        except ProjectNotFoundError as e:
            print(f"  Error: {e}")
        input("  Press Enter to continue...")

    def _do_assign_task(self) -> None:
        """Assign a task to a project."""
        _clear()
        tasks = self._service.list_tasks()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        print("  Assign task to project — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in tasks])
        if idx is None:
            return
        task = tasks[idx]

        projects = self._service.list_projects()
        if not projects:
            input("  No projects available. Press Enter...")
            return
        _clear()
        print(f"  Assign task to project: {task.title}\n")
        print("  Pick a project:\n")
        pidx = _pick("Select", [f"{p.id[:8]}  {p.name}" for p in projects])
        if pidx is None:
            return
        project = projects[pidx]
        try:
            self._service.assign_task_to_project(task.id, project.id)
            print(f"\n  Assigned task to project: {project.name}")
        except (TaskNotFoundError, ProjectNotFoundError) as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")

    def _do_unassign_task(self) -> None:
        """Unassign a task from its project."""
        _clear()
        tasks = self._service.list_tasks()
        if not tasks:
            input("  No tasks. Press Enter...")
            return
        # Filter to only tasks with a project
        assigned_tasks = [t for t in tasks if t.project_id is not None]
        if not assigned_tasks:
            input("  No tasks currently assigned to projects. Press Enter...")
            return
        print("  Unassign task from project — pick a task:\n")
        idx = _pick("Select", [_task_line(t) for t in assigned_tasks])
        if idx is None:
            return
        task = assigned_tasks[idx]
        try:
            self._service.unassign_task_from_project(task.id)
            print(f"\n  Unassigned task from project")
        except TaskNotFoundError as e:
            print(f"\n  Error: {e}")
        input("  Press Enter to continue...")
