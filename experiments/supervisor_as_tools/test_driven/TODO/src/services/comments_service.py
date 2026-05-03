from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .comment_manager import CommentManager
from .task_manager import TaskNotFoundError
from .todo_service import TodoService


class CommentsService:
    def __init__(self, todo_service: TodoService, storage: Optional[JsonStorage] = None) -> None:
        self._todo_service = todo_service
        self._comment_manager = CommentManager(storage)

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Strip and validate content
        stripped_content = content.strip() if content else ""
        if not stripped_content:
            raise ValueError("comment content cannot be empty")

        # Add comment via manager
        return self._comment_manager.add(task_id, stripped_content)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Return sorted comments
        return self._comment_manager.list_by_task(task_id)

    def delete_comment(self, comment_id: str) -> None:
        self._comment_manager.delete(comment_id)

    def delete_comments_for_task(self, task_id: str) -> None:
        self._comment_manager.delete_all_by_task(task_id)
