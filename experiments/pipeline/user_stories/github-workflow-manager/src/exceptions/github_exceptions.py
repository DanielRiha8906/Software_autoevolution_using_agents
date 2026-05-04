"""GitHub-related exceptions for fetch operations."""


class GitHubAuthError(Exception):
    """Raised when authentication fails (invalid/expired token)."""

    pass


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails."""

    pass


class GitHubNetworkError(Exception):
    """Raised when network connection fails."""

    pass


class GitHubRateLimitError(Exception):
    """Raised when GitHub API rate limit is exceeded."""

    pass
