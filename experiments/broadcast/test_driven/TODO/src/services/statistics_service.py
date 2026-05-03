from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from ..models.task_status import TaskStatus
from .todo_service import TodoService

CEST = timezone(timedelta(hours=2))


@dataclass
class TaskStatisticsReport:
    total: int
    count_per_status: dict[TaskStatus, int]
    overdue_count: int
    with_due_date_count: int
    completion_rate: float


class TaskStatisticsService:
    def __init__(self, todo_service: TodoService) -> None:
        self._todo_service = todo_service

    def compute(self) -> TaskStatisticsReport:
        all_tasks = self._todo_service.list_tasks()

        total = len(all_tasks)

        # Count tasks per status
        count_per_status = {
            TaskStatus.PENDING: 0,
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.DONE: 0,
        }
        for task in all_tasks:
            count_per_status[task.status] += 1

        # Count overdue tasks
        overdue_count = sum(1 for task in all_tasks if task.is_overdue())

        # Count tasks with due date
        with_due_date_count = sum(1 for task in all_tasks if task.due_date is not None)

        # Calculate completion rate
        if total == 0:
            completion_rate = 0.0
        else:
            completion_rate = (count_per_status[TaskStatus.DONE] / total) * 100.0

        return TaskStatisticsReport(
            total=total,
            count_per_status=count_per_status,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
            completion_rate=completion_rate,
        )
