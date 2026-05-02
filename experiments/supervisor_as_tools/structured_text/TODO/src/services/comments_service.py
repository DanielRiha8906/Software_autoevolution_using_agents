from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage

if TYPE_CHECKING:
    from .task_manager import TaskManager


class CommentNotFoundError(Exception):
    """Raised when a comment cannot be found."""

    pass


class CommentsService:
    """Manages task comments with CRUD operations and persistence."""

    def __init__(
        self,
        storage: Optional[JsonStorage] = None,
        task_manager: Optional["TaskManager"] = None,
    ) -> None:
        """Initialize CommentsService.

        Args:
            storage: JsonStorage instance for persistence. Defaults to new JsonStorage().
            task_manager: Optional TaskManager for task existence validation.
        """
        self._storage = storage or JsonStorage()
        self._task_manager = task_manager
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage."""
        data = self._storage.load_all()
        comments_list = data.get("comments", [])
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in comments_list}

    def _persist(self) -> None:
        """Persist all data (tasks and comments) to storage."""
        data = self._storage.load_all()
        data["comments"] = [c.to_dict() for c in self._comments.values()]
        self._storage.save_all(data)

    def add(
        self,
        task_id: str,
        content: str,
        author: Optional[str] = None,
    ) -> TaskComment:
        """Add a new comment to a task.

        Args:
            task_id: ID of the task to comment on.
            content: Comment content.
            author: Optional author name/identifier.

        Returns:
            The created TaskComment.

        Raises:
            ValueError: If task_id or content is empty.
        """
        comment = TaskComment(task_id=task_id, content=content, author=author)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        """Get a comment by ID or prefix.

        Args:
            comment_id: Full or partial comment ID.

        Returns:
            The TaskComment.

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous.
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

    def list_all(self) -> list[TaskComment]:
        """Get all comments.

        Returns:
            List of all TaskComment objects.
        """
        return list(self._comments.values())

    def list_for_task(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a specific task, sorted by created_at ascending.

        Args:
            task_id: ID of the task.

        Returns:
            List of TaskComment objects for the task, sorted by created_at ascending.
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def update(
        self,
        comment_id: str,
        content: Optional[str] = None,
        author: Optional[str] = None,
    ) -> TaskComment:
        """Update a comment.

        Args:
            comment_id: Full or partial comment ID.
            content: New content. If None, content is not changed.
            author: New author. If None, author is not changed.

        Returns:
            The updated TaskComment.

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous.
        """
        comment = self.get(comment_id)
        if content is not None:
            comment.content = content
        if author is not None:
            comment.author = author
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment

    def delete(self, comment_id: str) -> None:
        """Delete a comment by ID or prefix.

        Args:
            comment_id: Full or partial comment ID.

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous.
        """
        comment = self.get(comment_id)  # resolves prefix; raises if missing
        del self._comments[comment.id]
        self._persist()

    def delete_by_task_id(self, task_id: str) -> None:
        """Delete all comments for a specific task.

        Args:
            task_id: ID of the task.
        """
        comment_ids = [c.id for c in self._comments.values() if c.task_id == task_id]
        for cid in comment_ids:
            del self._comments[cid]
        if comment_ids:
            self._persist()
