"""Comment persistence adapter - separates comment storage from domain logic."""

from typing import Any

from ..models.task_comment import TaskComment


class CommentPersistenceAdapter:
    """Adapter handling comment persistence operations.

    Responsibility: Manage all comment storage/loading logic.
    This isolates persistence details from CommentsService domain logic.
    """

    _COMMENTS_KEY = "__comments__"

    def __init__(self, storage: Any) -> None:
        """Initialize with a storage backend.

        Args:
            storage: Storage with load() and save() methods.
        """
        self._storage = storage

    def load(self) -> dict[str, list[TaskComment]]:
        """Load all comments from storage.

        Returns:
            Dictionary mapping task ID to list of TaskComment.
        """
        raw = self._storage.load()
        if isinstance(raw, dict):
            comments_data = raw.get(self._COMMENTS_KEY, {})
        else:
            comments_data = {}

        result = {}
        for task_id, comment_list in comments_data.items():
            result[task_id] = [TaskComment.from_dict(c) for c in comment_list]
        return result

    def save(self, comments: dict[str, list[TaskComment]]) -> None:
        """Save all comments to storage.

        Preserves other data like tasks and projects.

        Args:
            comments: Dictionary mapping task ID to list of TaskComment.
        """
        raw = self._storage.load()
        if isinstance(raw, list):
            raw = {"__tasks__": raw}

        comments_dict = {}
        for task_id, comment_list in comments.items():
            comments_dict[task_id] = [c.to_dict() for c in comment_list]

        raw[self._COMMENTS_KEY] = comments_dict
        self._storage.save(raw)
