"""Repository for persisting and retrieving tasks."""

from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.protocols import StorageProtocol
from .exceptions import TaskNotFoundError


class TaskRepository:
    """Repository managing task persistence and retrieval.

    Uses StorageProtocol for abstraction from storage implementation.
    """

    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        """Load tasks from storage."""
        raw = self._storage.load()
        # Handle both formats: list (legacy) or dict (with tasks/comments)
        if isinstance(raw, dict):
            task_list = raw.get("tasks", [])
        else:
            task_list = raw if isinstance(raw, list) else []
        self._tasks = {d["id"]: Task.from_dict(d) for d in task_list}

    def _persist(self) -> None:
        """Persist tasks to storage."""
        raw = self._storage.load()
        # Preserve existing structure (with comments if present)
        if isinstance(raw, dict):
            raw["tasks"] = [t.to_dict() for t in self._tasks.values()]
        else:
            raw = [t.to_dict() for t in self._tasks.values()]
        self._storage.save(raw)

    def add(self, title: str, description: Optional[str] = None, due_date=None) -> Task:
        """Add a new task."""
        task = Task(title=title, description=description, due_date=due_date)
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
        """Get a task by ID, supporting prefix lookup."""
        if task_id in self._tasks:
            return self._tasks[task_id]
        # support short prefix lookup (e.g. first 8 chars shown by list)
        matches = [t for tid, t in self._tasks.items() if tid.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFoundError(f"Ambiguous prefix '{task_id}' matches {len(matches)} tasks")
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks by status."""
        return [t for t in self._tasks.values() if t.status == status]

    def list_by_project(self, project_id: str) -> list[Task]:
        """List tasks by project."""
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def list_overdue(self) -> list[Task]:
        """List all overdue tasks."""
        return [t for t in self._tasks.values() if t.is_overdue()]

    def list_by_due_date_range(self, before=None, after=None) -> list[Task]:
        """List tasks with due_date in the specified range."""
        result = []
        for task in self._tasks.values():
            if task.due_date is None:
                continue
            if before is not None and task.due_date > before:
                continue
            if after is not None and task.due_date < after:
                continue
            result.append(task)
        return result

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date=None) -> Task:
        """Update a task."""
        from datetime import datetime, timezone

        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        """Set task status."""
        from datetime import datetime, timezone

        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        """Delete a task."""
        task = self.get(task_id)  # resolves prefix; raises if missing
        del self._tasks[task.id]
        self._persist()
