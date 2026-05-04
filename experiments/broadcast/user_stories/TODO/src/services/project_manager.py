"""Project management service - business logic layer."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Any

from ..models.project import Project

if TYPE_CHECKING:
    pass


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""
    pass


class ProjectManager:
    """
    Business logic layer for project management.

    Encapsulates project-related operations using the project repository for persistence.

    Can accept either a ProjectRepository (preferred) or JsonStorage (backward compatible).
    """

    def __init__(self, repository: Any) -> None:
        """
        Initialize ProjectManager with a project repository.

        Args:
            repository: ProjectRepository instance OR JsonStorage for backward compatibility
        """
        # Backward compatibility: if given JsonStorage, wrap it in a ProjectRepository
        if hasattr(repository, 'load') and hasattr(repository, 'save') and not hasattr(repository, 'add'):
            from ..project_domain import ProjectRepositoryImpl
            self._repository = ProjectRepositoryImpl(repository)
        else:
            self._repository = repository

    def add(self, name: str) -> Project:
        """Create and store a new project."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name.strip())
        return self._repository.add(project)

    def get(self, project_id: str) -> Project:
        """Get a project by ID, supporting prefix lookup."""
        from ..project_domain import ProjectNotFoundError as DomainProjectNotFoundError
        try:
            return self._repository.get(project_id)
        except DomainProjectNotFoundError as e:
            raise ProjectNotFoundError(str(e))

    def list_all(self) -> list[Project]:
        """Return all projects."""
        return self._repository.get_all()

    def update(self, project_id: str, name: Optional[str] = None) -> Project:
        """Update a project's name."""
        project = self.get(project_id)
        if name is not None:
            if not name.strip():
                raise ValueError("Project name cannot be empty")
            project.name = name.strip()
            return self._repository.update(project)
        return project

    def delete(self, project_id: str) -> None:
        """Delete a project. Tasks are not deleted, just unassigned."""
        from ..project_domain import ProjectNotFoundError as DomainProjectNotFoundError
        try:
            self._repository.delete(project_id)
        except DomainProjectNotFoundError as e:
            raise ProjectNotFoundError(str(e))
