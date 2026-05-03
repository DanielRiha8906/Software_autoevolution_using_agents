from datetime import datetime, timezone
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager, TaskNotFoundError


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    """Service for managing TaskComment objects with full lifecycle support."""

    def __init__(
        self, task_manager: TaskManager, storage: Optional[JsonStorage] = None
    ) -> None:
        self._task_manager = task_manager
        self._storage = storage or JsonStorage()
        self._comments: dict[str, TaskComment] = {}
        self._load()
        # Register callback for cascade delete
        self._task_manager.set_on_delete_callback(self._delete_comments_for_task)

    def _load(self) -> None:
        """Load comments from storage."""
        raw = self._storage.load_comments()
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in raw}

    def _persist(self) -> None:
        """Persist both tasks and comments to storage."""
        tasks_raw = [t.to_dict() for t in self._task_manager.list_all()]
        comments_raw = [c.to_dict() for c in self._comments.values()]
        self._storage.save_all(tasks_raw, comments_raw)

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
        self._comments[comment.id] = comment
        self._persist()
        return comment

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
        if comment_id in self._comments:
            return self._comments[comment_id]
        # Support short prefix lookup (e.g. first 8 chars shown by list)
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(
                f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments"
            )
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

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

        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment (supports prefix lookup)

        Raises:
            CommentNotFoundError: If the comment does not exist
        """
        comment = self.get_comment(comment_id)  # resolves prefix; raises if missing
        del self._comments[comment.id]
        self._persist()

    def _delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task (called on task deletion for cascade).

        Args:
            task_id: The ID of the task
        """
        self._comments = {
            cid: c for cid, c in self._comments.items() if c.task_id != task_id
        }
        self._persist()

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
        comment = self.get_comment(comment_id)  # resolves prefix; raises if missing

        # Validate content
        if not content or not content.strip():
            raise ValueError("content cannot be empty or whitespace-only")

        comment.content = content.strip()
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment
