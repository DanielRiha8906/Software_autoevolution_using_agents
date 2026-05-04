from typing import Optional
from ..models.task import Task
from ..serialization.task_serializer import TaskSerializer
from ..storage.storage_port import StoragePort


class TaskRepository:
    """Repository pattern wrapper around storage for Task persistence.

    Coordinates storage operations with TaskSerializer for serialization.
    """

    def __init__(self, storage: StoragePort) -> None:
        """Initialize the repository with a storage backend.

        Args:
            storage: Implementation of StoragePort protocol
        """
        self._storage = storage
        self._serializer = TaskSerializer()

    def load_all(self) -> list[Task]:
        """Load all tasks from storage.

        Returns:
            List of Task objects
        """
        raw_tasks = self._storage.load()
        return [self._serializer.from_dict(d) for d in raw_tasks]

    def save_all(self, tasks: list[Task]) -> None:
        """Save all tasks to storage.

        Args:
            tasks: List of Task objects to persist
        """
        task_dicts = [self._serializer.to_dict(t) for t in tasks]
        self._storage.save(task_dicts)
