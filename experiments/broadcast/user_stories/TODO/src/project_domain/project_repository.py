"""Project repository layer - isolates project persistence from business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..models.project import Project

if TYPE_CHECKING:
    from ..protocols import ProjectRepository as ProjectRepositoryProtocol


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""
    pass


class ProjectRepository:
    """
    Repository for project persistence and retrieval.

    Isolates project storage operations from business logic. Implements the Repository pattern
    to provide a collection-like interface to project storage.
    """

    def __init__(self, storage_backend: ProjectRepositoryProtocol) -> None:
        """
        Initialize the project repository.

        Args:
            storage_backend: Storage backend implementing ProjectRepository protocol
        """
        self._storage = storage_backend
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load all projects from storage backend."""
        raw_projects = self._storage.load_projects()
        # Convert dicts to Project objects if necessary
        projects = []
        for p in raw_projects:
            if isinstance(p, dict):
                projects.append(Project.from_dict(p))
            else:
                projects.append(p)
        self._projects = {p.id: p for p in projects}

    def _persist(self) -> None:
        """Persist all projects to storage backend."""
        self._storage.save_projects(list(self._projects.values()))

    def add(self, project: Project) -> Project:
        """
        Add a project to the repository.

        Args:
            project: Project to add

        Returns:
            The added project
        """
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """
        Get a project by ID, supporting prefix lookup.

        Args:
            project_id: Project ID or unique prefix

        Returns:
            The project

        Raises:
            ProjectNotFoundError: If project not found
        """
        if project_id in self._projects:
            return self._projects[project_id]
        # Support short prefix lookup
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def get_all(self) -> list[Project]:
        """Get all projects."""
        return list(self._projects.values())

    def update(self, project: Project) -> Project:
        """
        Update a project in the repository.

        Args:
            project: Project with updated values (must have existing id)

        Returns:
            The updated project
        """
        if project.id not in self._projects:
            raise ProjectNotFoundError(f"Project '{project.id}' not found")
        self._projects[project.id] = project
        self._persist()
        return project

    def delete(self, project_id: str) -> Project:
        """
        Delete a project from the repository.

        Args:
            project_id: Project ID or prefix

        Returns:
            The deleted project

        Raises:
            ProjectNotFoundError: If project not found
        """
        project = self.get(project_id)  # Resolves prefix
        del self._projects[project.id]
        self._persist()
        return project


__all__ = ["ProjectRepository", "ProjectNotFoundError"]
