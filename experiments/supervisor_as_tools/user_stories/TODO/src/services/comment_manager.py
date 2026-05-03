from datetime import datetime, timezone
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager, TaskNotFoundError


class CommentNotFoundError(Exception):
    pass


class CommentManager:
    def __init__(self, task_manager: TaskManager, storage: Optional[JsonStorage] = None) -> None:
        self._task_manager = task_manager
        self._storage = storage or JsonStorage(str(__import__("pathlib").Path.home() / ".todo_comments.json"))
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([c.to_dict() for c in self._comments.values()])

    def add(self, task_id: str, content: str) -> TaskComment:
        # Validate task exists
        self._task_manager.get(task_id)

        # Validate content is non-empty
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        comment = TaskComment(task_id=task_id, content=content.strip())
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        if comment_id in self._comments:
            return self._comments[comment_id]
        # support short prefix lookup
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments")
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def list_by_task(self, task_id: str) -> list[TaskComment]:
        return [c for c in self._comments.values() if c.task_id == task_id]

    def update(self, comment_id: str, content: str) -> TaskComment:
        comment = self.get(comment_id)
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        comment.content = content.strip()
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment

    def delete(self, comment_id: str) -> None:
        comment = self.get(comment_id)  # resolves prefix; raises if missing
        del self._comments[comment.id]
        self._persist()
