"""GitHub token validation."""

from .exceptions import GitHubApiError


class GitHubTokenValidator:
    """Validate GitHub tokens with basic format checking."""

    @staticmethod
    def validate(token: str) -> None:
        """Validate token format.

        GitHub tokens typically:
        - Start with specific prefixes (ghp_, ghu_, ghs_, ghr_)
        - Are non-empty strings

        Args:
            token: Token to validate

        Raises:
            GitHubApiError: If token format is invalid
        """
        if not token or not isinstance(token, str):
            raise GitHubApiError("Token must be a non-empty string")

        if len(token) < 20:
            raise GitHubApiError("Token appears too short to be a valid GitHub token")

        # Allow various token formats
        valid_prefixes = ("ghp_", "ghu_", "ghs_", "ghr_", "github_pat_")
        if not any(token.startswith(prefix) for prefix in valid_prefixes):
            # Token might still be valid (e.g., legacy personal access tokens)
            # Just ensure it's alphanumeric with some expected length
            if not all(c.isalnum() or c == "_" for c in token):
                raise GitHubApiError("Token contains invalid characters")
