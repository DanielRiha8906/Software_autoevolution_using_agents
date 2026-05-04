"""Repository for persisting and retrieving projects."""

from typing import Optional

from ..models.project import Project
from ..storage.protocols import StorageProtocol
from .exceptions import ProjectNotFoundError


class ProjectRepository:
    """Repository managing project persistence and retrieval.

    Uses StorageProtocol for abstraction from storage implementation.
    """

    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        raw = self._storage.load()
        # Handle both formats: list (legacy) or dict (with tasks/comments/projects)
        if isinstance(raw, dict):
            project_list = raw.get("projects", [])
        else:
            project_list = []
        self._projects = {d["id"]: Project.from_dict(d) for d in project_list}

    def _persist(self) -> None:
        """Persist projects to storage."""
        raw = self._storage.load()
        # Preserve existing structure (with tasks/comments if present)
        if isinstance(raw, dict):
            raw["projects"] = [p.to_dict() for p in self._projects.values()]
        else:
            raw = {"projects": [p.to_dict() for p in self._projects.values()]}
        self._storage.save(raw)

    def add(self, name: str) -> Project:
        """Add a new project."""
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
        # support short prefix lookup (e.g. first 8 chars shown by list)
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list_all(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())

    def update(self, project_id: str, name: str) -> Project:
        """Update a project."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = self.get(project_id)
        project.name = name.strip()
        self._persist()
        return project

    def delete(self, project_id: str) -> None:
        """Delete a project."""
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()
