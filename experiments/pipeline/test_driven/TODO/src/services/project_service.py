from typing import Optional

from ..models.project import Project
from ..storage.json_storage import JsonStorage


class ProjectNotFoundError(Exception):
    pass


class ProjectService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load_projects()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save_projects([p.to_dict() for p in self._projects.values()])

    def create(self, name: str, description: Optional[str] = None) -> Project:
        project = Project(name=name, description=description)
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
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
        return sorted(list(self._projects.values()), key=lambda p: p.created_at)

    def update(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Project:
        project = self.get(project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        self._persist()
        return project

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)
        del self._projects[project.id]
        self._persist()
