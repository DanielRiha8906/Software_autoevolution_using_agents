"""Layered architecture for TODO application.

This package organizes the TODO application into distinct, decoupled layers:

1. models/: Domain models (Task, TaskComment, Project, TaskStatus, TaskStatistics)
   - Pure data classes and enums
   - No dependencies on storage or services
   - Used throughout the application

2. storage/: Persistence abstraction and implementation
   - StorageProtocol: Abstract interface for persistence
   - JsonStorage: Concrete JSON file implementation
   - Technology-independent interface

3. repositories/: Data access patterns
   - Repository protocols: TaskRepository, CommentRepository, ProjectRepository
   - Concrete implementations: JsonTaskRepository, JsonCommentRepository, JsonProjectRepository
   - Decouples domain logic from storage details

4. services/: Domain services and business logic
   - TaskService: Task-specific operations
   - CommentService: Comment-specific operations
   - ProjectService: Project-specific operations
   - StatisticsService: Aggregated metrics
   - ImportExportService: Data exchange
   - TodoService: Unified high-level service combining all operations

The architecture ensures:
- No circular dependencies between layers
- Clear separation of concerns
- Easy testing and mocking
- Technology-agnostic domain logic
- Protocol-based abstraction for repositories and storage
"""

from . import models
from . import storage
from . import repositories
from . import services

__all__ = ["models", "storage", "repositories", "services"]
