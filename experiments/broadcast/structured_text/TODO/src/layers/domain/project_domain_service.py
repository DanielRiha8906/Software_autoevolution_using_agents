"""Domain service for project-related operations.

This service encapsulates project-specific business logic independent of storage.
"""

from typing import Optional

from ..models.project import Project
from .project_repository import ProjectRepository
from .task_repository import TaskRepository


class ProjectDomainService:
    """Service encapsulating project domain logic."""

    def __init__(self, project_repository: ProjectRepository, task_repository: TaskRepository) -> None:
        self._project_repo = project_repository
        self._task_repo = task_repository

    def create_project(self, name: str) -> Project:
        """Create a new project."""
        return self._project_repo.add(name)

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID."""
        return self._project_repo.get(project_id)

    def update_project(self, project_id: str, name: str) -> Project:
        """Update a project."""
        return self._project_repo.update(project_id, name)

    def list_all_projects(self) -> list[Project]:
        """List all projects."""
        return self._project_repo.list_all()

    def delete_project(self, project_id: str) -> None:
        """Delete a project and unassign its tasks."""
        # Unassign tasks from this project
        tasks = self._task_repo.list_by_project(project_id)
        for task in tasks:
            task.project_id = None
        if tasks:
            self._task_repo._persist()
        # Delete the project
        self._project_repo.delete(project_id)
