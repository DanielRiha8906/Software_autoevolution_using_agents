from datetime import datetime, timezone
from uuid import uuid4

from ..models.task_comment import TaskComment
from .task_manager import TaskManager, TaskNotFoundError


class CommentsService:
    """Service for managing task comments.

    Centralizes all comment lifecycle operations: create, retrieve, update, and delete.
    Depends on TaskManager for task validation and persistence.
    Comments are stored as nested objects within Task entities.
    """

    def __init__(self, task_manager: TaskManager) -> None:
        """Initialize CommentsService with a TaskManager instance.

        Args:
            task_manager: TaskManager instance for task access and persistence
        """
        self._task_manager = task_manager

    def add_comment(self, task_id: str, content: str, author: str | None = None) -> TaskComment:
        """Create and append a comment to a task.

        Args:
            task_id: ID of the task to comment on
            content: Text content of the comment (must be non-empty after stripping)
            author: Optional author identifier

        Returns:
            The created TaskComment object

        Raises:
            ValueError: If content is empty or only whitespace
            TaskNotFoundError: If task does not exist
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        task = self._task_manager.get(task_id)
        comment = TaskComment(
            task_id=task.id,
            content=content.strip(),
            author=author,
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
        )
        task.comments.append(comment)
        self._task_manager._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task.

        Args:
            task_id: ID of the task

        Returns:
            List of TaskComment objects for the task (in creation order)

        Raises:
            TaskNotFoundError: If task does not exist
        """
        task = self._task_manager.get(task_id)
        return task.comments

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a comment from a task.

        Args:
            task_id: ID of the task
            comment_id: ID of the comment to delete

        Raises:
            TaskNotFoundError: If task does not exist
            ValueError: If comment does not exist on the task
        """
        task = self._task_manager.get(task_id)
        for i, comment in enumerate(task.comments):
            if comment.id == comment_id:
                task.comments.pop(i)
                self._task_manager._persist()
                return
        raise ValueError(f"Comment '{comment_id}' not found on task '{task_id}'")

    def edit_comment(self, task_id: str, comment_id: str, new_content: str) -> TaskComment:
        """Edit the content of a comment.

        Args:
            task_id: ID of the task
            comment_id: ID of the comment to edit
            new_content: New text content for the comment (must be non-empty after stripping)

        Returns:
            The updated TaskComment object

        Raises:
            ValueError: If new_content is empty or only whitespace, or if comment not found
            TaskNotFoundError: If task does not exist
        """
        if not new_content or not new_content.strip():
            raise ValueError("Comment content cannot be empty")

        task = self._task_manager.get(task_id)
        for comment in task.comments:
            if comment.id == comment_id:
                comment.content = new_content.strip()
                comment.updated_at = datetime.now(timezone.utc)
                self._task_manager._persist()
                return comment
        raise ValueError(f"Comment '{comment_id}' not found on task '{task_id}'")
