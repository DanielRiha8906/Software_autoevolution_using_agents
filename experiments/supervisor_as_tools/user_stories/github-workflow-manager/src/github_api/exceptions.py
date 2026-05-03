"""GitHub API exceptions."""


class GitHubApiError(Exception):
    """Base exception for GitHub API errors."""

    pass


class TokenResolutionError(Exception):
    """Raised when GitHub token cannot be resolved from any source."""

    pass


class GitHubImportError(Exception):
    """Raised when GitHub import operation fails."""

    pass
