from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TaskSummaryReport:
    """Frozen dataclass containing task summary statistics."""

    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    with_due_date_count: int
    completion_rate_percent: float
    average_days_to_completion: Optional[float]

    def __str__(self) -> str:
        """Return human-readable formatted output."""
        lines = [
            f"Total tasks:                {self.total_count}",
            f"Pending:                    {self.pending_count}",
            f"In progress:                {self.in_progress_count}",
            f"Done:                       {self.done_count}",
            f"Overdue:                    {self.overdue_count}",
            f"With due date:              {self.with_due_date_count}",
            f"Completion rate:            {self.completion_rate_percent:.1f}%",
        ]
        if self.average_days_to_completion is not None:
            lines.append(f"Average days to completion: {self.average_days_to_completion:.1f}")
        else:
            lines.append("Average days to completion: —")
        return "\n".join(lines)
