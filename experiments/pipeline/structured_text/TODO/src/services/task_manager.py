from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task
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

    def list_by_filter(
        self,
        status: Optional[TaskStatus] = None,
        due_after: Optional[datetime] = None,
        due_before: Optional[datetime] = None,
        overdue: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by status, due date range, and overdue status.

        Args:
            status: Filter by task status (optional).
            due_after: Return tasks with due_date >= this datetime (optional).
            due_before: Return tasks with due_date <= this datetime (optional).
            overdue: If True, return only overdue tasks; if False, return only non-overdue tasks (optional).

        Returns:
            List of tasks matching all specified filters.

        Raises:
            ValueError: If due_after > due_before.
        """
        # Validate date range
        if due_after is not None and due_before is not None:
            if due_after > due_before:
                raise ValueError("due_after cannot be after due_before")

        tasks = list(self._tasks.values())

        # Filter by status
        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        # Filter by due date range (tasks without due_date are excluded from range filters)
        if due_after is not None or due_before is not None:
            filtered_by_due = []
            for t in tasks:
                # Skip tasks without a due_date
                if t.due_date is None:
                    continue
                # Check due_after
                if due_after is not None and t.due_date < due_after:
                    continue
                # Check due_before
                if due_before is not None and t.due_date > due_before:
                    continue
                filtered_by_due.append(t)
            tasks = filtered_by_due

        # Filter by overdue status
        if overdue is not None:
            tasks = [t for t in tasks if t.is_overdue() == overdue]

        return tasks

    def list_by_project(self, project_id: str) -> list[Task]:
        """Get all tasks assigned to a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of Task instances assigned to that project
        """
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def assign_to_project(self, task_id: str, project_id: str) -> Task:
        """Assign a task to a project.

        Args:
            task_id: ID of the task (full or prefix)
            project_id: ID of the project to assign to

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found or prefix is ambiguous
        """
        task = self.get(task_id)
        task.project_id = project_id
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def unassign_from_project(self, task_id: str) -> Task:
        """Unassign a task from its project.

        Args:
            task_id: ID of the task (full or prefix)

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found or prefix is ambiguous
        """
        task = self.get(task_id)
        task.project_id = None
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task
