"""Comment repository layer - isolates comment persistence from business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable

from ..models.task_comment import TaskComment

if TYPE_CHECKING:
    from ..protocols import CommentRepository as CommentRepositoryProtocol


class CommentNotFoundError(Exception):
    """Raised when a comment cannot be found."""
    pass


class CommentRepository:
    """
    Repository for comment persistence and retrieval.

    Isolates comment storage operations from business logic. Implements the Repository pattern
    to provide a collection-like interface to comment storage.
    """

    def __init__(self, storage_backend: CommentRepositoryProtocol) -> None:
        """
        Initialize the comment repository.

        Args:
            storage_backend: Storage backend implementing CommentRepository protocol
        """
        self._storage = storage_backend
        self._comments: dict[str, TaskComment] = {}
        self._on_cascade_delete: Optional[Callable[[str], None]] = None
        self._load()

    def _load(self) -> None:
        """Load all comments from storage backend."""
        raw_comments = self._storage.load_comments()
        # Convert dicts to TaskComment objects if necessary
        comments = []
        for c in raw_comments:
            if isinstance(c, dict):
                comments.append(TaskComment.from_dict(c))
            else:
                comments.append(c)
        self._comments = {c.id: c for c in comments}

    def _persist(self) -> None:
        """Persist all comments to storage backend."""
        self._storage.save_comments(list(self._comments.values()))

    def set_cascade_delete_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for cascade delete when a task is deleted."""
        self._on_cascade_delete = callback

    def add(self, comment: TaskComment) -> TaskComment:
        """
        Add a comment to the repository.

        Args:
            comment: Comment to add

        Returns:
            The added comment
        """
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        """
        Get a comment by ID, supporting prefix lookup.

        Args:
            comment_id: Comment ID or unique prefix

        Returns:
            The comment

        Raises:
            CommentNotFoundError: If comment not found
        """
        if comment_id in self._comments:
            return self._comments[comment_id]
        # Support short prefix lookup
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(
                f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments"
            )
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def get_all(self) -> list[TaskComment]:
        """Get all comments."""
        return list(self._comments.values())

    def get_by_task(self, task_id: str) -> list[TaskComment]:
        """
        Get all comments for a task, ordered by created_at.

        Args:
            task_id: The task ID

        Returns:
            List of comments ordered by created_at
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def update(self, comment: TaskComment) -> TaskComment:
        """
        Update a comment in the repository.

        Args:
            comment: Comment with updated values (must have existing id)

        Returns:
            The updated comment
        """
        if comment.id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment.id}' not found")
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def delete(self, comment_id: str) -> TaskComment:
        """
        Delete a comment from the repository.

        Args:
            comment_id: Comment ID or prefix

        Returns:
            The deleted comment

        Raises:
            CommentNotFoundError: If comment not found
        """
        comment = self.get(comment_id)  # Resolves prefix
        del self._comments[comment.id]
        self._persist()
        return comment

    def delete_by_task(self, task_id: str) -> None:
        """
        Delete all comments for a task (cascade operation).

        Args:
            task_id: The task ID
        """
        self._comments = {
            cid: c for cid, c in self._comments.items() if c.task_id != task_id
        }
        self._persist()


__all__ = ["CommentRepository", "CommentNotFoundError"]
