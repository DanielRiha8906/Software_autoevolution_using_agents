from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.task_comment import TaskComment
from ..models.task_summary_report import TaskSummaryReport
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

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
        week_start, week_end = self._manager._get_week_boundaries(year, week)
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
        month_start, month_end = self._manager._get_month_boundaries(year, month)
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
        year_start, year_end = self._manager._get_year_boundaries(year)
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
