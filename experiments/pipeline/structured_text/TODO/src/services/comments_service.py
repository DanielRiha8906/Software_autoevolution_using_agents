from pathlib import Path
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    def __init__(self, storage: Optional[JsonStorage] = None, task_manager: TaskManager = None) -> None:
        """Initialize CommentsService with optional custom storage and task manager for validation.

        Args:
            storage: Optional JsonStorage instance. Defaults to ~/.todo_comments.json
            task_manager: TaskManager instance for validating task existence
        """
        self._storage = storage or JsonStorage(path=str(Path.home() / ".todo_comments.json"))
        self._task_manager = task_manager
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage into memory cache."""
        raw = self._storage.load()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Persist comments from memory cache to storage."""
        self._storage.save([c.to_dict() for c in self._comments.values()])

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: ID of the task to comment on
            content: Comment text

        Returns:
            TaskComment object

        Raises:
            TaskNotFoundError: If task does not exist
            ValueError: If content is empty or whitespace-only
        """
        # Validate task exists
        self._task_manager.get(task_id)

        # Validate content is not empty
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        # Create and store comment
        comment = TaskComment(task_id=task_id, content=content.strip())
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, sorted by created_at ascending.

        Args:
            task_id: ID of the task

        Returns:
            List of TaskComment objects sorted by created_at
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: ID of the comment to delete

        Raises:
            CommentNotFoundError: If comment does not exist
        """
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        del self._comments[comment_id]
        self._persist()

    def delete_task_comments(self, task_id: str) -> None:
        """Delete all comments for a task. Idempotent (no error if no comments).

        Args:
            task_id: ID of the task
        """
        comment_ids_to_delete = [
            cid for cid, c in self._comments.items() if c.task_id == task_id
        ]
        for cid in comment_ids_to_delete:
            del self._comments[cid]
        if comment_ids_to_delete:
            self._persist()
