from typing import Protocol


class TaskRepository(Protocol):
    """Protocol for task storage abstraction."""

    def load(self) -> list[dict]:
        """Load tasks from storage."""
        ...

    def save(self, tasks: list[dict]) -> None:
        """Save tasks to storage."""
        ...


class CommentRepository(Protocol):
    """Protocol for comment storage abstraction."""

    def load(self) -> list[dict]:
        """Load comments from storage."""
        ...

    def save(self, comments: list[dict]) -> None:
        """Save comments to storage."""
        ...


class ProjectRepository(Protocol):
    """Protocol for project storage abstraction."""

    def load(self) -> list[dict]:
        """Load projects from storage."""
        ...

    def save(self, projects: list[dict]) -> None:
        """Save projects to storage."""
        ...
