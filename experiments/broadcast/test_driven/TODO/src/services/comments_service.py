from typing import Optional

from ..models.task_comment import TaskComment
from .task_manager import TaskNotFoundError
from .todo_service import TodoService


class CommentsService:
    def __init__(self, todo_service: TodoService) -> None:
        self._todo_service = todo_service
        self._comments: dict[str, TaskComment] = {}

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to add a comment to.
            content: The comment content.

        Returns:
            The created TaskComment.

        Raises:
            TaskNotFoundError: If the task does not exist.
            Exception: If content is empty.
        """
        # Validate that the task exists
        try:
            self._todo_service.get_task(task_id)
        except TaskNotFoundError as e:
            raise Exception(str(e))

        # TaskComment validates empty content in __post_init__
        comment = TaskComment(task_id=task_id, content=content)
        self._comments[comment.id] = comment
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at.

        Args:
            task_id: The ID of the task.

        Returns:
            A list of TaskComment objects ordered by created_at (ascending).
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by its ID.

        Args:
            comment_id: The ID of the comment to delete.
        """
        if comment_id in self._comments:
            del self._comments[comment_id]

    def delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task.

        Args:
            task_id: The ID of the task.
        """
        comment_ids_to_delete = [
            c_id for c_id, comment in self._comments.items()
            if comment.task_id == task_id
        ]
        for comment_id in comment_ids_to_delete:
            del self._comments[comment_id]
