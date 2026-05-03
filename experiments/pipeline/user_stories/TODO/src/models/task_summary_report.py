from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TaskSummaryReport:
    """Summary report of task statistics.

    This dataclass provides aggregate statistics about tasks including counts
    by status, completion metrics, and average time to completion.

    Attributes:
        total_count: Total number of tasks.
        pending_count: Number of tasks in PENDING status.
        in_progress_count: Number of tasks in IN_PROGRESS status.
        done_count: Number of tasks in DONE status.
        overdue_count: Number of tasks that are overdue.
        due_date_set_count: Number of tasks with a due date set.
        completion_rate: Fraction of tasks completed (0.0 to 1.0).
        avg_days_to_completion: Average days from creation to completion for done tasks.
    """

    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    due_date_set_count: int
    completion_rate: float
    avg_days_to_completion: Optional[float] = None
