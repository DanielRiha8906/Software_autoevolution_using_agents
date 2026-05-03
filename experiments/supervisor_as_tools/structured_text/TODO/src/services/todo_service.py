from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_statistics import TaskStatistics
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .comments_service import CommentsService
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        storage = storage or JsonStorage()
        self._manager = TaskManager(storage)
        self._comments_service = CommentsService(storage, self._manager)
        # Now set the comments_service on the manager for cascade deletes
        self._manager._comments_service = self._comments_service

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
        overdue: bool = False,
    ) -> list[Task]:
        """List tasks with optional filtering.

        Args:
            status: Optional status filter.
            due_before: Optional upper bound for due_date (inclusive).
            due_after: Optional lower bound for due_date (inclusive).
            overdue: If True, return only overdue tasks, ignoring due_before/due_after.

        Returns:
            Filtered list of tasks.
        """
        if overdue:
            return self._manager.list_overdue(status)
        elif due_before is not None or due_after is not None:
            return self._manager.list_by_due_date_range(due_after, due_before, status)
        elif status is not None:
            return self._manager.list_by_status(status)
        else:
            return self._manager.list_all()

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

    def set_due_date(self, task_id: str, due_date: Optional[datetime] = None) -> Task:
        return self._manager.set_due_date(task_id, due_date)

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        return self._comments_service.add_comment(task_id, content)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        return self._comments_service.list_comments(task_id)

    def delete_comment(self, comment_id: str) -> None:
        self._comments_service.delete_comment(comment_id)

    def get_statistics(self) -> TaskStatistics:
        """Calculate and return statistics about all tasks.

        Returns:
            TaskStatistics with task counts, completion rate, and average days to completion.
        """
        all_tasks = self._manager.list_all()
        total_count = len(all_tasks)

        # Count tasks by status
        pending_count = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        in_progress_count = len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS])
        done_count = len([t for t in all_tasks if t.status == TaskStatus.DONE])

        # Count overdue tasks
        overdue_count = len([t for t in all_tasks if t.is_overdue()])

        # Count tasks with due date
        tasks_with_due_date = len([t for t in all_tasks if t.due_date is not None])

        # Compute completion rate
        completion_rate = (done_count / total_count * 100) if total_count > 0 else 0
        completion_rate = round(completion_rate, 1)

        # Compute average days to completion for done tasks
        done_tasks = [t for t in all_tasks if t.status == TaskStatus.DONE]
        if done_tasks:
            total_days = sum((t.updated_at - t.created_at).days for t in done_tasks)
            avg_days_to_completion = round(total_days / len(done_tasks), 1)
        else:
            avg_days_to_completion = None

        return TaskStatistics(
            total_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            tasks_with_due_date=tasks_with_due_date,
            completion_rate=completion_rate,
            avg_days_to_completion=avg_days_to_completion,
        )
