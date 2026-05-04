from abc import ABC, abstractmethod


class Storage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    def load(self) -> list[dict]:
        """Load all tasks.

        Returns:
            List of task dictionaries.
        """
        pass

    @abstractmethod
    def save(self, tasks: list[dict]) -> None:
        """Save all tasks.

        Args:
            tasks: List of task dictionaries.
        """
        pass

    @abstractmethod
    def load_comments(self) -> list[dict]:
        """Load all comments.

        Returns:
            List of comment dictionaries.
        """
        pass

    @abstractmethod
    def save_comments(self, comments: list[dict]) -> None:
        """Save all comments.

        Args:
            comments: List of comment dictionaries.
        """
        pass

    @abstractmethod
    def load_projects(self) -> list[dict]:
        """Load all projects.

        Returns:
            List of project dictionaries.
        """
        pass

    @abstractmethod
    def save_projects(self, projects: list[dict]) -> None:
        """Save all projects.

        Args:
            projects: List of project dictionaries.
        """
        pass
