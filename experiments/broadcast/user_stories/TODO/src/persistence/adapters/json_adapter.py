"""JSON adapter implementations for repositories."""

from typing import Optional

from ...models.task import Task
from ...models.task_comment import TaskComment
from ...models.project import Project
from ...models.task_status import TaskStatus
from ...storage.json_storage import JsonStorage
from ..repositories import TaskRepository, CommentRepository, ProjectRepository


class TaskNotFoundError(Exception):
    """Exception raised when a task is not found."""
    pass


class CommentNotFoundError(Exception):
    """Exception raised when a comment is not found."""
    pass


class ProjectNotFoundError(Exception):
    """Exception raised when a project is not found."""
    pass


class JsonTaskRepository(TaskRepository):
    """JSON-based implementation of TaskRepository."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        """Load tasks from storage."""
        raw = self._storage.load()
        self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Persist tasks to storage."""
        self._storage.save([t.to_dict() for t in self._tasks.values()])

    def add(self, task: Task) -> Task:
        """Add a new task."""
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
        """Get a task by ID (supports prefix lookup)."""
        if task_id in self._tasks:
            return self._tasks[task_id]
        # Support short prefix lookup
        matches = [t for tid, t in self._tasks.items() if tid.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFoundError(f"Ambiguous prefix '{task_id}' matches {len(matches)} tasks")
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks by status."""
        return [t for t in self._tasks.values() if t.status == status]

    def list_by_project(self, project_id: str) -> list[Task]:
        """List tasks by project ID."""
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def list_unassigned(self) -> list[Task]:
        """List tasks not assigned to any project."""
        return [t for t in self._tasks.values() if t.project_id is None]

    def update(self, task: Task) -> Task:
        """Update an existing task."""
        if task.id not in self._tasks:
            raise TaskNotFoundError(f"Task '{task.id}' not found")
        self._tasks[task.id] = task
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        """Delete a task by ID."""
        task = self.get(task_id)  # resolves prefix; raises if missing
        del self._tasks[task.id]
        self._persist()


class JsonCommentRepository(CommentRepository):
    """JSON-based implementation of CommentRepository."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage."""
        raw = self._storage.load_comments()
        self._comments = {c["id"]: TaskComment.from_dict(c) for c in raw}

    def _persist(self) -> None:
        """Persist comments to storage."""
        comments_raw = [c.to_dict() for c in self._comments.values()]
        # Load tasks to preserve them
        tasks_raw = self._storage.load()
        self._storage.save_all(tasks_raw, comments_raw)

    def add(self, comment: TaskComment) -> TaskComment:
        """Add a new comment."""
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def get(self, comment_id: str) -> TaskComment:
        """Get a comment by ID (supports prefix lookup)."""
        if comment_id in self._comments:
            return self._comments[comment_id]
        # Support short prefix lookup
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments")
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def list_for_task(self, task_id: str) -> list[TaskComment]:
        """List comments for a specific task, ordered by created_at."""
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def list_all(self) -> list[TaskComment]:
        """List all comments."""
        return list(self._comments.values())

    def update(self, comment: TaskComment) -> TaskComment:
        """Update an existing comment."""
        if comment.id not in self._comments:
            raise CommentNotFoundError(f"Comment '{comment.id}' not found")
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def delete(self, comment_id: str) -> None:
        """Delete a comment by ID."""
        comment = self.get(comment_id)  # resolves prefix; raises if missing
        del self._comments[comment.id]
        self._persist()

    def delete_by_task_id(self, task_id: str) -> None:
        """Delete all comments for a specific task."""
        self._comments = {
            cid: c for cid, c in self._comments.items() if c.task_id != task_id
        }
        self._persist()


class JsonProjectRepository(ProjectRepository):
    """JSON-based implementation of ProjectRepository."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        """Load projects from storage."""
        raw = self._storage.load_projects()
        self._projects = {d["id"]: Project.from_dict(d) for d in raw}

    def _persist(self) -> None:
        """Persist projects to storage."""
        self._storage.save_projects([p.to_dict() for p in self._projects.values()])

    def add(self, project: Project) -> Project:
        """Add a new project."""
        self._projects[project.id] = project
        self._persist()
        return project

    def get(self, project_id: str) -> Project:
        """Get a project by ID (supports prefix lookup)."""
        if project_id in self._projects:
            return self._projects[project_id]
        # Support short prefix lookup
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    def list_all(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())

    def update(self, project: Project) -> Project:
        """Update an existing project."""
        if project.id not in self._projects:
            raise ProjectNotFoundError(f"Project '{project.id}' not found")
        self._projects[project.id] = project
        self._persist()
        return project

    def delete(self, project_id: str) -> None:
        """Delete a project by ID."""
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()


__all__ = ["JsonTaskRepository", "JsonCommentRepository", "JsonProjectRepository"]
