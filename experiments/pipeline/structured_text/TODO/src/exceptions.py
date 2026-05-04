"""Domain exceptions for TODO application."""


class DomainError(Exception):
    """Base exception for domain-level errors."""
    pass


class TaskNotFoundError(DomainError):
    """Raised when a task is not found."""
    pass


class CommentNotFoundError(DomainError):
    """Raised when a comment is not found."""
    pass


class ProjectNotFoundError(DomainError):
    """Raised when a project is not found."""
    pass


class ImportExportError(DomainError):
    """Raised when import/export validation fails."""
    pass
