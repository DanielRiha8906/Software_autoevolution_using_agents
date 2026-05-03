from typing import Optional

from ..models.task_statistics import TaskStatistics
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class StatisticsService:
    """Service for computing task statistics."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage or JsonStorage())

    def compute_statistics(self) -> TaskStatistics:
        """Compute statistics for all tasks.

        Returns:
            TaskStatistics with counts and completion rate
        """
        tasks = self._manager.list_all()

        total_count = len(tasks)
        pending_count = len(self._manager.list_by_status(TaskStatus.PENDING))
        in_progress_count = len(self._manager.list_by_status(TaskStatus.IN_PROGRESS))
        done_count = len(self._manager.list_by_status(TaskStatus.DONE))
        overdue_count = len(self._manager.list_overdue())
        tasks_with_due_date_count = sum(1 for task in tasks if task.due_date is not None)

        # Calculate completion rate
        completion_rate = 0.0
        if total_count > 0:
            completion_rate = done_count / total_count

        return TaskStatistics(
            total_task_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            tasks_with_due_date_count=tasks_with_due_date_count,
            completion_rate=completion_rate,
        )
