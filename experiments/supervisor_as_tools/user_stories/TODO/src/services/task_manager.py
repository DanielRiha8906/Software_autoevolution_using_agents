from datetime import datetime, timezone
from typing import Optional, Union

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from ..utils.datetime_utils import parse_datetime_or_iso_string, is_datetime_in_range


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([t.to_dict() for t in self._tasks.values()])

    def _validate_due_date(self, due_date: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """Validate and convert due_date to CEST datetime or None."""
        try:
            return parse_datetime_or_iso_string(due_date)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid due_date: {e}")

    def add(self, title: str, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None) -> Task:
        validated_due_date = self._validate_due_date(due_date)
        task = Task(title=title, description=description, due_date=validated_due_date)
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

    def list_by_due_date_before(self, due_before: datetime) -> list[Task]:
        """List tasks with due_date on or before the given datetime."""
        return [t for t in self._tasks.values() if t.due_date is not None and t.due_date <= due_before]

    def list_by_due_date_after(self, due_after: datetime) -> list[Task]:
        """List tasks with due_date on or after the given datetime."""
        return [t for t in self._tasks.values() if t.due_date is not None and t.due_date >= due_after]

    def list_by_due_date_range(self, due_start: Optional[datetime], due_end: Optional[datetime]) -> list[Task]:
        """List tasks with due_date within [due_start, due_end] range (inclusive)."""
        return [t for t in self._tasks.values() if is_datetime_in_range(t.due_date, due_start, due_end)]

    def list_overdue(self) -> list[Task]:
        """List tasks that are overdue (past due_date and not completed)."""
        return [t for t in self._tasks.values() if t.is_overdue()]

    def list_by_status_with_filters(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        overdue_only: bool = False,
    ) -> list[Task]:
        """
        List tasks combining status and date filters with AND logic.
        Sorts by (due_date is None, due_date) so tasks with due dates appear first.

        Args:
            status: Filter by TaskStatus, or None for all statuses
            due_before: Filter to tasks due on or before this datetime, or None
            due_after: Filter to tasks due on or after this datetime, or None
            overdue_only: If True, only return overdue tasks (takes precedence over date range)

        Returns:
            Sorted list of tasks matching all filters
        """
        result = list(self._tasks.values())

        if status is not None:
            result = [t for t in result if t.status == status]

        if overdue_only:
            result = [t for t in result if t.is_overdue()]
        else:
            if due_before is not None:
                result = [t for t in result if t.due_date is not None and t.due_date <= due_before]
            if due_after is not None:
                result = [t for t in result if t.due_date is not None and t.due_date >= due_after]

        # Sort by (due_date is None, due_date): tasks with due dates first, then by date
        result.sort(key=lambda t: (t.due_date is None, t.due_date))
        return result

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None) -> Task:
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = self._validate_due_date(due_date)
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
        del self._tasks[task.id]
        self._persist()
