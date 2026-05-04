"""Persistence layer - separates storage concerns from domain logic.

This layer provides adapters for handling entity persistence,
keeping storage details outside domain models and services.
"""

from .task_adapter import TaskPersistenceAdapter
from .comment_adapter import CommentPersistenceAdapter
from .project_adapter import ProjectPersistenceAdapter

__all__ = [
    "TaskPersistenceAdapter",
    "CommentPersistenceAdapter",
    "ProjectPersistenceAdapter",
]
