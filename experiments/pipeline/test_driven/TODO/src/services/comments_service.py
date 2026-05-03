from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskNotFoundError
from .todo_service import TodoService


class CommentsService:
    def __init__(self, todo_service: TodoService, storage: Optional[JsonStorage] = None) -> None:
        self._todo_service = todo_service
        self._storage = storage or JsonStorage()
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load_comments()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save_comments([c.to_dict() for c in self._comments.values()])

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        # Validate that task exists
        self._todo_service.get_task(task_id)

        # Create comment (TaskComment validates non-empty content)
        comment = TaskComment(task_id=task_id, content=content)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        # Filter comments by task_id and sort by created_at ascending
        task_comments = [c for c in self._comments.values() if c.task_id == task_id]
        task_comments.sort(key=lambda c: c.created_at)
        return task_comments

    def delete_comment(self, comment_id: str) -> None:
        if comment_id in self._comments:
            del self._comments[comment_id]
            self._persist()

    def delete_comments_for_task(self, task_id: str) -> None:
        # Cascade delete - does not validate task existence
        comment_ids = [c.id for c in self._comments.values() if c.task_id == task_id]
        for comment_id in comment_ids:
            del self._comments[comment_id]
        if comment_ids:
            self._persist()
