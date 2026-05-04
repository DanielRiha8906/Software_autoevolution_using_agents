"""Service layer exceptions."""


class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass


class TaskNotFoundError(ServiceError):
    """Raised when a task is not found."""
    pass


class ProjectNotFoundError(ServiceError):
    """Raised when a project is not found."""
    pass
