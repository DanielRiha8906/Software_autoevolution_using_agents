from typing import Optional

from ..services.task_manager import TaskManager


class TaskRepository:
    """Repository coordinating task and comment operations."""

    def __init__(self, task_manager: TaskManager) -> None:
        """Initialize the repository.

        Args:
            task_manager: The task manager instance.
        """
        self._task_manager = task_manager
        self._comments_service: Optional["CommentsService"] = None  # type: ignore

    def set_comments_service(self, comments_service: "CommentsService") -> None:  # type: ignore
        """Set the comments service for cascade deletes.

        Args:
            comments_service: The comments service instance.
        """
        self._comments_service = comments_service

    def task_exists(self, task_id: str) -> bool:
        """Check if a task exists.

        Args:
            task_id: The task ID to check.

        Returns:
            True if task exists.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        self._task_manager.get(task_id)
        return True

    def delete_task_with_comments(self, task_id: str) -> None:
        """Delete a task and all its comments.

        Args:
            task_id: The task ID to delete.
        """
        task = self._task_manager.get(task_id)
        if self._comments_service is not None:
            self._comments_service.delete_all_for_task(task.id)
        self._task_manager.delete(task.id)
