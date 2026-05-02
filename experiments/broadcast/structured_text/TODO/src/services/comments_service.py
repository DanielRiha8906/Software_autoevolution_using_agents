from datetime import datetime, timezone
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    def __init__(self, storage: Optional[JsonStorage] = None, task_manager=None) -> None:
        # Create a separate storage instance for comments with a different path
        if storage is None:
            storage = JsonStorage()
        self._storage = storage
        self._task_manager = task_manager
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([c.to_dict() for c in self._comments.values()])

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        # Validate that the referenced task exists (if task_manager is provided)
        if self._task_manager is not None:
            self._task_manager.get(task_id)  # Raises TaskNotFoundError if not found

        comment = TaskComment(task_id=task_id, content=content, author=author)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        # Return all comments for a task, ordered by created_at
        task_comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(task_comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        del self._comments[comment_id]
        self._persist()

    def delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a given task (cascade deletion)."""
        comment_ids_to_delete = [c.id for c in self._comments.values() if c.task_id == task_id]
        for comment_id in comment_ids_to_delete:
            del self._comments[comment_id]
        if comment_ids_to_delete:
            self._persist()

    def get_comment(self, comment_id: str) -> TaskComment:
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        return self._comments[comment_id]

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment's content and update updated_at timestamp."""
        comment = self.get_comment(comment_id)
        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment
