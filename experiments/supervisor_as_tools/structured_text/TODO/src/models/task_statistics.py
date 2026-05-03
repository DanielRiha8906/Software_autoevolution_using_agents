from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskStatistics:
    """Statistics about the task collection."""

    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    tasks_with_due_date: int
    completion_rate: float
    avg_days_to_completion: Optional[float]
