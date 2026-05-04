"""Task persistence adapter - separates task storage from domain logic."""

from typing import Any

from ..models.task import Task


class TaskPersistenceAdapter:
    """Adapter handling task persistence operations.

    Responsibility: Manage all task storage/loading logic.
    This isolates persistence details from TaskManager domain logic.
    """

    def __init__(self, storage: Any) -> None:
        """Initialize with a storage backend.

        Args:
            storage: Storage with load() and save() methods.
        """
        self._storage = storage

    def load(self) -> dict[str, Task]:
        """Load all tasks from storage.

        Handles both legacy list and new dict format with projects.

        Returns:
            Dictionary mapping task ID to Task.
        """
        raw = self._storage.load()
        if isinstance(raw, dict):
            tasks_data = raw.get("__tasks__", [])
        else:
            tasks_data = raw
        return {d["id"]: Task.from_dict(d) for d in tasks_data}

    def save(self, tasks: dict[str, Task]) -> None:
        """Save all tasks to storage.

        Preserves format and other data like projects.

        Args:
            tasks: Dictionary mapping task ID to Task.
        """
        raw = self._storage.load()
        if isinstance(raw, dict):
            raw["__tasks__"] = [t.to_dict() for t in tasks.values()]
            self._storage.save(raw)
        else:
            self._storage.save([t.to_dict() for t in tasks.values()])
