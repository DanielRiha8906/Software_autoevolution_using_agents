"""Abstract base classes for adapters."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class GitHubAPIClient(ABC):
    """Abstract base class for GitHub API client implementations."""

    @abstractmethod
    def make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GitHub API request.

        Args:
            endpoint: API endpoint path (may have leading slash).
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubAuthenticationError: If authentication fails (401/403).
            GitHubRepositoryNotFoundError: If 404 response.
            GitHubAPIError: If API error occurs.
            GitHubNetworkError: If network error occurs.
            GitHubDataParseError: If response cannot be parsed as JSON.
        """
        pass


class GitHubDataMapper(ABC):
    """Abstract base class for GitHub data mapping."""

    @abstractmethod
    def parse_datetime(self, iso_string: str) -> Any:
        """Parse ISO 8601 datetime string from GitHub API.

        Args:
            iso_string: ISO 8601 datetime string (e.g., "2026-05-03T10:30:00Z").

        Returns:
            datetime object with UTC timezone.
        """
        pass

    @abstractmethod
    def map_github_run_to_workflow_run(self, github_run: dict) -> Any:
        """Map GitHub API run object to WorkflowRun model.

        Args:
            github_run: GitHub API run response object.

        Returns:
            WorkflowRun instance.
        """
        pass


class FileHandler(ABC):
    """Abstract base class for file I/O operations."""

    @abstractmethod
    def export_to_file(self, data: dict, output_path: str) -> str:
        """Export data to a file.

        Args:
            data: Data to export.
            output_path: Path to write the export file.

        Returns:
            Path to the written file.

        Raises:
            IOError: If file cannot be written.
        """
        pass

    @abstractmethod
    def import_from_file(self, input_path: str) -> dict:
        """Import data from a file.

        Args:
            input_path: Path to read the import file from.

        Returns:
            Imported data as dictionary.

        Raises:
            IOError: If file cannot be read.
            ValueError: If file contents are invalid.
        """
        pass
