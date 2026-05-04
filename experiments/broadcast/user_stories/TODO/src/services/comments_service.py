"""Comments management service - business logic layer."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, Any

from ..models.task_comment import TaskComment
from .task_manager import TaskManager, TaskNotFoundError

if TYPE_CHECKING:
    pass


class CommentNotFoundError(Exception):
    """Raised when a comment cannot be found."""
    pass


class CommentsService:
    """
    Business logic layer for comment management.

    Encapsulates comment-related operations using the comment repository for persistence.
    Handles task validation and cascade deletes.

    Can accept either a CommentRepository (preferred) or JsonStorage (backward compatible).
    """

    def __init__(
        self, task_manager: TaskManager, comment_repository: Any
    ) -> None:
        """
        Initialize CommentsService.

        Args:
            task_manager: TaskManager for task validation
            comment_repository: CommentRepository instance OR JsonStorage for backward compatibility
        """
        self._task_manager = task_manager
        # Backward compatibility: if given JsonStorage, wrap it in a CommentRepository
        if hasattr(comment_repository, 'load') and hasattr(comment_repository, 'save') and not hasattr(comment_repository, 'add'):
            from ..comment_domain import CommentRepositoryImpl
            self._repository = CommentRepositoryImpl(comment_repository)
        else:
            self._repository = comment_repository
        # Register callback for cascade delete
        self._repository.set_cascade_delete_callback(self._delete_comments_for_task)
        self._task_manager.set_on_delete_callback(self._delete_comments_for_task)

    # Backward compatibility properties for accessing internals
    @property
    def _comments(self) -> dict:
        """Access internal comments dict (backward compatibility)."""
        return self._repository._comments

    def _persist(self) -> None:
        """Persist comments (backward compatibility)."""
        return self._repository._persist()

    def add_comment(
        self, task_id: str, content: str, author: Optional[str] = None
    ) -> TaskComment:
        """Add a comment to a task.

        Validates that the referenced task exists before adding the comment.

        Args:
            task_id: The ID of the task to comment on
            content: The comment content (cannot be empty or whitespace-only)
            author: Optional author name

        Returns:
            The created TaskComment

        Raises:
            TaskNotFoundError: If the task does not exist
            ValueError: If content is empty
        """
        # Validate that the task exists
        self._task_manager.get(task_id)

        # Create and store the comment
        comment = TaskComment(task_id=task_id, content=content, author=author)
        return self._repository.add(comment)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID.

        Supports prefix lookup for convenience.

        Args:
            comment_id: The ID or unique prefix of the comment

        Returns:
            The TaskComment

        Raises:
            CommentNotFoundError: If the comment does not exist
        """
        from ..comment_domain import CommentNotFoundError as DomainCommentNotFoundError
        try:
            comment = self._repository.get(comment_id)
            return comment
        except DomainCommentNotFoundError as e:
            raise CommentNotFoundError(str(e))

    def list_comments_for_task(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at (ascending).

        Args:
            task_id: The ID of the task

        Returns:
            A list of TaskComment objects ordered by created_at

        Raises:
            TaskNotFoundError: If the task does not exist
        """
        # Validate that the task exists
        self._task_manager.get(task_id)
        return self._repository.get_by_task(task_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment (supports prefix lookup)

        Raises:
            CommentNotFoundError: If the comment does not exist
        """
        from ..comment_domain import CommentNotFoundError as DomainCommentNotFoundError
        try:
            deleted = self._repository.delete(comment_id)
        except DomainCommentNotFoundError as e:
            raise CommentNotFoundError(str(e))

    def _delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task (called on task deletion for cascade).

        Args:
            task_id: The ID of the task
        """
        self._repository.delete_by_task(task_id)

    def edit_comment(self, comment_id: str, content: str) -> TaskComment:
        """Edit a comment's content (bonus feature).

        Updates the updated_at timestamp when content is modified.

        Args:
            comment_id: The ID of the comment (supports prefix lookup)
            content: The new comment content

        Returns:
            The updated TaskComment

        Raises:
            CommentNotFoundError: If the comment does not exist
            ValueError: If content is empty or whitespace-only
        """
        from ..comment_domain import CommentNotFoundError as DomainCommentNotFoundError

        # Validate content
        if not content or not content.strip():
            raise ValueError("content cannot be empty or whitespace-only")

        try:
            comment = self._repository.get(comment_id)
            comment.content = content.strip()
            comment.updated_at = datetime.now(timezone.utc)
            return self._repository.update(comment)
        except DomainCommentNotFoundError as e:
            raise CommentNotFoundError(str(e))
