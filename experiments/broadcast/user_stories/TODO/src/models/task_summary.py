from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskSummary:
    """Summary statistics for all tasks."""

    total_tasks: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    with_due_date_count: int
    completion_rate: float
    avg_days_to_completion: Optional[float]
