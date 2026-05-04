from datetime import datetime, timezone
from typing import Optional, Union

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from ..repositories.task_repository import TaskRepository


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(self, storage_or_repo: Optional[Union[JsonStorage, TaskRepository]] = None) -> None:
        # Support both TaskRepository and JsonStorage for backward compatibility
        if isinstance(storage_or_repo, TaskRepository):
            self._repository = storage_or_repo
        elif isinstance(storage_or_repo, JsonStorage):
            self._repository = TaskRepository(storage_or_repo)
        elif storage_or_repo is None:
            storage = JsonStorage()
            self._repository = TaskRepository(storage)
        else:
            # Fallback: treat as JsonStorage
            self._repository = TaskRepository(storage_or_repo)

        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        tasks = self._repository.load_all()
        self._tasks = {t.id: t for t in tasks}

    def _persist(self) -> None:
        tasks_list = list(self._tasks.values())
        self._repository.save_all(tasks_list)

    def add(self, title: str, description: Optional[str] = None, project_id: Optional[str] = None) -> Task:
        task = Task(title=title, description=description, project_id=project_id)
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

    def list_by_project(self, project_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, project_id: Optional[str] = None) -> Task:
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if project_id is not None:
            task.project_id = project_id
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
