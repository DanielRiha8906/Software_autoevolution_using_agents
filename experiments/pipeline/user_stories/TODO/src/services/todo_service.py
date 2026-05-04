from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.task_comment import TaskComment
from ..models.task_summary_report import TaskSummaryReport
from ..models.project import Project
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager
from .project_manager import ProjectManager
from .exceptions import TaskNotFoundError, ProjectNotFoundError
from .import_validator import ImportValidator


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._project_manager = ProjectManager(storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return self._manager.add(title.strip(), description, due_date)

    def list_tasks_by_week(
        self, year: int, week: int, status: Optional[TaskStatus] = None
    ) -> list[Task]:
        """List tasks due in a specific ISO 8601 week.

        Args:
            year: Year (e.g., 2026).
            week: ISO week number (1-53).
            status: Optional status filter (TaskStatus enum or None).

        Returns:
            list[Task]: Tasks due in the specified week.

        Raises:
            ValueError: If week is not in 1-53.
        """
        week_start, week_end = self._manager.get_week_boundaries(year, week)
        return self._manager.list_by_due_date_range(
            after=week_start, before=week_end, status=status
        )

    def list_tasks_by_month(
        self, year: int, month: int, status: Optional[TaskStatus] = None
    ) -> list[Task]:
        """List tasks due in a specific calendar month.

        Args:
            year: Year (e.g., 2026).
            month: Month (1-12).
            status: Optional status filter (TaskStatus enum or None).

        Returns:
            list[Task]: Tasks due in the specified month.

        Raises:
            ValueError: If month is not in 1-12.
        """
        month_start, month_end = self._manager.get_month_boundaries(year, month)
        return self._manager.list_by_due_date_range(
            after=month_start, before=month_end, status=status
        )

    def list_tasks_by_year(
        self, year: int, status: Optional[TaskStatus] = None
    ) -> list[Task]:
        """List tasks due in a specific calendar year.

        Args:
            year: Year (e.g., 2026).
            status: Optional status filter (TaskStatus enum or None).

        Returns:
            list[Task]: Tasks due in the specified year.
        """
        year_start, year_end = self._manager.get_year_boundaries(year)
        return self._manager.list_by_due_date_range(
            after=year_start, before=year_end, status=status
        )

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        overdue_only: bool = False,
    ) -> list[Task]:
        """List tasks with optional filtering by status and due date.

        Args:
            status: Filter by status (TaskStatus enum or None for all).
            before: Filter tasks with due_date <= before (datetime or None).
            after: Filter tasks with due_date >= after (datetime or None).
            overdue_only: If True, include only overdue tasks.

        Returns:
            list[Task]: Filtered task list.
        """
        if before is not None or after is not None or overdue_only:
            return self._manager.list_by_due_date_range(
                before=before, after=after, status=status, overdue_only=overdue_only
            )
        if status is not None:
            return self._manager.list_by_status(status)
        return self._manager.list_all()

    def list_tasks_by_project(self, project_id: str) -> list[Task]:
        """List all tasks in a project.

        Args:
            project_id: The project ID.

        Returns:
            list[Task]: All tasks in the project.
        """
        return self._manager.list_by_project(project_id)

    def create_project(self, name: str) -> Project:
        """Create a new project.

        Args:
            name: Project name (non-empty string).

        Returns:
            Project: The created project.

        Raises:
            ValueError: If name is empty.
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        return self._project_manager.add(name.strip())

    def list_projects(self) -> list[Project]:
        """Get all projects.

        Returns:
            list[Project]: All projects.
        """
        return self._project_manager.list_all()

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID or prefix.

        Args:
            project_id: The project ID or partial ID.

        Returns:
            Project: The project.

        Raises:
            ProjectNotFoundError: If project not found.
        """
        return self._project_manager.get(project_id)

    def delete_project(self, project_id: str) -> None:
        """Delete a project (tasks are orphaned, not deleted).

        Args:
            project_id: The project ID.

        Raises:
            ProjectNotFoundError: If project not found.
        """
        project = self._project_manager.get(project_id)  # Validates existence
        self._manager.orphan_project_tasks(project.id)  # Orphan tasks first
        self._project_manager.delete(project_id)

    def move_task_to_project(self, task_id: str, project_id: Optional[str]) -> Task:
        """Assign or reassign a task to a project.

        Args:
            task_id: The task ID.
            project_id: The project ID, or None to unassign.

        Returns:
            Task: The updated task.

        Raises:
            TaskNotFoundError: If task is not found.
            ProjectNotFoundError: If project_id is provided but project not found.
        """
        if project_id is not None:
            self._project_manager.get(project_id)  # Validates project exists
        return self._manager.set_project(task_id, project_id)

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def set_due_date(self, task_id: str, due_date: Optional[datetime]) -> Task:
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return self._manager.set_due_date(task_id, due_date)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to comment on.
            content: The comment content (non-empty string).
            author: Optional author name for the comment.

        Returns:
            TaskComment: The created comment.

        Raises:
            ValueError: If content is empty.
            TaskNotFoundError: If task is not found.
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        return self._manager.add_comment(task_id, content.strip(), author)

    def get_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task.

        Args:
            task_id: The ID of the task.

        Returns:
            list[TaskComment]: All comments for the task.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        return self._manager.get_comments(task_id)

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a comment from a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to delete.

        Raises:
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found on the task.
        """
        self._manager.delete_comment(task_id, comment_id)

    def edit_comment(self, task_id: str, comment_id: str, content: str) -> TaskComment:
        """Edit a comment on a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to edit.
            content: The new comment content (non-empty string).

        Returns:
            TaskComment: The updated comment.

        Raises:
            ValueError: If content is empty.
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found on the task.
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        return self._manager.edit_comment(task_id, comment_id, content.strip())

    def generate_report(self) -> TaskSummaryReport:
        """Generate a summary report of task statistics.

        Returns:
            TaskSummaryReport: Summary statistics including total count, status breakdown,
                             completion rate, and average days to completion for done tasks.
        """
        tasks = self.list_tasks()
        total_count = len(tasks)

        pending_count = len(self.list_tasks(status=TaskStatus.PENDING))
        in_progress_count = len(self.list_tasks(status=TaskStatus.IN_PROGRESS))
        done_count = len(self.list_tasks(status=TaskStatus.DONE))

        overdue_count = sum(1 for task in tasks if task.is_overdue())
        due_date_set_count = sum(1 for task in tasks if task.due_date is not None)

        completion_rate = done_count / total_count if total_count > 0 else 0.0

        avg_days_to_completion = None
        done_tasks = [t for t in tasks if t.is_completed()]
        if done_tasks:
            total_days = sum((t.updated_at - t.created_at).days for t in done_tasks)
            avg_days_to_completion = total_days / len(done_tasks)

        return TaskSummaryReport(
            total_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            due_date_set_count=due_date_set_count,
            completion_rate=completion_rate,
            avg_days_to_completion=avg_days_to_completion,
        )

    def export_tasks(self, file_path: Optional[str] = None) -> int:
        """Export all tasks to a JSON file.

        Args:
            file_path: Path to export to. If None, uses default location.

        Returns:
            int: Number of tasks exported.

        Raises:
            OSError: If file cannot be written.
        """
        tasks = self.list_tasks()
        task_dicts = [t.to_dict() for t in tasks]

        if file_path is None:
            file_path = str(Path.home() / ".todo_export.json")

        # Create parent directories if needed
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task_dicts, f, indent=2, ensure_ascii=False)

        return len(task_dicts)

    def import_tasks(self, file_path: str, duplicate_strategy: str = "skip") -> dict:
        """Import tasks from a JSON file with validation.

        Args:
            file_path: Path to the JSON file to import from.
            duplicate_strategy: How to handle duplicate task IDs.
                - "skip": Keep existing task, ignore imported one (default).
                - "replace": Replace existing task with imported one.

        Returns:
            dict: Result dictionary with keys:
                - imported_count: Number of tasks successfully imported.
                - skipped_count: Number of duplicate tasks skipped.
                - errors: List of error messages for invalid entries.

        Raises:
            ValueError: If duplicate_strategy is invalid.
        """
        if duplicate_strategy not in ("skip", "replace"):
            raise ValueError("duplicate_strategy must be 'skip' or 'replace'")

        validator = ImportValidator()
        validated_tasks, validation_errors = validator.validate_file(file_path)

        result = {
            "imported_count": 0,
            "skipped_count": 0,
            "errors": validation_errors,
        }

        if not validated_tasks:
            return result

        # Get existing task IDs for duplicate checking
        existing_tasks = self.list_tasks()
        existing_ids = {t.id for t in existing_tasks}

        # Import validated tasks
        for task_dict in validated_tasks:
            task_id = task_dict["id"]
            is_duplicate = task_id in existing_ids

            if is_duplicate and duplicate_strategy == "skip":
                result["skipped_count"] += 1
                continue

            try:
                # Filter out empty comments before reconstructing task
                task_dict_copy = task_dict.copy()
                if "comments" in task_dict_copy and task_dict_copy["comments"]:
                    filtered_comments = [
                        c for c in task_dict_copy["comments"]
                        if c.get("content") and c.get("content").strip()
                    ]
                    task_dict_copy["comments"] = filtered_comments

                # Reconstruct task from dict and add/update
                task = Task.from_dict(task_dict_copy)
                self._manager.set_task(task_id, task)

                if is_duplicate and duplicate_strategy == "replace":
                    # Counted as skipped when replacing
                    result["skipped_count"] += 1
                else:
                    result["imported_count"] += 1
                existing_ids.add(task_id)
            except Exception as e:
                result["errors"].append({"id": task_id, "error": f"Failed to import: {e}"})

        return result
