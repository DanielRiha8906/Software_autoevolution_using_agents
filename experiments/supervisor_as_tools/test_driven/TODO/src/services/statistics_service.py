from ..models.task_status import TaskStatus
from ..models.task_statistics import TaskStatistics
from .todo_service import TodoService


class TaskStatisticsService:
    def __init__(self, todo_service: TodoService) -> None:
        self._service = todo_service

    def compute(self) -> TaskStatistics:
        """Compute statistics from all tasks in a single pass."""
        tasks = self._service.list_tasks()

        total = len(tasks)
        done_count = 0
        overdue_count = 0
        with_due_date_count = 0
        count_per_status = {
            TaskStatus.PENDING: 0,
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.DONE: 0,
        }

        for task in tasks:
            # Count by status
            count_per_status[task.status] += 1

            # Count completed tasks
            if task.is_completed():
                done_count += 1

            # Count overdue tasks
            if task.is_overdue():
                overdue_count += 1

            # Count tasks with due date
            if task.due_date is not None:
                with_due_date_count += 1

        # Calculate completion rate
        completion_rate = (done_count / total * 100) if total > 0 else 0.0

        return TaskStatistics(
            total=total,
            count_per_status=count_per_status,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
            completion_rate=completion_rate,
        )
