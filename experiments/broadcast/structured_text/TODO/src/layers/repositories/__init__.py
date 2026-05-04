"""Repository layer - abstract interfaces and concrete implementations for data persistence."""

from .protocols import TaskRepository, CommentRepository, ProjectRepository
from .json_repositories import (
    JsonTaskRepository,
    JsonCommentRepository,
    JsonProjectRepository,
    TaskNotFoundError,
    CommentNotFoundError,
    ProjectNotFoundError,
)

__all__ = [
    # Protocols
    "TaskRepository",
    "CommentRepository",
    "ProjectRepository",
    # Concrete implementations
    "JsonTaskRepository",
    "JsonCommentRepository",
    "JsonProjectRepository",
    # Exceptions
    "TaskNotFoundError",
    "CommentNotFoundError",
    "ProjectNotFoundError",
]
