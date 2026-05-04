"""GitHub adapter module for API integrations."""

from .api_fetcher import GitHubAPIFetcher
from .cli_fetcher import GitHubCLIFetcher
from .factory import GitHubWorkflowRunFactory
from .auth import GitHubAuthManager
from .exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)
from .base import WorkflowFetcher

__all__ = [
    "GitHubAPIFetcher",
    "GitHubCLIFetcher",
    "GitHubWorkflowRunFactory",
    "GitHubAuthManager",
    "GitHubAuthError",
    "GitHubAPIError",
    "GitHubNetworkError",
    "GitHubRateLimitError",
    "WorkflowFetcher",
]
