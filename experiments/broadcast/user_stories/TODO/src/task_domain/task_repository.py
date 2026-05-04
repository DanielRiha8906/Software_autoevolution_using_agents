"""Task repository layer - isolates task persistence from business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.filter_options import FilterOptions

if TYPE_CHECKING:
    from ..protocols import TaskRepository as TaskRepositoryProtocol


class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""
    pass


class TaskRepository:
    """
    Repository for task persistence and retrieval.

    Isolates task storage operations from business logic. Implements the Repository pattern
    to provide a collection-like interface to task storage.
    """

    def __init__(self, storage_backend: TaskRepositoryProtocol) -> None:
        """
        Initialize the task repository.

        Args:
            storage_backend: Storage backend implementing TaskRepository protocol
        """
        self._storage = storage_backend
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        """Load all tasks from storage backend."""
        tasks = self._storage.load_tasks()
        self._tasks = {t.id: t for t in tasks}

    def _persist(self) -> None:
        """Persist all tasks to storage backend."""
        self._storage.save_tasks(list(self._tasks.values()))

    def add(self, task: Task) -> Task:
        """
        Add a task to the repository.

        Args:
            task: Task to add

        Returns:
            The added task
        """
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
        """
        Get a task by ID, supporting prefix lookup.

        Args:
            task_id: Task ID or unique prefix

        Returns:
            The task

        Raises:
            TaskNotFoundError: If task not found
        """
        if task_id in self._tasks:
            return self._tasks[task_id]
        # Support short prefix lookup
        matches = [t for tid, t in self._tasks.items() if tid.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFoundError(f"Ambiguous prefix '{task_id}' matches {len(matches)} tasks")
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    def get_all(self) -> list[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks filtered by status."""
        return [t for t in self._tasks.values() if t.status == status]

    def update(self, task: Task) -> Task:
        """
        Update a task in the repository.

        Args:
            task: Task with updated values (must have existing id)

        Returns:
            The updated task
        """
        if task.id not in self._tasks:
            raise TaskNotFoundError(f"Task '{task.id}' not found")
        self._tasks[task.id] = task
        self._persist()
        return task

    def delete(self, task_id: str) -> Task:
        """
        Delete a task from the repository.

        Args:
            task_id: Task ID or prefix

        Returns:
            The deleted task

        Raises:
            TaskNotFoundError: If task not found
        """
        task = self.get(task_id)  # Resolves prefix
        del self._tasks[task.id]
        self._persist()
        return task

    def apply_filters(self, options: FilterOptions) -> list[Task]:
        """
        Apply multiple filter criteria to tasks.

        Args:
            options: FilterOptions with filter criteria

        Returns:
            Filtered list of tasks
        """
        from ..models.task import CEST

        results = list(self._tasks.values())

        # Filter by status if specified
        if options.status is not None:
            results = [t for t in results if t.status == options.status]

        # Filter by due date range (excluding tasks without due dates when filtering by date)
        if options.due_before is not None or options.due_after is not None:
            filtered_by_date = []
            for task in results:
                if task.due_date is None:
                    continue

                # Convert to CEST for consistent comparison
                task_due = task.due_date.astimezone(CEST)

                if options.due_before is not None:
                    before_cest = options.due_before.astimezone(CEST) if options.due_before.tzinfo else options.due_before.replace(tzinfo=CEST)
                    if task_due >= before_cest:
                        continue

                if options.due_after is not None:
                    after_cest = options.due_after.astimezone(CEST) if options.due_after.tzinfo else options.due_after.replace(tzinfo=CEST)
                    if task_due < after_cest:
                        continue

                filtered_by_date.append(task)
            results = filtered_by_date

        # Filter by overdue status if requested
        if options.overdue_only:
            results = [t for t in results if t.is_overdue()]

        return results


__all__ = ["TaskRepository", "TaskNotFoundError"]
