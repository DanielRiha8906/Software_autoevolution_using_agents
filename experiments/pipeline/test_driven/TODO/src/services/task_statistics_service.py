from dataclasses import dataclass

from ..models.task_status import TaskStatus
from .todo_service import TodoService


@dataclass
class TaskStatistics:
    """Statistics snapshot of task data."""
    total: int
    count_per_status: dict  # Maps TaskStatus to count
    overdue_count: int
    with_due_date_count: int
    completion_rate: float  # 0-100 percentage


class TaskStatisticsService:
    def __init__(self, todo_service: TodoService) -> None:
        """Initialize with a TodoService instance."""
        self._service = todo_service

    def compute(self) -> TaskStatistics:
        """
        Compute and return statistics for all tasks.

        Returns:
            TaskStatistics object with computed fields.
        """
        # Get all tasks
        all_tasks = self._service.list_tasks()
        total = len(all_tasks)

        # Count per status
        count_per_status = {
            TaskStatus.PENDING: 0,
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.DONE: 0,
        }
        for task in all_tasks:
            count_per_status[task.status] += 1

        # Overdue count
        overdue_count = len(self._service.list_tasks(overdue=True))

        # Count tasks with due date
        with_due_date_count = sum(1 for task in all_tasks if task.due_date is not None)

        # Completion rate (percentage)
        completion_rate = (count_per_status[TaskStatus.DONE] / total * 100) if total > 0 else 0.0

        return TaskStatistics(
            total=total,
            count_per_status=count_per_status,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
            completion_rate=completion_rate,
        )
