from datetime import datetime, timezone
from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class CommentNotFoundError(Exception):
    pass


class CommentsService:
    def __init__(
        self,
        task_manager: Optional[TaskManager] = None,
        storage: Optional[JsonStorage] = None,
    ) -> None:
        self._task_manager = task_manager or TaskManager()
        self._storage = storage or JsonStorage(path=None)
        # Use a separate storage file for comments
        if self._storage.path.name == ".todo_data.json":
            # Override to use comments file
            self._storage = JsonStorage(
                path=str(self._storage.path.parent / ".todo_comments.json")
            )
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage."""
        raw = self._storage.load()
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in raw}

    def _persist(self) -> None:
        """Save comments to storage."""
        self._storage.save(
            [c.to_dict() for c in sorted(self._comments.values(), key=lambda x: x.created_at)]
        )

    def add_comment(
        self, task_id: str, content: str, author: Optional[str] = None
    ) -> TaskComment:
        """
        Add a comment to a task.

        Validates that the task exists before adding the comment.

        Args:
            task_id: The ID of the task to comment on
            content: The comment content
            author: Optional author name

        Returns:
            The created TaskComment

        Raises:
            ValueError: If content is empty
            TaskNotFoundError: If the task does not exist
        """
        # Validate task exists
        self._task_manager.get(task_id)

        # Create and store comment
        comment = TaskComment(task_id=task_id, content=content, author=author)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """
        List all comments for a task, ordered by created_at ascending.

        Args:
            task_id: The ID of the task

        Returns:
            List of TaskComment objects ordered by created_at
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, comment_id: str) -> None:
        """
        Delete a comment by ID.

        Args:
            comment_id: The ID of the comment to delete

        Raises:
            CommentNotFoundError: If the comment does not exist
        """
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")
        del self._comments[comment_id]
        self._persist()

    def delete_comments_for_task(self, task_id: str) -> None:
        """
        Delete all comments for a task (cascade when task is deleted).

        Args:
            task_id: The ID of the task whose comments should be deleted
        """
        comment_ids = [
            c.id for c in self._comments.values() if c.task_id == task_id
        ]
        for comment_id in comment_ids:
            del self._comments[comment_id]
        if comment_ids:
            self._persist()

    def edit_comment(self, comment_id: str, content: str) -> TaskComment:
        """
        Edit a comment's content and update its updated_at timestamp.

        Args:
            comment_id: The ID of the comment to edit
            content: The new comment content

        Returns:
            The updated TaskComment

        Raises:
            CommentNotFoundError: If the comment does not exist
            ValueError: If content is empty
        """
        if comment_id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment_id}' not found")

        # Validate content using same logic as TaskComment
        if not content or not content.strip():
            raise ValueError("content cannot be empty")

        comment = self._comments[comment_id]
        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment
