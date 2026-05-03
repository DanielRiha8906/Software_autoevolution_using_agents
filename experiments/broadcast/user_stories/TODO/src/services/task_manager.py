from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..models.filter_options import FilterOptions
from ..storage.json_storage import JsonStorage


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._on_delete_callback: Optional[Callable[[str], None]] = None
        self._load()

    def set_on_delete_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when a task is deleted."""
        self._on_delete_callback = callback

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
        del self._tasks[task.id]
        self._persist()
        # Call delete callback for cascade operations
        if self._on_delete_callback:
            self._on_delete_callback(task.id)

    def mark_in_progress(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.mark_in_progress()
        self._persist()
        return task

    def mark_done(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.mark_done()
        self._persist()
        return task

    def reopen(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.reopen()
        self._persist()
        return task

    def list_by_date_range(
        self,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> list[Task]:
        """Filter tasks by due date range."""
        results = []
        for task in self._tasks.values():
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
        return [t for t in self._tasks.values() if t.is_overdue()]

    def apply_filters(self, options: FilterOptions) -> list[Task]:
        """Apply multiple filter criteria to tasks."""
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
