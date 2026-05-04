"""Domain layer containing business logic and repositories.

This layer is independent of storage implementation details through
the use of the StorageProtocol. It manages core operations for tasks,
projects, and comments.
"""

from .exceptions import TaskNotFoundError, ProjectNotFoundError, CommentNotFoundError
from .task_repository import TaskRepository
from .project_repository import ProjectRepository
from .comment_repository import CommentRepository
from .task_domain_service import TaskDomainService
from .project_domain_service import ProjectDomainService
from .comment_domain_service import CommentDomainService

__all__ = [
    "TaskNotFoundError",
    "ProjectNotFoundError",
    "CommentNotFoundError",
    "TaskRepository",
    "ProjectRepository",
    "CommentRepository",
    "TaskDomainService",
    "ProjectDomainService",
    "CommentDomainService",
]
