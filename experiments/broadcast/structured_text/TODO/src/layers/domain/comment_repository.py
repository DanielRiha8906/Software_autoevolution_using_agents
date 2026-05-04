"""Repository for persisting and retrieving task comments."""

from datetime import datetime, timezone
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.protocols import StorageProtocol
from .exceptions import CommentNotFoundError


class CommentRepository:
    """Repository managing comment persistence and retrieval.

    Uses StorageProtocol for abstraction from storage implementation.
    """

    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage."""
        raw = self._storage.load()
        # Filter for comment objects (they have task_id field)
        # We'll store comments in a separate structure
        self._comments = {}
        if isinstance(raw, dict) and "comments" in raw:
            for c in raw.get("comments", []):
                comment = TaskComment.from_dict(c)
                self._comments[comment.id] = comment

    def _persist(self) -> None:
        """Persist comments to storage."""
        raw = self._storage.load()
        # Preserve existing tasks and structure
        if not isinstance(raw, dict):
            raw = {"tasks": raw if raw else []}
        if "tasks" not in raw:
            raw["tasks"] = [t for t in raw] if isinstance(raw, list) else []

        raw["comments"] = [c.to_dict() for c in self._comments.values()]
        self._storage.save(raw)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to add the comment to
            content: The comment content
            author: Optional author name

        Returns:
            The created TaskComment

        Raises:
            ValueError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        comment = TaskComment(
            task_id=task_id,
            content=content.strip(),
            author=author
        )
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments_by_task(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at ascending.

        Args:
            task_id: The ID of the task

        Returns:
            List of TaskComment objects ordered by created_at
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID.

        Args:
            comment_id: The ID of the comment (exact match or unique prefix)

        Returns:
            The TaskComment object

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
        """
        if comment_id in self._comments:
            return self._comments[comment_id]
        # Support prefix lookup (e.g. first 8 chars shown by list)
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments")
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment to delete (exact match or unique prefix)

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
        """
        comment = self.get_comment(comment_id)  # raises if not found, resolves prefix
        del self._comments[comment.id]
        self._persist()

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment's content and set updated_at timestamp.

        Args:
            comment_id: The ID of the comment to update (exact match or unique prefix)
            content: The new comment content

        Returns:
            The updated TaskComment

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
            ValueError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        comment = self.get_comment(comment_id)  # raises if not found, resolves prefix
        comment.content = content.strip()
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment

    def delete_comments_by_task(self, task_id: str) -> None:
        """Delete all comments for a task (cascade delete).

        Args:
            task_id: The ID of the task whose comments should be deleted
        """
        comment_ids = [c.id for c in self._comments.values() if c.task_id == task_id]
        for comment_id in comment_ids:
            del self._comments[comment_id]
        if comment_ids:
            self._persist()
