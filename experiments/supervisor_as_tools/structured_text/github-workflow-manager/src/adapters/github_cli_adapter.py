"""GitHub API client using gh CLI."""

import subprocess
import json
from typing import Optional

from .protocols import GitHubAPIClient
from ..exceptions import (
    GitHubAuthenticationError,
    GitHubRepositoryNotFoundError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubDataParseError,
)


class GhCliGitHubAdapter(GitHubAPIClient):
    """GitHub API client implementation using gh CLI."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize GhCliGitHubAdapter.

        Args:
            timeout: Request timeout in seconds (default: 30).
        """
        self.timeout = timeout

    def make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GitHub API request using gh CLI.

        Args:
            endpoint: API endpoint path (may have leading slash).
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubAuthenticationError: If authentication fails (401/403).
            GitHubRepositoryNotFoundError: If 404 response.
            GitHubAPIError: If API error occurs.
            GitHubNetworkError: If gh CLI not found or network error occurs.
            GitHubDataParseError: If response cannot be parsed as JSON.
        """
        # Remove leading slash if present (gh CLI expects no leading slash)
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]

        # Build gh api command
        cmd = ["gh", "api", endpoint]

        # Add query parameters as CLI flags
        if params:
            for key, value in params.items():
                if value is not None:
                    # Use -F for field values (automatically converts to proper JSON)
                    cmd.extend(["-F", f"{key}={value}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError:
            raise GitHubNetworkError("gh CLI not installed or not in PATH")
        except subprocess.TimeoutExpired:
            raise GitHubNetworkError("gh CLI request timeout")

        # Check for errors in stderr or non-zero exit code
        if result.returncode != 0:
            stderr = result.stderr.lower()

            # Check for authentication errors
            if "401" in stderr or "unauthorized" in stderr:
                raise GitHubAuthenticationError(
                    "Authentication failed. Check your GitHub token or gh CLI authentication."
                )
            # Check for 403 (forbidden/rate limit)
            elif "403" in stderr or "rate limit" in stderr or "forbidden" in stderr:
                raise GitHubAuthenticationError(
                    "Authentication failed or rate limited. Check your token permissions."
                )
            # Check for 404 (not found)
            elif "404" in stderr or "not found" in stderr:
                raise GitHubRepositoryNotFoundError(
                    "Repository not found. Check owner/repo names."
                )
            # Generic API error
            else:
                raise GitHubAPIError(f"GitHub API error: {result.stderr}")

        # Parse JSON response
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise GitHubDataParseError(f"Failed to parse GitHub API response: {e}")
