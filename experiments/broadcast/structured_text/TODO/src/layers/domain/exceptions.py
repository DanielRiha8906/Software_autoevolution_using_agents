"""Domain layer exceptions."""


class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""

    pass


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""

    pass


class CommentNotFoundError(Exception):
    """Raised when a comment cannot be found."""

    pass
