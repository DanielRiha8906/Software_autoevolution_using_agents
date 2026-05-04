"""Unified TodoService combining all domain services."""

from datetime import datetime
from typing import Optional

from ..models import Task, TaskComment, Project, TaskStatus
from ..storage import JsonStorage
from .task_service import TaskService
from .comment_service import CommentService
from .project_service import ProjectService


class TodoService:
    """High-level unified service for all TODO operations."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        storage = storage or JsonStorage()
        self._task_service = TaskService(storage)
        self._comment_service = CommentService(storage)
        self._project_service = ProjectService(storage)

    # Task management
    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None, project_id: Optional[str] = None) -> Task:
        """Add a new task, optionally assigning it to a project."""
        task = self._task_service.add_task(title, description, due_date)
        if project_id:
            # Validate project exists and get the full ID
            project = self._project_service.get_project(project_id)
            task.project_id = project.id
            # Persist the updated task
            self._task_service._repository._persist()
        return task

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID."""
        return self._task_service.get_task(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        overdue: bool = False,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        """List tasks with optional filters."""
        if project_id is not None:
            # Validate project exists and get the full ID
            project = self._project_service.get_project(project_id)
            project_id = project.id
        return self._task_service.list_tasks(status, overdue, due_before, due_after, project_id)

    def start_task(self, task_id: str) -> Task:
        """Mark a task as in-progress."""
        return self._task_service.start_task(task_id)

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as done."""
        return self._task_service.complete_task(task_id)

    def reopen_task(self, task_id: str) -> Task:
        """Mark a task as pending."""
        return self._task_service.reopen_task(task_id)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        """Update a task."""
        return self._task_service.update_task(task_id, title, description, due_date)

    def delete_task(self, task_id: str) -> None:
        """Delete a task and cascade delete its comments."""
        # Get the full task ID (in case a prefix was provided)
        task = self.get_task(task_id)
        # Cascade delete: remove comments for this task
        self._comment_service.delete_comments_by_task(task.id)
        # Delete the task
        self._task_service.delete_task(task.id)

    # Comment management
    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task."""
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self.get_task(task_id)
        return self._comment_service.add_comment(task.id, content, author)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List comments for a task."""
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self.get_task(task_id)
        return self._comment_service.list_comments(task.id)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID."""
        return self._comment_service.get_comment(comment_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        self._comment_service.delete_comment(comment_id)

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment."""
        return self._comment_service.update_comment(comment_id, content)

    # Project management
    def add_project(self, name: str) -> Project:
        """Create a new project."""
        return self._project_service.add_project(name)

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID."""
        return self._project_service.get_project(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return self._project_service.list_projects()

    def update_project(self, project_id: str, name: str) -> Project:
        """Update a project."""
        return self._project_service.update_project(project_id, name)

    def delete_project(self, project_id: str) -> None:
        """Delete a project. Tasks in the project become unassigned."""
        # Unassign tasks from this project
        project = self._project_service.get_project(project_id)
        tasks = self._task_service._repository.list_by_project(project.id)
        for task in tasks:
            task.project_id = None
        if tasks:
            self._task_service._repository._persist()
        # Delete the project
        self._project_service.delete_project(project.id)
