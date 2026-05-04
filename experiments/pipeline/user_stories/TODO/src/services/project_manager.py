from typing import Optional

from ..models.project import Project
from ..storage.json_storage import JsonStorage


class ProjectNotFoundError(Exception):
    pass


class ProjectManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        data = self._storage.load()
        projects_data = data.get("projects", []) if isinstance(data, dict) else []
        self._projects = {d["id"]: Project.from_dict(d) for d in projects_data}

    def _persist(self) -> None:
        """Persist projects to storage."""
        # Must preserve tasks when saving
        data = self._storage.load()
        if isinstance(data, dict):
            tasks_data = data.get("tasks", [])
        else:
            # Handle migration from old list format
            tasks_data = data if isinstance(data, list) else []
        self._storage.save({
            "tasks": tasks_data,
            "projects": [p.to_dict() for p in self._projects.values()]
        })

    def add(self, name: str) -> Project:
        """Create a new project.

        Args:
            name: Project name (non-empty string).

        Returns:
            Project: The created project.

        Raises:
            ValueError: If name is empty.
        """
        project = Project(name=name)
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """Get a project by ID or prefix.

        Args:
            project_id: Full or partial project ID (first 8+ chars).

        Returns:
            Project: The project.

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous.
        """
        if project_id in self._projects:
            return self._projects[project_id]
        # Prefix lookup support
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list_all(self) -> list[Project]:
        """Get all projects."""
        return list(self._projects.values())

    def delete(self, project_id: str) -> None:
        """Delete a project.

        Args:
            project_id: Full or partial project ID.

        Raises:
            ProjectNotFoundError: If project not found.
        """
        project = self.get(project_id)  # Resolves prefix, raises if missing
        del self._projects[project.id]
        self._persist()
