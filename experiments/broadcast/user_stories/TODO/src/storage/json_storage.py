"""JSON-based storage backend implementation."""

import json
from pathlib import Path
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.project import Project


class JsonStorage:
    """
    JSON file-based storage backend.

    Implements StorageBackend protocol and manages persistence of tasks,
    comments, and projects in a single JSON file.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"
        self._cached_comments: list[dict] = []
        self._cached_projects: list[dict] = []

    @property
    def path(self) -> Path:
        """Get the storage file path."""
        return self._path

    def load(self) -> list[dict]:
        """Load raw task data from storage (legacy interface for compatibility)."""
        if not self._path.exists():
            self._cached_comments = []
            self._cached_projects = []
            return []
        try:
            with self._path.open("r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    self._cached_comments = []
                    self._cached_projects = []
                    return []
                data = json.loads(content)
                # Support legacy format (list of tasks) and new format (dict with tasks, comments, projects)
                if isinstance(data, list):
                    self._cached_comments = []
                    self._cached_projects = []
                    return data
                elif isinstance(data, dict) and "tasks" in data:
                    self._cached_comments = data.get("comments", [])
                    self._cached_projects = data.get("projects", [])
                    return data["tasks"]
                return []
        except (json.JSONDecodeError, ValueError):
            self._cached_comments = []
            self._cached_projects = []
            return []

    def save(self, tasks: list[dict]) -> None:
        """Save tasks, preserving any cached comments and projects."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Always use the unified format
        data = {"tasks": tasks, "comments": self._cached_comments, "projects": self._cached_projects}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_tasks(self) -> list[Task]:
        """Load all tasks from storage (StorageBackend protocol)."""
        raw = self.load()
        return [Task.from_dict(d) for d in raw]

    def save_tasks(self, tasks: list[Task]) -> None:
        """Save all tasks to storage (StorageBackend protocol)."""
        self.save([t.to_dict() for t in tasks])

    def load_comments(self) -> list[dict] | list[TaskComment]:
        """Load all comments from storage."""
        if not self._path.exists():
            self._cached_comments = []
            return []
        try:
            with self._path.open("r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    self._cached_comments = []
                    return []
                data = json.loads(content)
                # Support new format (dict with tasks and comments)
                if isinstance(data, dict) and "comments" in data:
                    self._cached_comments = data["comments"]
                    return data["comments"]
                self._cached_comments = []
                return []
        except (json.JSONDecodeError, ValueError):
            self._cached_comments = []
            return []

    def save_comments(self, comments: list[TaskComment] | list[dict]) -> None:
        """Save comments to storage (StorageBackend protocol)."""
        if not comments:
            self._cached_comments = []
        elif isinstance(comments[0] if comments else None, TaskComment):
            self._cached_comments = [c.to_dict() for c in comments]
        else:
            self._cached_comments = comments
        # Preserve current tasks and projects
        self._path.parent.mkdir(parents=True, exist_ok=True)
        current_data = {"tasks": [], "comments": [], "projects": []}
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        current_data = json.loads(content)
                        if not isinstance(current_data, dict):
                            current_data = {"tasks": [], "comments": [], "projects": []}
            except (json.JSONDecodeError, ValueError):
                pass
        data = {
            "tasks": current_data.get("tasks", []),
            "comments": self._cached_comments,
            "projects": current_data.get("projects", []),
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_all(self, tasks: list[dict], comments: list[dict]) -> None:
        """Save both tasks and comments to storage."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cached_comments = comments
        data = {"tasks": tasks, "comments": comments, "projects": self._cached_projects}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_projects(self) -> list[dict] | list[Project]:
        """Load all projects from storage."""
        if not self._path.exists():
            self._cached_projects = []
            return []
        try:
            with self._path.open("r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    self._cached_projects = []
                    return []
                data = json.loads(content)
                # Support new format (dict with tasks and projects)
                if isinstance(data, dict) and "projects" in data:
                    self._cached_projects = data["projects"]
                    return data["projects"]
                self._cached_projects = []
                return []
        except (json.JSONDecodeError, ValueError):
            self._cached_projects = []
            return []

    def save_projects(self, projects: list[Project] | list[dict]) -> None:
        """Save projects to storage (StorageBackend protocol)."""
        if not projects:
            self._cached_projects = []
        elif isinstance(projects[0] if projects else None, Project):
            self._cached_projects = [p.to_dict() for p in projects]
        else:
            self._cached_projects = projects
        # Load current data first to preserve tasks and comments
        self._path.parent.mkdir(parents=True, exist_ok=True)
        current_data = {}
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        current_data = json.loads(content)
                        if not isinstance(current_data, dict):
                            current_data = {}
            except (json.JSONDecodeError, ValueError):
                current_data = {}
        # Always use the unified format
        data = {
            "tasks": current_data.get("tasks", []),
            "comments": current_data.get("comments", []),
            "projects": self._cached_projects,
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
