from typing import Optional
from datetime import datetime

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None, project_id: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        task = self._manager.add(title.strip(), description, project_id=project_id)
        if due_date is not None:
            task.due_date = due_date
            self._manager._persist()
        return task

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        overdue: bool = False,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        # Validate timezone for date parameters
        if due_before is not None and due_before.tzinfo != CEST:
            raise ValueError("due_before must use CEST timezone")
        if due_after is not None and due_after.tzinfo != CEST:
            raise ValueError("due_after must use CEST timezone")

        # Get all tasks
        tasks = self._manager.list_all()

        # Apply status filter if provided
        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        # Apply due_before filter if provided
        if due_before is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date < due_before]

        # Apply due_after filter if provided
        if due_after is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date > due_after]

        # Apply overdue filter if True
        if overdue:
            tasks = [t for t in tasks if t.is_overdue()]

        # Apply project_id filter if provided
        if project_id is not None:
            tasks = [t for t in tasks if t.project_id == project_id]

        return tasks

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, project_id: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description, project_id=project_id)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)
