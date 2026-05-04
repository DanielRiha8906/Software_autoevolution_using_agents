"""Concrete repository implementations using JSON storage."""

from datetime import datetime, timezone
from typing import Optional

from ..models import Task, TaskComment, Project, TaskStatus, CEST
from ..storage import JsonStorage


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    pass


class CommentNotFoundError(Exception):
    """Raised when a comment is not found."""
    pass


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""
    pass


class JsonTaskRepository:
    """JSON-based repository for task persistence."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        # Handle both formats: list (legacy) or dict (with tasks/comments)
        if isinstance(raw, dict):
            task_list = raw.get("tasks", [])
        else:
            task_list = raw if isinstance(raw, list) else []
        self._tasks = {d["id"]: Task.from_dict(d) for d in task_list}

    def _persist(self) -> None:
        raw = self._storage.load()
        # Preserve existing structure (with comments if present)
        if isinstance(raw, dict):
            raw["tasks"] = [t.to_dict() for t in self._tasks.values()]
        else:
            raw = [t.to_dict() for t in self._tasks.values()]
        self._storage.save(raw)

    def add(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        task = Task(title=title, description=description, due_date=due_date)
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
        if task_id in self._tasks:
            return self._tasks[task_id]
        # support short prefix lookup (e.g. first 8 chars shown by list)
        matches = [t for tid, t in self._tasks.items() if tid.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFoundError(f"Ambiguous prefix '{task_id}' matches {len(matches)} tasks")
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    def list_by_project(self, project_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def list_overdue(self) -> list[Task]:
        """Return all tasks that are overdue (due_date is set and earlier than current CEST time)."""
        return [t for t in self._tasks.values() if t.is_overdue()]

    def list_by_due_date_range(self, before: Optional[datetime] = None, after: Optional[datetime] = None) -> list[Task]:
        """Return tasks with due_date in the specified range.

        Args:
            before: Only include tasks with due_date <= this datetime
            after: Only include tasks with due_date >= this datetime

        Returns:
            List of tasks matching the criteria (those with due_date set)
        """
        result = []
        for task in self._tasks.values():
            if task.due_date is None:
                continue
            if before is not None and task.due_date > before:
                continue
            if after is not None and task.due_date < after:
                continue
            result.append(task)
        return result

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        task = self.get(task_id)
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        task = self.get(task_id)  # resolves prefix; raises if missing
        del self._tasks[task.id]
        self._persist()


class JsonCommentRepository:
    """JSON-based repository for comment persistence."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._comments: dict[str, TaskComment] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from storage."""
        raw = self._storage.load()
        # Filter for comment objects (they have task_id field)
        # We'll store comments in a separate structure
        self._comments = {}
        if isinstance(raw, dict) and "comments" in raw:
            for c in raw.get("comments", []):
                comment = TaskComment.from_dict(c)
                self._comments[comment.id] = comment

    def _persist(self) -> None:
        """Persist comments to storage."""
        raw = self._storage.load()
        # Preserve existing tasks and structure
        if not isinstance(raw, dict):
            raw = {"tasks": raw if raw else []}
        if "tasks" not in raw:
            raw["tasks"] = [t for t in raw] if isinstance(raw, list) else []

        raw["comments"] = [c.to_dict() for c in self._comments.values()]
        self._storage.save(raw)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to add the comment to
            content: The comment content
            author: Optional author name

        Returns:
            The created TaskComment

        Raises:
            ValueError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        comment = TaskComment(
            task_id=task_id,
            content=content.strip(),
            author=author
        )
        self._comments[comment.id] = comment
        self._persist()
        return comment

    def list_comments_by_task(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at ascending.

        Args:
            task_id: The ID of the task

        Returns:
            List of TaskComment objects ordered by created_at
        """
        comments = [c for c in self._comments.values() if c.task_id == task_id]
        return sorted(comments, key=lambda c: c.created_at)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID.

        Args:
            comment_id: The ID of the comment (exact match or unique prefix)

        Returns:
            The TaskComment object

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
        """
        if comment_id in self._comments:
            return self._comments[comment_id]
        # Support prefix lookup (e.g. first 8 chars shown by list)
        matches = [c for cid, c in self._comments.items() if cid.startswith(comment_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommentNotFoundError(f"Ambiguous prefix '{comment_id}' matches {len(matches)} comments")
        raise CommentNotFoundError(f"Comment '{comment_id}' not found")

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment to delete (exact match or unique prefix)

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
        """
        comment = self.get_comment(comment_id)  # raises if not found, resolves prefix
        del self._comments[comment.id]
        self._persist()

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment's content and set updated_at timestamp.

        Args:
            comment_id: The ID of the comment to update (exact match or unique prefix)
            content: The new comment content

        Returns:
            The updated TaskComment

        Raises:
            CommentNotFoundError: If the comment is not found or prefix is ambiguous
            ValueError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        comment = self.get_comment(comment_id)  # raises if not found, resolves prefix
        comment.content = content.strip()
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment

    def delete_comments_by_task(self, task_id: str) -> None:
        """Delete all comments for a task (cascade delete).

        Args:
            task_id: The ID of the task whose comments should be deleted
        """
        comment_ids = [c.id for c in self._comments.values() if c.task_id == task_id]
        for comment_id in comment_ids:
            del self._comments[comment_id]
        if comment_ids:
            self._persist()


class JsonProjectRepository:
    """JSON-based repository for project persistence."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        # Handle both formats: list (legacy) or dict (with tasks/comments/projects)
        if isinstance(raw, dict):
            project_list = raw.get("projects", [])
        else:
            project_list = []
        self._projects = {d["id"]: Project.from_dict(d) for d in project_list}

    def _persist(self) -> None:
        raw = self._storage.load()
        # Preserve existing structure (with tasks/comments if present)
        if isinstance(raw, dict):
            raw["projects"] = [p.to_dict() for p in self._projects.values()]
        else:
            raw = {"projects": [p.to_dict() for p in self._projects.values()]}
        self._storage.save(raw)

    def add(self, name: str) -> Project:
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = Project(name=name.strip())
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

    def update(self, project_id: str, name: str) -> Project:
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        project = self.get(project_id)
        project.name = name.strip()
        self._persist()
        return project

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)  # resolves prefix; raises if missing
        del self._projects[project.id]
        self._persist()
