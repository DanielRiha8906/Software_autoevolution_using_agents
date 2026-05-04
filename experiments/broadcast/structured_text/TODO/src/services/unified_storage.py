"""Unified storage layer that manages all entities through repositories.

This module provides concrete implementations of the repository interfaces,
coordinating persistence across tasks, comments, and projects.
"""

from typing import Optional, Union

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.project import Project
from ..storage.json_storage import JsonStorage
from .base_repositories import TaskRepository, CommentRepository, ProjectRepository


class JsonTaskRepository(TaskRepository):
    """Task persistence via JsonStorage."""

    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage

    def load(self) -> dict[str, Task]:
        raw = self._storage.load()
        if isinstance(raw, dict):
            task_list = raw.get("tasks", [])
        else:
            task_list = raw if isinstance(raw, list) else []
        return {d["id"]: Task.from_dict(d) for d in task_list}

    def save(self, tasks: dict[str, Task]) -> None:
        raw = self._storage.load()
        if isinstance(raw, dict):
            raw["tasks"] = [t.to_dict() for t in tasks.values()]
        else:
            raw = [t.to_dict() for t in tasks.values()]
        self._storage.save(raw)

    def get(self, task_id: str) -> Optional[Task]:
        tasks = self.load()
        return tasks.get(task_id)

    def find_by_prefix(self, prefix: str) -> list[Task]:
        tasks = self.load()
        return [t for tid, t in tasks.items() if tid.startswith(prefix)]


class JsonCommentRepository(CommentRepository):
    """Comment persistence via JsonStorage."""

    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage

    def load(self) -> dict[str, TaskComment]:
        raw = self._storage.load()
        comments = {}
        if isinstance(raw, dict) and "comments" in raw:
            for c in raw.get("comments", []):
                comment = TaskComment.from_dict(c)
                comments[comment.id] = comment
        return comments

    def save(self, comments: dict[str, TaskComment]) -> None:
        raw = self._storage.load()
        if not isinstance(raw, dict):
            raw = {"tasks": raw if raw else []}
        if "tasks" not in raw:
            raw["tasks"] = []
        raw["comments"] = [c.to_dict() for c in comments.values()]
        self._storage.save(raw)

    def get(self, comment_id: str) -> Optional[TaskComment]:
        comments = self.load()
        return comments.get(comment_id)

    def find_by_prefix(self, prefix: str) -> list[TaskComment]:
        comments = self.load()
        return [c for cid, c in comments.items() if cid.startswith(prefix)]

    def find_by_task(self, task_id: str) -> list[TaskComment]:
        comments = self.load()
        result = [c for c in comments.values() if c.task_id == task_id]
        return sorted(result, key=lambda c: c.created_at)


class JsonProjectRepository(ProjectRepository):
    """Project persistence via JsonStorage."""

    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage

    def load(self) -> dict[str, Project]:
        raw = self._storage.load()
        if isinstance(raw, dict):
            project_list = raw.get("projects", [])
        else:
            project_list = []
        return {d["id"]: Project.from_dict(d) for d in project_list}

    def save(self, projects: dict[str, Project]) -> None:
        raw = self._storage.load()
        if isinstance(raw, dict):
            raw["projects"] = [p.to_dict() for p in projects.values()]
        else:
            raw = {"projects": [p.to_dict() for p in projects.values()]}
        self._storage.save(raw)

    def get(self, project_id: str) -> Optional[Project]:
        projects = self.load()
        return projects.get(project_id)

    def find_by_prefix(self, prefix: str) -> list[Project]:
        projects = self.load()
        return [p for pid, p in projects.items() if pid.startswith(prefix)]
