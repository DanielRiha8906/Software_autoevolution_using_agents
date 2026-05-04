from typing import Optional

from ..models.project import Project
from ..storage.json_storage import JsonStorage


class ProjectNotFoundError(Exception):
    pass


class ProjectService:
    def __init__(self, todo_service=None, storage: Optional[JsonStorage] = None, storage_path: Optional[str] = None) -> None:
        """Initialize ProjectService with optional TodoService and custom storage.

        Args:
            todo_service: Optional TodoService instance (for test fixture pattern).
            storage: Optional JsonStorage instance. Defaults to ~/.todo_projects.json.
            storage_path: Optional path for JsonStorage. Used if storage is not provided.
        """
        if storage:
            self._storage = storage
        elif storage_path:
            self._storage = JsonStorage(path=storage_path)
        else:
            self._storage = JsonStorage(path=str(JsonStorage().path.parent / ".todo_projects.json"))
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        raw = self._storage.load()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Save projects to storage."""
        self._storage.save([p.to_dict() for p in self._projects.values()])

    def create(self, name: str) -> Project:
        """Create a new project.

        Args:
            name: The project name (validated by Project.__init__).

        Returns:
            The newly created Project.

        Raises:
            ValueError: If name is empty or whitespace-only.
        """
        project = Project(name=name)
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """Get a project by ID.

        Args:
            project_id: The project ID.

        Returns:
            The Project instance.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        if project_id in self._projects:
            return self._projects[project_id]
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list(self) -> list[Project]:
        """List all projects.

        Returns:
            A list of all projects.
        """
        return list(self._projects.values())

    def delete(self, project_id: str) -> None:
        """Delete a project by ID.

        Args:
            project_id: The project ID.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        project = self.get(project_id)  # Validate exists
        del self._projects[project.id]
        self._persist()
