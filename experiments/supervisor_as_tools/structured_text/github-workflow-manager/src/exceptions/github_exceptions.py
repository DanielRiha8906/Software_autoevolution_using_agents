"""GitHub API exception classes."""


class GitHubException(Exception):
    """Base exception for GitHub-related errors."""

    pass


class GitHubAuthenticationError(GitHubException):
    """Raised when authentication to GitHub API fails (401/403)."""

    pass


class GitHubRepositoryNotFoundError(GitHubException):
    """Raised when the specified GitHub repository is not found (404)."""

    pass


class GitHubAPIError(GitHubException):
    """Raised when GitHub API returns a server error (5xx)."""

    pass


class GitHubNetworkError(GitHubException):
    """Raised when a network error occurs (timeout, connection refused)."""

    pass


class GitHubDataParseError(GitHubException):
    """Raised when GitHub API response cannot be parsed as JSON."""

    pass
