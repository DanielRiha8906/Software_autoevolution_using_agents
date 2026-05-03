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
        project_dicts = self._storage.load_projects()
        for data in project_dicts:
            p = Project.from_dict(data)
            self._projects[p.id] = p

    def _persist(self) -> None:
        projects_dicts = [p.to_dict() for p in self._projects.values()]
        self._storage.save_projects(projects_dicts)

    def add(self, name: str) -> Project:
        p = Project(name=name)
        self._projects[p.id] = p
        self._persist()
        return p

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

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()
