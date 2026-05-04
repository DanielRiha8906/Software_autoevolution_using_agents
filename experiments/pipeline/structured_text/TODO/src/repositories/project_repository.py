"""Repository for Project persistence."""

from datetime import datetime, timezone
from typing import Optional, List

from ..exceptions import ProjectNotFoundError
from ..models.project import Project
from .base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for project persistence and CRUD operations."""

    def _deserialize(self, data: dict) -> Project:
        """Deserialize a dict to a Project object.

        Args:
            data: Dictionary representation of a project

        Returns:
            Project instance
        """
        return Project.from_dict(data)

    def _serialize(self, item: Project) -> dict:
        """Serialize a Project to a dict.

        Args:
            item: Project instance

        Returns:
            Dictionary representation of the project
        """
        return item.to_dict()

    def _item_not_found(self, message: str) -> Exception:
        """Create a ProjectNotFoundError.

        Args:
            message: Error message

        Returns:
            ProjectNotFoundError instance
        """
        return ProjectNotFoundError(message)

    def add(self, name: str) -> Project:
        """Create and persist a new project.

        Args:
            name: Project name (required, non-empty)

        Returns:
            The created Project instance
        """
        project = Project(name=name)
        self._items[project.id] = project
        self._persist()
        return project

    def update(self, project_id: str, name: str) -> Project:
        """Update a project's name.

        Args:
            project_id: Project ID or unique prefix
            name: New project name (required, non-empty)

        Returns:
            The updated Project instance

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        project = self.get(project_id)
        project.name = name
        self._persist()
        return project

    def add_many(self, projects: List[Project]) -> int:
        """Add multiple projects at once.

        Args:
            projects: List of Project instances to add

        Returns:
            Number of projects added
        """
        for project in projects:
            self._items[project.id] = project
        if projects:
            self._persist()
        return len(projects)

    def replace_all(self, projects: List[Project]) -> int:
        """Replace all projects with a new set.

        Args:
            projects: List of Project instances

        Returns:
            Number of projects in the new set
        """
        self._items.clear()
        return self.add_many(projects)
