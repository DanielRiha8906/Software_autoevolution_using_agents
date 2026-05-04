"""Comment domain layer.

This module contains comment-specific business logic, separated from storage and interface concerns.
"""

from .comment_repository import CommentRepository as CommentRepositoryImpl
from .comment_repository import CommentNotFoundError

__all__ = [
    "CommentRepositoryImpl",
    "CommentNotFoundError",
]
