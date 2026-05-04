from datetime import datetime
from statistics import mean
from typing import Optional, Tuple, Union

from ..models.project import Project
from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..models.task_summary_report import TaskSummaryReport
from ..storage.json_storage import JsonStorage
from ..storage.project_storage import ProjectStorage
from ..utils.datetime_utils import parse_datetime_or_iso_string
from .comments_service import CommentsService
from .import_export_service import ImportExportService
from .project_manager import ProjectManager
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comments_service = CommentsService(self._manager)
        self._project_manager = ProjectManager(ProjectStorage())

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None, project_id: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description, due_date, project_id)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[Union[datetime, str]] = None,
        due_after: Optional[Union[datetime, str]] = None,
        overdue_only: bool = False,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        """
        List tasks with optional filtering by status, due date, overdue status, and project.

        Args:
            status: Filter by TaskStatus, or None for all statuses
            due_before: Filter to tasks due on or before this date, or None (accepts datetime or ISO string)
            due_after: Filter to tasks due on or after this date, or None (accepts datetime or ISO string)
            overdue_only: If True, only return overdue tasks
            project_id: Filter by project_id, or None for all projects

        Returns:
            Sorted list of tasks matching all filters
        """
        # Parse date strings to datetime
        parsed_due_before = None
        if due_before is not None:
            parsed_due_before = parse_datetime_or_iso_string(due_before) if isinstance(due_before, str) else due_before

        parsed_due_after = None
        if due_after is not None:
            parsed_due_after = parse_datetime_or_iso_string(due_after) if isinstance(due_after, str) else due_after

        return self._manager.list_by_project_with_filters(
            project_id=project_id,
            status=status,
            due_before=parsed_due_before,
            due_after=parsed_due_after,
            overdue_only=overdue_only,
        )

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def delete_task(self, task_id: str) -> None:
        # Cascade delete: remove all associated comments first
        self._comments_service.delete_by_task(task_id)
        self._manager.delete(task_id)

    def mark_in_progress(self, task_id: str) -> Task:
        """Mark task as in-progress and persist."""
        task = self._manager.get(task_id)
        task.mark_in_progress()
        self._manager._persist()
        return task

    def mark_done(self, task_id: str) -> Task:
        """Mark task as done and persist."""
        task = self._manager.get(task_id)
        task.mark_done()
        self._manager._persist()
        return task

    def reopen(self, task_id: str) -> Task:
        """Reopen task (transition to PENDING) and persist."""
        task = self._manager.get(task_id)
        task.reopen()
        self._manager._persist()
        return task

    def is_pending(self, task_id: str) -> bool:
        """Check if task is pending."""
        return self._manager.get(task_id).is_pending()

    def is_in_progress(self, task_id: str) -> bool:
        """Check if task is in progress."""
        return self._manager.get(task_id).is_in_progress()

    def is_completed(self, task_id: str) -> bool:
        """Check if task is completed."""
        return self._manager.get(task_id).is_completed()

    def is_overdue(self, task_id: str) -> bool:
        """Check if task is overdue."""
        return self._manager.get(task_id).is_overdue()

    # ── Comment management ─────────────────────────────────────────────────

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        return self._comments_service.add(task_id, content)

    def get_comment(self, comment_id: str) -> TaskComment:
        return self._comments_service.get(comment_id)

    def list_task_comments(self, task_id: str) -> list[TaskComment]:
        return self._comments_service.list_by_task(task_id)

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        return self._comments_service.update(comment_id, content)

    def delete_comment(self, comment_id: str) -> None:
        self._comments_service.delete(comment_id)

    # ── Project management ────────────────────────────────────────────────

    def add_project(self, name: str, description: Optional[str] = None) -> Project:
        """Add a new project."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        return self._project_manager.add(name.strip(), description)

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID (supports prefix matching)."""
        return self._project_manager.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return self._project_manager.list_all()

    def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Project:
        """Update a project's name and/or description."""
        return self._project_manager.update(project_id, name, description)

    def delete_project(self, project_id: str) -> None:
        """Delete a project and unassign all its tasks."""
        # Cascade: unassign all tasks from this project
        self._manager.unassign_project(project_id)
        self._project_manager.delete(project_id)

    def generate_summary_report(self) -> TaskSummaryReport:
        """
        Generate a summary report of all tasks with statistics.

        Returns:
            TaskSummaryReport with counts and completion metrics
        """
        all_tasks = self._manager.list_all()

        # Count tasks by status
        total_count = len(all_tasks)
        pending_count = sum(1 for t in all_tasks if t.status == TaskStatus.PENDING)
        in_progress_count = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
        done_count = sum(1 for t in all_tasks if t.status == TaskStatus.DONE)

        # Count overdue tasks
        overdue_count = sum(1 for t in all_tasks if t.is_overdue())

        # Count tasks with due_date
        with_due_date_count = sum(1 for t in all_tasks if t.due_date is not None)

        # Calculate completion rate
        completion_rate_percent = (done_count / total_count * 100) if total_count > 0 else 0.0

        # Calculate average days to completion for DONE tasks
        average_days_to_completion: Optional[float] = None
        done_tasks = [t for t in all_tasks if t.status == TaskStatus.DONE]
        if done_tasks:
            days_list = [(t.updated_at - t.created_at).days for t in done_tasks]
            average_days_to_completion = mean(days_list) if days_list else None

        return TaskSummaryReport(
            total_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
            completion_rate_percent=completion_rate_percent,
            average_days_to_completion=average_days_to_completion,
        )

    # ── Import/Export ─────────────────────────────────────────────────

    def export_to_json(self, file_path: str) -> int:
        """
        Export all tasks and comments to JSON file.

        Args:
            file_path: Path to the JSON file to write

        Returns:
            int: Number of tasks exported
        """
        service = ImportExportService(self._manager, self._comments_service)
        return service.export_to_json(file_path)

    def import_from_json(
        self, file_path: str, merge_mode: str = "skip"
    ) -> Tuple[int, int, int, int]:
        """
        Import tasks and comments from JSON file.

        Args:
            file_path: Path to the JSON file to read
            merge_mode: "skip" (default) or "overwrite"

        Returns:
            Tuple: (tasks_imported, tasks_skipped, comments_imported, comments_skipped)
        """
        service = ImportExportService(self._manager, self._comments_service)
        return service.import_from_json(file_path, merge_mode)
