"""TODO application - a simple task management system.

Layered Architecture:
    - layers/models/: Domain models (Task, TaskComment, Project, TaskStatus)
    - layers/storage/: Storage abstractions (StorageProtocol) and implementations (JsonStorage)
    - layers/repositories/: Repository patterns for data access
    - layers/services/: Domain services and business logic
    - cli/: Command-line interface (TodoCLI, InteractiveMenu)

Main entry point:
    Use 'python -m src' to run interactively or with CLI flags.

Public API:
    - TodoService: Main service for all operations
    - JsonStorage: Storage implementation
    - Domain models from layers.models
"""

from .layers.services.todo_service import TodoService
from .layers.storage.json_storage import JsonStorage
from .layers.models import Task, TaskStatus, Project, TaskComment, CEST
from .layers.storage import StorageProtocol

__all__ = [
    "TodoService",
    "JsonStorage",
    "Task",
    "TaskStatus",
    "Project",
    "TaskComment",
    "CEST",
    "StorageProtocol",
]
