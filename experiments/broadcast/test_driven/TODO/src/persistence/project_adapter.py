"""Project persistence adapter - separates project storage from domain logic."""

from typing import Any

from ..models.project import Project


class ProjectPersistenceAdapter:
    """Adapter handling project persistence operations.

    Responsibility: Manage all project storage/loading logic.
    This isolates persistence details from ProjectService domain logic.
    """

    _PROJECTS_KEY = "__projects__"

    def __init__(self, storage: Any) -> None:
        """Initialize with a storage backend.

        Args:
            storage: Storage with load() and save() methods.
        """
        self._storage = storage

    def load(self) -> dict[str, Project]:
        """Load all projects from storage.

        Returns:
            Dictionary mapping project ID to Project.
        """
        raw = self._storage.load()
        if isinstance(raw, dict):
            projects_data = raw.get(self._PROJECTS_KEY, [])
        else:
            projects_data = []
        return {p["id"]: Project.from_dict(p) for p in projects_data}

    def save(self, projects: dict[str, Project]) -> None:
        """Save all projects to storage.

        Preserves other data like tasks.

        Args:
            projects: Dictionary mapping project ID to Project.
        """
        raw = self._storage.load()
        if isinstance(raw, list):
            raw = {"__tasks__": raw}

        raw[self._PROJECTS_KEY] = [p.to_dict() for p in projects.values()]
        self._storage.save(raw)
