"""Repositories package for data persistence abstraction."""

from .base_repository import BaseRepository
from .task_repository import TaskRepository
from .comment_repository import CommentRepository
from .project_repository import ProjectRepository

__all__ = [
    "BaseRepository",
    "TaskRepository",
    "CommentRepository",
    "ProjectRepository",
]
