"""Project domain layer.

This module contains project-specific business logic, separated from storage and interface concerns.
"""

from .project_repository import ProjectRepository as ProjectRepositoryImpl
from .project_repository import ProjectNotFoundError

__all__ = [
    "ProjectRepositoryImpl",
    "ProjectNotFoundError",
]
