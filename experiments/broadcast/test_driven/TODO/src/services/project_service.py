from typing import TYPE_CHECKING, Optional

from ..models.project import Project
from ..persistence.project_adapter import ProjectPersistenceAdapter

if TYPE_CHECKING:
    from .todo_service import TodoService


class ProjectService:
    """Project management service - manages project lifecycle and persistence.

    Responsibility:
    - Project creation and retrieval
    - Project persistence to storage
    - Coordination with task storage for coexistence

    Separation from persistence:
    - Uses ProjectPersistenceAdapter to delegate storage operations
    - Accesses storage via TodoService to maintain consistency
    """

    _PROJECTS_KEY = "__projects__"

    def __init__(self, todo_service: "TodoService") -> None:
        """Initialize ProjectService with a TodoService instance."""
        self._todo_service = todo_service
        self._adapter = ProjectPersistenceAdapter(self._todo_service.get_storage())
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage using the persistence adapter."""
        self._projects = self._adapter.load()

    def _persist(self) -> None:
        """Persist projects to storage using the persistence adapter."""
        self._adapter.save(self._projects)

    def create(self, name: str) -> Project:
        """Create a new project."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name)
        self._projects[project.id] = project
        self._persist()
        return project

    def list(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())
