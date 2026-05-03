from dataclasses import dataclass


@dataclass
class TaskStatistics:
    """Aggregate statistics about tasks in the TODO application.

    Attributes:
        total_count: Total number of tasks
        pending_count: Number of pending tasks
        in_progress_count: Number of in-progress tasks
        done_count: Number of completed tasks
        overdue_count: Number of overdue (active) tasks
        with_due_date_count: Number of tasks with a due date set
    """
    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    with_due_date_count: int
