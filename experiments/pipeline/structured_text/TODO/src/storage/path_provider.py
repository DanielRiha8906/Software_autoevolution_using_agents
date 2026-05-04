"""Storage path provider for deriving file paths for different entity types."""

from pathlib import Path
from typing import Optional


class StoragePathProvider:
    """Provides file paths for different storage types based on a base tasks path."""

    def __init__(self, tasks_path: Optional[str] = None) -> None:
        """Initialize path provider with optional base path.

        Args:
            tasks_path: Path to the tasks storage file. If None, uses ~/.todo_data.json
        """
        if tasks_path:
            self._tasks_path = Path(tasks_path)
        else:
            self._tasks_path = Path.home() / ".todo_data.json"

    def get_tasks_path(self) -> Path:
        """Get the path for task storage.

        Returns:
            Path to the tasks storage file
        """
        return self._tasks_path

    def get_comments_path(self) -> Path:
        """Get the path for comment storage, derived from tasks path.

        Returns:
            Path to the comments storage file
        """
        return self._tasks_path.parent / ".todo_comments.json"

    def get_projects_path(self) -> Path:
        """Get the path for project storage, derived from tasks path.

        Returns:
            Path to the projects storage file
        """
        return self._tasks_path.parent / ".todo_projects.json"
