from typing import Optional

from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage


class CommentNotFoundError(Exception):
    pass


class CommentManager:
    """Manager for task comments with CRUD operations and JSON persistence.

    Stores comments in a separate JSON file (default: ~/.todo_comments.json).
    Maintains an in-memory dict of comments, persisting after mutations.
    """

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        """Initialize CommentManager with optional custom storage.

        Args:
            storage: JsonStorage instance. If None, uses default path ~/.todo_comments.json
        """
        self._storage = storage or JsonStorage(path=None)  # Will get default path from JsonStorage
        # Override default path to use comments file
        if self._storage.path == self._storage.path.parent / ".todo_data.json":
            self._storage._path = self._storage.path.parent / ".todo_comments.json"
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load all comments from storage into memory."""
        raw = self._storage.load()
        self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Save all comments from memory to storage."""
        self._storage.save([c.to_dict() for c in self._comments.values()])

    def add(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a new comment to a task.

        Args:
            task_id: ID of the task to comment on
            content: Comment text (required)
            author: Optional author name

        Returns:
            The created TaskComment instance

        Raises:
            ValueError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        comment = TaskComment(task_id=task_id, content=content.strip(), author=author)
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        """Get a comment by ID or ID prefix.

        Args:
            comment_id: Full comment ID or unique prefix (e.g., first 8 chars)

        Returns:
            The TaskComment instance

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous
        """
        if comment_id in self._comments:
            return self._comments[comment_id]
        # support short prefix lookup
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments")
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def list_all(self) -> list[TaskComment]:
        """Get all comments in chronological order (oldest first).

        Returns:
            List of TaskComment instances sorted by created_at
        """
        return sorted(self._comments.values(), key=lambda c: c.created_at)

    def list_by_task(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a specific task in chronological order.

        Args:
            task_id: ID of the task

        Returns:
            List of TaskComment instances for that task, sorted by created_at (oldest first)
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def delete(self, comment_id: str) -> None:
        """Delete a comment by ID or ID prefix.

        Args:
            comment_id: Full comment ID or unique prefix

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous
        """
        comment = self.get(comment_id)  # resolves prefix; raises if missing
        del self._comments[comment.id]
        self._persist()

    def delete_all_by_task(self, task_id: str) -> None:
        """Delete all comments for a specific task (cascading deletion).

        Args:
            task_id: ID of the task
        """
        self._comments = {cid: c for cid, c in self._comments.items() if c.task_id != task_id}
        self._persist()
