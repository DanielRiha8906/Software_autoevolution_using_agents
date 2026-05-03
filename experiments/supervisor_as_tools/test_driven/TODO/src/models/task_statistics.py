from dataclasses import dataclass

from .task_status import TaskStatus


@dataclass
class TaskStatistics:
    total: int
    count_per_status: dict[TaskStatus, int]
    overdue_count: int
    with_due_date_count: int
    completion_rate: float
