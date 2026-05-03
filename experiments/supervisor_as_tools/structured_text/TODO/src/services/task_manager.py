from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage

if TYPE_CHECKING:
    from .comments_service import CommentsService


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(
        self,
        storage: Optional[JsonStorage] = None,
        comments_service: Optional["CommentsService"] = None,
    ) -> None:
        self._storage = storage or JsonStorage()
        self._comments_service = comments_service
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([t.to_dict() for t in self._tasks.values()])

    def add(self, title: str, description: Optional[str] = None) -> Task:
        task = Task(title=title, description=description)
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
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
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        task = self.get(task_id)  # resolves prefix; raises if missing
        # Delete associated comments if comments_service is set
        if self._comments_service is not None:
            self._comments_service.delete_all_for_task(task.id)
        del self._tasks[task.id]
        self._persist()

    def _validate_due_date(self, dt: Optional[datetime]) -> None:
        """Validate that due_date is not in the past."""
        if dt is None:
            return
        if dt < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past")

    def set_due_date(self, task_id: str, due_date: Optional[datetime]) -> Task:
        task = self.get(task_id)
        self._validate_due_date(due_date)
        task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def list_by_due_date_range(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None, status: Optional[TaskStatus] = None
    ) -> list[Task]:
        """Filter tasks by due_date range (inclusive).

        Args:
            start: Lower bound (inclusive). If None, no lower bound.
            end: Upper bound (inclusive). If None, no upper bound.
            status: Optional status filter.

        Returns:
            List of tasks with due_date in range, excluding tasks without due_date.
            If start > end, returns empty list.
        """
        if start is not None and end is not None and start > end:
            return []

        result = []
        for task in self._tasks.values():
            # Exclude tasks without a due_date
            if task.due_date is None:
                continue

            # Check bounds
            if start is not None and task.due_date < start:
                continue
            if end is not None and task.due_date > end:
                continue

            # Check status filter if provided
            if status is not None and task.status != status:
                continue

            result.append(task)

        return result

    def list_overdue(self, status: Optional[TaskStatus] = None) -> list[Task]:
        """Return only tasks where is_overdue() returns True.

        Args:
            status: Optional status filter.

        Returns:
            List of overdue tasks, optionally filtered by status.
        """
        result = []
        for task in self._tasks.values():
            if not task.is_overdue():
                continue

            if status is not None and task.status != status:
                continue

            result.append(task)

        return result
