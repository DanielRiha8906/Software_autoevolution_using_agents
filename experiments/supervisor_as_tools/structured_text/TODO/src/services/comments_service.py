from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager, TaskNotFoundError


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    def __init__(
        self,
        storage: Optional[JsonStorage] = None,
        task_manager: Optional[TaskManager] = None,
    ) -> None:
        self._storage = storage or JsonStorage()
        self._task_manager = task_manager or TaskManager(self._storage)
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load_comments()
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in raw}

    def _persist(self) -> None:
        self._storage.save_comments([c.to_dict() for c in self._comments.values()])

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        """Add a comment to a task. Raises TaskNotFoundError if task doesn't exist."""
        # Validate task exists
        self._task_manager.get(task_id)
        # Create and store comment
        comment = TaskComment(task_id=task_id, content=content)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at ascending.
        Raises TaskNotFoundError if task doesn't exist."""
        # Validate task exists
        self._task_manager.get(task_id)
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
