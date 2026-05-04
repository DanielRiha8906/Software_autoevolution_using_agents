"""Dependency injection container for TODO application."""

from pathlib import Path
from typing import Optional

from .repositories.task_repository import TaskRepository
from .repositories.comment_repository import CommentRepository
from .repositories.project_repository import ProjectRepository
from .services.todo_service import TodoService
from .storage.path_provider import StoragePathProvider


class Container:
    """Dependency injection container that manages application dependencies.

    Coordinates the creation and initialization of repositories, services,
    and other components needed by the application.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the container with optional custom storage path.

        Args:
            storage_path: Path to the tasks storage file. If None, uses ~/.todo_data.json
        """
        self._storage_path = storage_path
        self._path_provider = StoragePathProvider(storage_path)
        self._task_repository: Optional[TaskRepository] = None
        self._comment_repository: Optional[CommentRepository] = None
        self._project_repository: Optional[ProjectRepository] = None
        self._service: Optional[TodoService] = None

    def get_task_repository(self) -> TaskRepository:
        """Get or create the task repository.

        Returns:
            TaskRepository instance
        """
        if self._task_repository is None:
            self._task_repository = TaskRepository(self._path_provider.get_tasks_path())
        return self._task_repository

    def get_comment_repository(self) -> CommentRepository:
        """Get or create the comment repository.

        Returns:
            CommentRepository instance
        """
        if self._comment_repository is None:
            self._comment_repository = CommentRepository(self._path_provider.get_comments_path())
        return self._comment_repository

    def get_project_repository(self) -> ProjectRepository:
        """Get or create the project repository.

        Returns:
            ProjectRepository instance
        """
        if self._project_repository is None:
            self._project_repository = ProjectRepository(self._path_provider.get_projects_path())
        return self._project_repository

    def get_todo_service(self) -> TodoService:
        """Get or create the TodoService with all repositories injected.

        Returns:
            TodoService instance
        """
        if self._service is None:
            self._service = TodoService(
                task_repository=self.get_task_repository(),
                comment_repository=self.get_comment_repository(),
                project_repository=self.get_project_repository(),
            )
        return self._service
