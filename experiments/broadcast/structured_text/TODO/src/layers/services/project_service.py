"""Project domain service for project-related use cases."""

from typing import Optional

from ..models import Project
from ..repositories import JsonProjectRepository, ProjectNotFoundError
from ..storage import JsonStorage


class ProjectService:
    """Domain service for managing projects."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._repository = JsonProjectRepository(storage or JsonStorage())

    def add_project(self, name: str) -> Project:
        """Create a new project."""
        return self._repository.add(name)

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID."""
        return self._repository.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return self._repository.list_all()

    def update_project(self, project_id: str, name: str) -> Project:
        """Update a project."""
        return self._repository.update(project_id, name)

    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        self._repository.delete(project_id)
