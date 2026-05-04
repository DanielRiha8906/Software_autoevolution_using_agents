"""Task management service - business logic layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional, TYPE_CHECKING, Any

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..models.filter_options import FilterOptions

if TYPE_CHECKING:
    pass


class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""
    pass


class TaskManager:
    """
    Business logic layer for task management.

    Encapsulates task-related operations using the task repository for persistence.
    This layer bridges domain logic and storage operations.

    Can accept either a TaskRepository (preferred) or JsonStorage (backward compatible).
    """

    def __init__(self, repository: Any) -> None:
        """
        Initialize TaskManager with a task repository.

        Args:
            repository: TaskRepository instance OR JsonStorage for backward compatibility
        """
        # Backward compatibility: if given JsonStorage, wrap it in a TaskRepository
        if hasattr(repository, 'load') and hasattr(repository, 'save') and not hasattr(repository, 'add'):
            from ..task_domain import TaskRepositoryImpl
            self._repository = TaskRepositoryImpl(repository)
        else:
            self._repository = repository
        self._on_delete_callback: Optional[Callable[[str], None]] = None

    def set_on_delete_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when a task is deleted."""
        self._on_delete_callback = callback

    # Backward compatibility properties for accessing internals
    @property
    def _tasks(self) -> dict:
        """Access internal tasks dict (backward compatibility)."""
        return self._repository._tasks

    @property
    def _storage(self) -> Any:
        """Access internal storage (backward compatibility)."""
        return self._repository._storage

    def _persist(self) -> None:
        """Persist tasks (backward compatibility)."""
        return self._repository._persist()

    def add(self, title: str, description: Optional[str] = None) -> Task:
        """Create and add a new task."""
        task = Task(title=title, description=description)
        return self._repository.add(task)

    def get(self, task_id: str) -> Task:
        """Get a task by ID (supports prefix lookup)."""
        from ..task_domain import TaskNotFoundError as DomainTaskNotFoundError
        try:
            return self._repository.get(task_id)
        except DomainTaskNotFoundError as e:
            raise TaskNotFoundError(str(e))

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return self._repository.get_all()

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks filtered by status."""
        return self._repository.get_by_status(status)

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        """Update task title and/or description."""
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        task.updated_at = datetime.now(timezone.utc)
        return self._repository.update(task)

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        """Set task status."""
        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        return self._repository.update(task)

    def delete(self, task_id: str) -> None:
        """Delete a task."""
        from ..task_domain import TaskNotFoundError as DomainTaskNotFoundError
        try:
            task = self._repository.delete(task_id)
        except DomainTaskNotFoundError as e:
            raise TaskNotFoundError(str(e))
        # Call delete callback for cascade operations
        if self._on_delete_callback:
            self._on_delete_callback(task.id)

    def mark_in_progress(self, task_id: str) -> Task:
        """Mark a task as in progress."""
        task = self.get(task_id)
        task.mark_in_progress()
        return self._repository.update(task)

    def mark_done(self, task_id: str) -> Task:
        """Mark a task as done."""
        task = self.get(task_id)
        task.mark_done()
        return self._repository.update(task)

    def reopen(self, task_id: str) -> Task:
        """Reopen a task."""
        task = self.get(task_id)
        task.reopen()
        return self._repository.update(task)

    def list_by_date_range(
        self,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> list[Task]:
        """Filter tasks by due date range."""
        results = []
        for task in self.list_all():
            if task.due_date is None:
                continue

            # Convert to CEST for consistent comparison
            task_due = task.due_date.astimezone(CEST)

            if before is not None:
                before_cest = before.astimezone(CEST) if before.tzinfo else before.replace(tzinfo=CEST)
                if task_due >= before_cest:
                    continue

            if after is not None:
                after_cest = after.astimezone(CEST) if after.tzinfo else after.replace(tzinfo=CEST)
                if task_due < after_cest:
                    continue

            results.append(task)

        return results

    def list_overdue(self) -> list[Task]:
        """Filter tasks that are overdue (due date in the past)."""
        return [t for t in self.list_all() if t.is_overdue()]

    def list_by_project(self, project_id: str) -> list[Task]:
        """Filter tasks by project ID."""
        return [t for t in self.list_all() if t.project_id == project_id]

    def list_unassigned(self) -> list[Task]:
        """List all tasks not assigned to any project."""
        return [t for t in self.list_all() if t.project_id is None]

    def set_project(self, task_id: str, project_id: Optional[str]) -> Task:
        """Assign or unassign a task to/from a project."""
        task = self.get(task_id)
        task.project_id = project_id
        return self._repository.update(task)

    def apply_filters(self, options: FilterOptions) -> list[Task]:
        """Apply multiple filter criteria to tasks."""
        return self._repository.apply_filters(options)
