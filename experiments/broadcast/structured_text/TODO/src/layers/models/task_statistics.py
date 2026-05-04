"""Task statistics model."""

from dataclasses import dataclass


@dataclass
class TaskStatistics:
    """Statistics report for tasks."""

    total_task_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    tasks_with_due_date_count: int
    completion_rate: float

    def __post_init__(self) -> None:
        """Validate statistics are non-negative."""
        if self.total_task_count < 0:
            raise ValueError("total_task_count cannot be negative")
        if self.pending_count < 0:
            raise ValueError("pending_count cannot be negative")
        if self.in_progress_count < 0:
            raise ValueError("in_progress_count cannot be negative")
        if self.done_count < 0:
            raise ValueError("done_count cannot be negative")
        if self.overdue_count < 0:
            raise ValueError("overdue_count cannot be negative")
        if self.tasks_with_due_date_count < 0:
            raise ValueError("tasks_with_due_date_count cannot be negative")
        if not 0.0 <= self.completion_rate <= 1.0:
            raise ValueError("completion_rate must be between 0.0 and 1.0")
