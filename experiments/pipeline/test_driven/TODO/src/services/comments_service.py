from ..models.task_comment import TaskComment
from .task_manager import TaskNotFoundError
from .todo_service import TodoService


class CommentNotFoundError(Exception):
    """Raised when a comment is not found."""
    pass


class CommentsService:
    """Service for managing task comments."""

    def __init__(self, todo_service: TodoService) -> None:
        """Initialize CommentsService with a TodoService instance.

        Args:
            todo_service: TodoService instance for task validation.
        """
        self._todo_service = todo_service
        self._comments: dict[str, TaskComment] = {}

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: ID of the task to comment on.
            content: Comment content (must be non-empty).

        Returns:
            The created TaskComment instance.

        Raises:
            TaskNotFoundError: If the task does not exist.
            ValueError: If content is empty or invalid (via TaskComment validation).
        """
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Create comment (TaskComment validates content non-empty)
        comment = TaskComment(task_id=task_id, content=content)

        # Store in memory
        self._comments[comment.id] = comment

        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by creation time.

        Args:
            task_id: ID of the task.

        Returns:
            List of TaskComment objects sorted by created_at ascending.
        """
        matching = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(matching, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: ID of the comment to delete.

        Raises:
            CommentNotFoundError: If the comment does not exist.
        """
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        del self._comments[comment_id]

    def delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task (cascade delete).

        Args:
            task_id: ID of the task.
        """
        ids_to_delete = [cid for cid, c in self._comments.items() if c.task_id == task_id]
        for comment_id in ids_to_delete:
            del self._comments[comment_id]
