"""GitHub-related exceptions - backward compatibility re-export."""

from ..adapters.github.exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)

__all__ = [
    "GitHubAuthError",
    "GitHubAPIError",
    "GitHubNetworkError",
    "GitHubRateLimitError",
]
