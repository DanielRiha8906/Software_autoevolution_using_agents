from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage


class CommentNotFoundError(Exception):
    pass


class CommentManager:
    def __init__(self, storage: Optional[JsonStorage] = None, storage_path: Optional[str] = None) -> None:
        if storage:
            self._storage = storage
        elif storage_path:
            self._storage = JsonStorage(storage_path)
        else:
            self._storage = JsonStorage(str(__file__.replace("comment_manager.py", "../../.todo_comments.json")))
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([c.to_dict() for c in self._comments.values()])

    def add(self, task_id: str, content: str) -> TaskComment:
        comment = TaskComment(task_id=task_id, content=content)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        return self._comments[comment_id]

    def list_by_task(self, task_id: str) -> list[TaskComment]:
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def get_all_comments(self) -> list[TaskComment]:
        """Get all comments.

        Returns:
            A list of all comments.
        """
        return list(self._comments.values())

    def get_comments_for_task(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a specific task.

        Args:
            task_id: The task ID.

        Returns:
            A sorted list of comments for the task.
        """
        return self.list_by_task(task_id)

    def delete(self, comment_id: str) -> None:
        comment = self.get(comment_id)  # raises if missing
        del self._comments[comment.id]
        self._persist()

    def delete_all_by_task(self, task_id: str) -> None:
        comment_ids = [c.id for c in self._comments.values() if c.task_id == task_id]
        for comment_id in comment_ids:
            del self._comments[comment_id]
        if comment_ids:
            self._persist()

    def import_comments(self, comments: list[TaskComment]) -> None:
        """Import a list of comments to storage.

        Args:
            comments: A list of TaskComment objects to import.
        """
        for comment in comments:
            self._comments[comment.id] = comment
        if comments:
            self._persist()
