"""TODO application - task management system.

Layered architecture with clear separation of concerns:
- models/: Data domain models
- protocols.py: Storage and repository abstractions
- *_domain/: Domain repositories for task, comment, and project layers
- storage/: Persistence implementations (JSON backend)
- services/: Business logic layer
- cli/: User interface layer
"""

from .services.todo_service import TodoService
from .storage.json_storage import JsonStorage

__all__ = ["TodoService", "JsonStorage"]
