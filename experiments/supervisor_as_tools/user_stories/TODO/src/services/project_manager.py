from datetime import datetime, timezone
from typing import Optional

from ..models.project import Project
from ..storage.repositories import ProjectRepository
from ..storage.project_storage import ProjectStorage


class ProjectNotFoundError(Exception):
    pass


class ProjectManager:
    def __init__(self, storage: Optional[ProjectRepository] = None) -> None:
        self._storage = storage or ProjectStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([p.to_dict() for p in self._projects.values()])

    def add(self, name: str, description: Optional[str] = None) -> Project:
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name.strip(), description=description)
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
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
        return list(self._projects.values())

    def update(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Project:
        project = self.get(project_id)
        if name is not None:
            if not name.strip():
                raise ValueError("Project name cannot be empty")
            project.name = name.strip()
        if description is not None:
            project.description = description
        project.updated_at = datetime.now(timezone.utc)
        self._persist()
        return project

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()
