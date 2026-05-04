from __future__ import annotations

from typing import Optional

from ..models.project import Project
from ..storage.json_storage import JsonStorage


class ProjectNotFoundError(Exception):
    pass


class ProjectManager:
    """Manages CRUD operations for projects."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        raw = self._storage.load_projects()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Persist projects to storage."""
        self._storage.save_projects([p.to_dict() for p in self._projects.values()])

    def add(self, name: str) -> Project:
        """Create and store a new project."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name.strip())
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """Get a project by ID, supporting prefix lookup."""
        if project_id in self._projects:
            return self._projects[project_id]
        # Support short prefix lookup (e.g., first 8 chars)
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list_all(self) -> list[Project]:
        """Return all projects."""
        return list(self._projects.values())

    def update(self, project_id: str, name: Optional[str] = None) -> Project:
        """Update a project's name."""
        project = self.get(project_id)
        if name is not None:
            if not name.strip():
                raise ValueError("Project name cannot be empty")
            project.name = name.strip()
            self._persist()
        return project

    def delete(self, project_id: str) -> None:
        """Delete a project. Tasks are not deleted, just unassigned."""
        project = self.get(project_id)  # raises if not found
        del self._projects[project.id]
        self._persist()
