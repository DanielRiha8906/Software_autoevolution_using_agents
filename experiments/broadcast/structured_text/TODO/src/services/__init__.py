"""Services layer - business logic coordinators.

This layer re-exports from the layers.services and repositories modules for backward compatibility
while maintaining the logical separation of concerns.

It also exports repository abstractions and concrete implementations for explicit
layer separation and testability.
"""

from ..layers.services.todo_service import TodoService
from ..layers.services.import_export_service import ImportExportService, ImportExportValidationError
from ..layers.services.statistics_service import StatisticsService
from ..layers.repositories import (
    TaskNotFoundError,
    CommentNotFoundError,
    ProjectNotFoundError,
)
from .task_manager import TaskManager
from .comments_service import CommentsService
from .project_manager import ProjectManager
from .base_repositories import TaskRepository, CommentRepository, ProjectRepository
from .unified_storage import JsonTaskRepository, JsonCommentRepository, JsonProjectRepository

__all__ = [
    "TodoService",
    "ImportExportService",
    "ImportExportValidationError",
    "StatisticsService",
    "TaskManager",
    "TaskNotFoundError",
    "CommentsService",
    "CommentNotFoundError",
    "ProjectManager",
    "ProjectNotFoundError",
    "TaskRepository",
    "CommentRepository",
    "ProjectRepository",
    "JsonTaskRepository",
    "JsonCommentRepository",
    "JsonProjectRepository",
]
