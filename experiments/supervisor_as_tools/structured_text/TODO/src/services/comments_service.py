from typing import TYPE_CHECKING, Optional

from ..models.task_comment import TaskComment
from ..repositories.task_validator import TaskExistenceValidator
from ..storage.storage import Storage
from ..storage.json_storage import JsonStorage

if TYPE_CHECKING:
    pass


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    def __init__(self, storage: Storage, validator: TaskExistenceValidator) -> None:
        self._storage = storage
        self._validator = validator
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load_comments()
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in raw}

    def load_from_dicts(self, comment_dicts: list[dict]) -> None:
        """Load comments from a list of dictionaries.

        Args:
            comment_dicts: List of comment dictionaries.
        """
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in comment_dicts}
        self._persist()

    def _persist(self) -> None:
        self._storage.save_comments([c.to_dict() for c in self._comments.values()])

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        """Add a comment to a task. Raises TaskNotFoundError if task doesn't exist."""
        # Validate task exists
        self._validator.task_exists(task_id)
        # Create and store comment
        comment = TaskComment(task_id=task_id, content=content)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at ascending.
        Raises TaskNotFoundError if task doesn't exist."""
        # Validate task exists
        self._validator.task_exists(task_id)
        # Return comments for this task, sorted by created_at
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment. Raises CommentNotFoundError if not found."""
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        del self._comments[comment_id]
        self._persist()

    def delete_all_for_task(self, task_id: str) -> None:
        """Delete all comments for a task. No error if task has no comments."""
        # Filter out comments for this task
        self._comments = {cid: c for cid, c in self._comments.items() if c.task_id != task_id}
        self._persist()

    def has_comments(self) -> bool:
        """Check if there are any comments.

        Returns:
            True if there are comments, False otherwise.
        """
        return bool(self._comments)

    def clear(self) -> None:
        """Clear all comments."""
        self._comments.clear()
        self._persist()
