"""Task display formatting for the GUI."""

from ..models.task import Task
from ..models.task_status import TaskStatus


class TaskRow:
    """Wraps a Task and provides formatted display for treeview."""

    def __init__(self, task: Task, project_name: str = "") -> None:
        """Initialize TaskRow.

        Args:
            task: The Task model to wrap.
            project_name: The project name (empty string if no project).
        """
        self.task = task
        self.project_name = project_name

    def format_for_treeview(self) -> tuple[str, ...]:
        """Format task data for treeview display.

        Returns:
            Tuple of (status_symbol, title, due_date_str, project_name, task_id).
        """
        # Status symbol
        status_symbols = {
            TaskStatus.PENDING: "[ ]",
            TaskStatus.IN_PROGRESS: "[~]",
            TaskStatus.DONE: "[x]",
        }
        status_symbol = status_symbols[self.task.status]

        # Due date string
        if self.task.due_date:
            due_date_str = self.task.due_date.strftime("%Y-%m-%d")
        else:
            due_date_str = "No due date"

        return (
            status_symbol,
            self.task.title,
            due_date_str,
            self.project_name,
            self.task.id,
        )

    def get_tag(self) -> str:
        """Get the tag for this task row (for styling).

        Returns:
            "overdue" if task is overdue, "normal" otherwise.
        """
        if self.task.is_overdue():
            return "overdue"
        return "normal"
