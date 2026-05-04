from typing import Protocol


class TaskExistenceValidator(Protocol):
    """Protocol for task existence validation."""

    def task_exists(self, task_id: str) -> bool:
        """Check if a task exists.

        Args:
            task_id: The task ID to check.

        Returns:
            True if task exists.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        ...
