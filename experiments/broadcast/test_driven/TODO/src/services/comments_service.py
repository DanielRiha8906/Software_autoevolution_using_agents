from typing import Optional

from ..models.task_comment import TaskComment
from ..models.task import Task


class CommentsService:
    """Comment management service - manages task comments in-memory.

    Responsibility:
    - In-memory comment storage and retrieval
    - Comment creation and access by task
    - Serialization for export/import

    Design notes:
    - Comments are NOT persisted to main storage (in-memory only)
    - Persistence only happens during export/import operations
    - Uses from_dict/to_dict for import/export serialization
    - No direct storage layer dependency
    """

    def __init__(self, todo_service=None) -> None:
        """Initialize the comments service with an empty comments store.

        Args:
            todo_service: Optional reference to TodoService (for future use).
        """
        self._todo_service = todo_service
        self._comments: dict[str, list[TaskComment]] = {}

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to comment on.
            content: The comment content.
            author: Optional author name.

        Returns:
            The created TaskComment.

        Raises:
            ValueError: If content is empty or whitespace-only.
        """
        comment = TaskComment(task_id=task_id, content=content, author=author)
        if task_id not in self._comments:
            self._comments[task_id] = []
        self._comments[task_id].append(comment)
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task.

        Args:
            task_id: The ID of the task.

        Returns:
            A list of TaskComment objects for the task.
        """
        return self._comments.get(task_id, [])

    def get_all_comments(self) -> list[TaskComment]:
        """Get all comments across all tasks.

        Returns:
            A flat list of all TaskComment objects.
        """
        all_comments = []
        for comments in self._comments.values():
            all_comments.extend(comments)
        return all_comments

    def from_dict(self, data: dict) -> None:
        """Load comments from a dictionary representation.

        This clears existing comments and loads from the provided data.

        Args:
            data: A dictionary with task_id keys and lists of comment dicts as values.
        """
        self._comments.clear()
        for task_id, comment_list in data.items():
            self._comments[task_id] = [TaskComment.from_dict(c) for c in comment_list]

    def to_dict(self) -> dict:
        """Export all comments to a dictionary representation.

        Returns:
            A dictionary with task_id keys and lists of comment dicts as values.
        """
        result = {}
        for task_id, comments in self._comments.items():
            result[task_id] = [c.to_dict() for c in comments]
        return result
