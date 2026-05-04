"""Repository for TaskComment persistence."""

from typing import Optional, List

from ..exceptions import CommentNotFoundError
from ..models.task_comment import TaskComment
from .base_repository import BaseRepository


class CommentRepository(BaseRepository[TaskComment]):
    """Repository for comment persistence and CRUD operations."""

    def _deserialize(self, data: dict) -> TaskComment:
        """Deserialize a dict to a TaskComment object.

        Args:
            data: Dictionary representation of a comment

        Returns:
            TaskComment instance
        """
        return TaskComment.from_dict(data)

    def _serialize(self, item: TaskComment) -> dict:
        """Serialize a TaskComment to a dict.

        Args:
            item: TaskComment instance

        Returns:
            Dictionary representation of the comment
        """
        return item.to_dict()

    def _item_not_found(self, message: str) -> Exception:
        """Create a CommentNotFoundError.

        Args:
            message: Error message

        Returns:
            CommentNotFoundError instance
        """
        return CommentNotFoundError(message)

    def add(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Create and persist a new comment.

        Args:
            task_id: ID of the task this comment belongs to
            content: Comment text (required, non-empty)
            author: Optional author name

        Returns:
            The created TaskComment instance
        """
        comment = TaskComment(task_id=task_id, content=content, author=author)
        self._items[comment.id] = comment
        self._persist()
        return comment

    def list_by_task(self, task_id: str) -> List[TaskComment]:
        """Get all comments for a task in chronological order.

        Args:
            task_id: ID of the task

        Returns:
            List of TaskComment instances sorted by created_at (oldest first)
        """
        comments = [c for c in self._items.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_all_by_task(self, task_id: str) -> None:
        """Delete all comments for a task.

        Args:
            task_id: ID of the task
        """
        comment_ids = [c.id for c in self._items.values() if c.task_id == task_id]
        for comment_id in comment_ids:
            del self._items[comment_id]
        if comment_ids:
            self._persist()

    def add_many(self, comments: List[TaskComment]) -> int:
        """Add multiple comments at once.

        Args:
            comments: List of TaskComment instances to add

        Returns:
            Number of comments added
        """
        for comment in comments:
            self._items[comment.id] = comment
        if comments:
            self._persist()
        return len(comments)

    def replace_all(self, comments: List[TaskComment]) -> int:
        """Replace all comments with a new set.

        Args:
            comments: List of TaskComment instances

        Returns:
            Number of comments in the new set
        """
        self._items.clear()
        return self.add_many(comments)
