from ..models.task import Task
from ..models.task_status import TaskStatus


class TaskFormatter:
    """Formatter for task display and status symbols."""

    STATUS_SYMBOLS = {
        TaskStatus.PENDING: "[ ]",
        TaskStatus.IN_PROGRESS: "[~]",
        TaskStatus.DONE: "[x]",
    }

    STATUS_NAMES = {
        TaskStatus.PENDING: "pending",
        TaskStatus.IN_PROGRESS: "in progress",
        TaskStatus.DONE: "done",
    }

    @classmethod
    def get_status_symbol(cls, status: TaskStatus) -> str:
        """Get the display symbol for a task status.

        Args:
            status: The TaskStatus enum value

        Returns:
            Display symbol string (e.g., "[ ]" for PENDING)
        """
        return cls.STATUS_SYMBOLS.get(status, "[ ]")

    @classmethod
    def get_status_name(cls, status: TaskStatus) -> str:
        """Get the human-readable name for a task status.

        Args:
            status: The TaskStatus enum value

        Returns:
            Status name string (e.g., "pending" for PENDING)
        """
        return cls.STATUS_NAMES.get(status, "unknown")

    @classmethod
    def format_task_line(cls, task: Task, show_project: bool = False) -> str:
        """Format a task as a single line for display.

        Args:
            task: The task to format
            show_project: Whether to include project ID in the line

        Returns:
            Formatted task line string
        """
        symbol = cls.get_status_symbol(task.status)
        line = f"{symbol} {task.id[:8]}  {task.title}"
        if show_project and task.project_id:
            line += f" [{task.project_id[:8]}]"
        return line
