from typing import Optional
from pathlib import Path

from ..models.project import Project
from ..storage.json_storage import JsonStorage


class ProjectNotFoundError(Exception):
    pass


def _derive_projects_path(task_path: Path) -> Path:
    """Derive the projects file path from the task storage path.

    Takes the directory of the task path and replaces the filename with
    .todo_projects.json.

    Args:
        task_path: Path to the task storage file

    Returns:
        Path to the projects storage file
    """
    return task_path.parent / ".todo_projects.json"


class ProjectManager:
    """Manager for projects with CRUD operations and JSON persistence.

    Stores projects in a separate JSON file (default: ~/.todo_projects.json).
    Maintains an in-memory dict of projects, persisting after mutations.
    """

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        """Initialize ProjectManager with optional custom storage.

        Args:
            storage: JsonStorage instance. If None, uses default path ~/.todo_projects.json
        """
        self._storage = storage or JsonStorage(path=None)  # Will get default path from JsonStorage
        # Override to use projects file derived from task storage path
        self._storage._path = _derive_projects_path(self._storage.path)
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load all projects from storage into memory."""
        raw = self._storage.load()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Save all projects from memory to storage."""
        self._storage.save([p.to_dict() for p in self._projects.values()])

    def add(self, name: str) -> Project:
        """Add a new project.

        Args:
            name: Project name (required, non-empty after validation)

        Returns:
            The created Project instance

        Raises:
            ValueError: If name is empty or whitespace-only
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name.strip())
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """Get a project by ID or ID prefix.

        Args:
            project_id: Full project ID or unique prefix (e.g., first 8 chars)

        Returns:
            The Project instance

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        if project_id in self._projects:
            return self._projects[project_id]
        # support short prefix lookup
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list_all(self) -> list[Project]:
        """Get all projects.

        Returns:
            List of Project instances
        """
        return list(self._projects.values())

    def delete(self, project_id: str) -> None:
        """Delete a project by ID or ID prefix.

        Args:
            project_id: Full project ID or unique prefix

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()

    def update(self, project_id: str, name: str) -> Project:
        """Update a project's name.

        Args:
            project_id: Full project ID or unique prefix
            name: New project name (required, non-empty after validation)

        Returns:
            The updated Project instance

        Raises:
            ValueError: If name is empty or whitespace-only
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = self.get(project_id)
        project.name = name.strip()
        self._persist()
        return project
