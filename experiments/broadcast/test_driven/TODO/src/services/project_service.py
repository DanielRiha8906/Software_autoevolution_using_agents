from typing import TYPE_CHECKING, Optional

from ..models.project import Project

if TYPE_CHECKING:
    from .todo_service import TodoService


class ProjectService:
    _PROJECTS_KEY = "__projects__"

    def __init__(self, todo_service: "TodoService") -> None:
        """Initialize ProjectService with a TodoService instance."""
        self._todo_service = todo_service
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        storage = self._todo_service._manager._storage
        raw = storage.load()
        if isinstance(raw, dict):
            projects_data = raw.get(self._PROJECTS_KEY, [])
        else:
            projects_data = []
        self._projects = {p["id"]: Project.from_dict(p) for p in projects_data}

    def _persist(self) -> None:
        """Persist projects to storage."""
        storage = self._todo_service._manager._storage
        raw = storage.load()
        # Convert to dict format if needed (to accommodate both tasks and projects)
        if isinstance(raw, list):
            # Current format is a list of tasks, convert to dict
            raw = {"__tasks__": raw}
        else:
            # Already dict, update __tasks__ with current tasks
            raw["__tasks__"] = [t.to_dict() for t in self._todo_service._manager._tasks.values()]
        # Add/update projects
        raw[self._PROJECTS_KEY] = [p.to_dict() for p in self._projects.values()]
        storage.save(raw)

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
