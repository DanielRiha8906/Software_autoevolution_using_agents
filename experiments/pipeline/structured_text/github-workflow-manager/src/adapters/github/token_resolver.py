"""GitHub token resolution from environment, secrets file, or interactive prompt."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class GitHubTokenResolver:
    """Resolves GitHub tokens from multiple sources in priority order."""

    def __init__(self) -> None:
        """Initialize the token resolver."""
        pass

    def resolve(self) -> str:
        """
        Resolve GitHub token from environment, secrets file, or prompt.

        Priority:
        1. GITHUB_TOKEN environment variable
        2. secrets/.env file
        3. Interactive prompt

        Returns:
            The resolved token string.

        Raises:
            RuntimeError: If token cannot be resolved.
        """
        # Check environment variable
        token = os.getenv("GITHUB_TOKEN")
        if token:
            logger.info("Using GitHub token from GITHUB_TOKEN environment variable")
            return token

        # Check secrets/.env file
        secrets_file = "secrets/.env"
        if os.path.exists(secrets_file):
            try:
                with open(secrets_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GITHUB_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            if token:
                                logger.info("Using GitHub token from secrets/.env file")
                                return token
            except (IOError, OSError) as e:
                logger.warning(f"Failed to read secrets/.env: {e}")

        # Prompt user
        try:
            token = input("GitHub token (or press Ctrl+C to cancel): ").strip()
            if not token:
                raise RuntimeError("No token provided")
            logger.info("Using GitHub token from user input")
            return token
        except KeyboardInterrupt:
            raise RuntimeError("Token input cancelled by user")

    def validate(self, token: str, fetch_mode: str = "api") -> bool:
        """
        Validate the GitHub token by testing connectivity.

        Args:
            token: The GitHub token to validate
            fetch_mode: "api" for REST API validation, "cli" for gh CLI validation

        Returns:
            True if token is valid, False otherwise
        """
        if fetch_mode == "cli":
            return self._validate_with_cli(token)
        else:
            return self._validate_with_api(token)

    def _validate_with_cli(self, token: str) -> bool:
        """Validate token using gh CLI."""
        try:
            import subprocess
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                timeout=5,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("gh CLI not available or timed out")
            return False

    def _validate_with_api(self, token: str) -> bool:
        """Validate token using REST API."""
        try:
            import requests
            headers = {"Authorization": f"token {token}"}
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                logger.info("GitHub token validated successfully")
                return True
            elif response.status_code == 401:
                logger.warning("GitHub token validation failed: unauthorized")
                return False
            else:
                logger.warning(f"GitHub token validation returned status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Failed to validate GitHub token: {e}")
            return False
