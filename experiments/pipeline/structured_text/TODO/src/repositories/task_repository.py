"""Repository for Task persistence."""

from datetime import datetime
from pathlib import Path
from typing import Optional, List

from ..exceptions import TaskNotFoundError
from ..models.task import Task
from ..models.task_status import TaskStatus
from .base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for task persistence and CRUD operations."""

    def _deserialize(self, data: dict) -> Task:
        """Deserialize a dict to a Task object.

        Args:
            data: Dictionary representation of a task

        Returns:
            Task instance
        """
        return Task.from_dict(data)

    def _serialize(self, item: Task) -> dict:
        """Serialize a Task to a dict.

        Args:
            item: Task instance

        Returns:
            Dictionary representation of the task
        """
        return item.to_dict()

    def _item_not_found(self, message: str) -> Exception:
        """Create a TaskNotFoundError.

        Args:
            message: Error message

        Returns:
            TaskNotFoundError instance
        """
        return TaskNotFoundError(message)

    def add(self, title: str, description: Optional[str] = None) -> Task:
        """Create and persist a new task.

        Args:
            title: Task title (required)
            description: Optional task description

        Returns:
            The created Task instance
        """
        from datetime import timezone
        task = Task(title=title, description=description)
        self._items[task.id] = task
        self._persist()
        return task

    def list_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status.

        Args:
            status: The TaskStatus to filter by

        Returns:
            List of tasks with the given status
        """
        return [t for t in self._items.values() if t.status == status]

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        """Update a task's title and/or description.

        Args:
            task_id: Task ID or unique prefix
            title: New title (optional)
            description: New description (optional)

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found or prefix is ambiguous
        """
        from datetime import timezone
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        """Update a task's status.

        Args:
            task_id: Task ID or unique prefix
            status: New TaskStatus

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found or prefix is ambiguous
        """
        from datetime import timezone
        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def list_by_filter(
        self,
        status: Optional[TaskStatus] = None,
        due_after: Optional[datetime] = None,
        due_before: Optional[datetime] = None,
        overdue: Optional[bool] = None,
    ) -> List[Task]:
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

        tasks = list(self._items.values())

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

    def list_by_project(self, project_id: str) -> List[Task]:
        """Get all tasks assigned to a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of Task instances assigned to that project
        """
        return [t for t in self._items.values() if t.project_id == project_id]

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
        from datetime import timezone
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
        from datetime import timezone
        task = self.get(task_id)
        task.project_id = None
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def add_many(self, tasks: List[Task]) -> int:
        """Add multiple tasks at once.

        Args:
            tasks: List of Task instances to add

        Returns:
            Number of tasks added
        """
        for task in tasks:
            self._items[task.id] = task
        if tasks:
            self._persist()
        return len(tasks)

    def replace_all(self, tasks: List[Task]) -> int:
        """Replace all tasks with a new set.

        Args:
            tasks: List of Task instances

        Returns:
            Number of tasks in the new set
        """
        self._items.clear()
        return self.add_many(tasks)
