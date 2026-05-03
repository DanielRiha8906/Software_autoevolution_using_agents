from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        # Handle both formats: list (legacy) or dict (with tasks/comments)
        if isinstance(raw, dict):
            task_list = raw.get("tasks", [])
        else:
            task_list = raw if isinstance(raw, list) else []
        self._tasks = {d["id"]: Task.from_dict(d) for d in task_list}

    def _persist(self) -> None:
        raw = self._storage.load()
        # Preserve existing structure (with comments if present)
        if isinstance(raw, dict):
            raw["tasks"] = [t.to_dict() for t in self._tasks.values()]
        else:
            raw = [t.to_dict() for t in self._tasks.values()]
        self._storage.save(raw)

    def add(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        task = Task(title=title, description=description, due_date=due_date)
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

    def list_overdue(self) -> list[Task]:
        """Return all tasks that are overdue (due_date is set and earlier than current CEST time)."""
        return [t for t in self._tasks.values() if t.is_overdue()]

    def list_by_due_date_range(self, before: Optional[datetime] = None, after: Optional[datetime] = None) -> list[Task]:
        """Return tasks with due_date in the specified range.

        Args:
            before: Only include tasks with due_date <= this datetime
            after: Only include tasks with due_date >= this datetime

        Returns:
            List of tasks matching the criteria (those with due_date set)
        """
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

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
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
        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        task = self.get(task_id)  # resolves prefix; raises if missing
        del self._tasks[task.id]
        self._persist()
