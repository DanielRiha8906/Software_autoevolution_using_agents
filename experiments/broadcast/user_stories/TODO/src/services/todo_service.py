from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..models.task_summary import TaskSummary
from ..models.filter_options import FilterOptions
from ..models.project import Project
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager
from .comments_service import CommentsService
from .project_manager import ProjectManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comments_service = CommentsService(self._manager, storage)
        self._project_manager = ProjectManager(storage)

    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        overdue: Optional[bool] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> list[Task]:
        """
        List tasks with optional filtering by status, due date range, and overdue status.

        Args:
            status: Filter by task status
            due_before: Filter tasks with due date before this datetime (preferred name)
            due_after: Filter tasks with due date after this datetime (preferred name)
            before: Alias for due_before (deprecated, use due_before)
            after: Alias for due_after (deprecated, use due_after)
            overdue: If True, only return overdue tasks. If False, only return non-overdue tasks.

        Returns:
            Filtered list of tasks
        """
        # Support both naming conventions
        _due_before = due_before or before
        _due_after = due_after or after

        # Build FilterOptions
        options = FilterOptions(
            status=status,
            due_before=_due_before,
            due_after=_due_after,
            overdue_only=(overdue is True),
        )

        # Get filtered tasks
        tasks = self._manager.apply_filters(options)

        # If overdue is explicitly False, exclude overdue tasks
        if overdue is False:
            tasks = [t for t in tasks if not t.is_overdue()]

        return tasks

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)

    def is_task_pending(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_pending()

    def is_task_in_progress(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_in_progress()

    def is_task_completed(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_completed()

    def is_task_overdue(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_overdue()

    # Comment management methods
    def add_comment(
        self, task_id: str, content: str, author: Optional[str] = None
    ) -> TaskComment:
        """Add a comment to a task."""
        return self._comments_service.add_comment(task_id, content, author)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task (ordered by created_at)."""
        return self._comments_service.list_comments_for_task(task_id)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a specific comment by id."""
        return self._comments_service.get_comment(comment_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by id."""
        self._comments_service.delete_comment(comment_id)

    def edit_comment(self, comment_id: str, content: str) -> TaskComment:
        """Edit a comment's content."""
        return self._comments_service.edit_comment(comment_id, content)

    # Project management methods
    def create_project(self, name: str) -> Project:
        """Create a new project."""
        return self._project_manager.add(name)

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID."""
        return self._project_manager.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return self._project_manager.list_all()

    def update_project(self, project_id: str, name: str) -> Project:
        """Update a project's name."""
        return self._project_manager.update(project_id, name)

    def delete_project(self, project_id: str) -> None:
        """Delete a project (tasks remain unassigned)."""
        # Unassign all tasks in this project
        tasks_in_project = self._manager.list_by_project(project_id)
        for task in tasks_in_project:
            task.project_id = None
        if tasks_in_project:
            self._manager._persist()
        # Delete the project itself
        self._project_manager.delete(project_id)

    def list_tasks_by_project(self, project_id: str) -> list[Task]:
        """List all tasks in a specific project."""
        # Verify the project exists
        self._project_manager.get(project_id)
        # Return tasks with this project_id
        return [t for t in self._manager.list_all() if t.project_id == project_id]

    def list_unassigned_tasks(self) -> list[Task]:
        """List all tasks not assigned to any project."""
        return [t for t in self._manager.list_all() if t.project_id is None]

    def assign_task_to_project(self, task_id: str, project_id: str) -> Task:
        """Assign a task to a project."""
        # Verify the project exists
        self._project_manager.get(project_id)
        # Get the task and update its project_id
        task = self._manager.get(task_id)
        task.project_id = project_id
        self._manager._persist()
        return task

    def unassign_task_from_project(self, task_id: str) -> Task:
        """Remove a task from its project."""
        task = self._manager.get(task_id)
        task.project_id = None
        self._manager._persist()
        return task

    def generate_report(self) -> TaskSummary:
        """Generate a summary report of all tasks."""
        all_tasks = self._manager.list_all()

        total_tasks = len(all_tasks)
        pending_count = sum(1 for t in all_tasks if t.status == TaskStatus.PENDING)
        in_progress_count = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
        done_count = sum(1 for t in all_tasks if t.status == TaskStatus.DONE)
        overdue_count = sum(1 for t in all_tasks if t.is_overdue())
        with_due_date_count = sum(1 for t in all_tasks if t.due_date is not None)

        # Calculate completion rate (percentage of done tasks)
        completion_rate = (done_count / total_tasks * 100) if total_tasks > 0 else 0.0

        # Calculate average days to completion for done tasks
        avg_days_to_completion = None
        if done_count > 0:
            total_days = 0
            for task in all_tasks:
                if task.status == TaskStatus.DONE:
                    days_elapsed = (task.updated_at - task.created_at).total_seconds() / 86400
                    total_days += days_elapsed
            avg_days_to_completion = round(total_days / done_count, 2)

        return TaskSummary(
            total_tasks=total_tasks,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
            completion_rate=completion_rate,
            avg_days_to_completion=avg_days_to_completion,
        )
