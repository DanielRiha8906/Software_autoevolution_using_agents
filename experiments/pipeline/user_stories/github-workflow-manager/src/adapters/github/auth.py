"""GitHub authentication and token management."""

import os
import re
from getpass import getpass
from pathlib import Path
from typing import Optional

from .exceptions import GitHubAuthError


class GitHubAuthManager:
    """Manage GitHub authentication tokens with multi-source resolution."""

    SECRETS_FILE_PATH = "secrets/.env"
    TOKEN_ENV_VAR = "GITHUB_TOKEN"
    TOKEN_PREFIX_PATTERN = r"^gh[puso]_[A-Za-z0-9_]{36,255}$"

    def get_token(self, explicit_token: Optional[str] = None) -> str:
        """
        Resolve GitHub Personal Access Token with priority order.

        Attempts to get a token in the following priority order:
        1. Explicit token passed as argument (highest priority)
        2. GITHUB_TOKEN environment variable
        3. Token from secrets/.env file
        4. Secure user prompt (not saved to disk)

        Args:
            explicit_token: Explicitly provided token (e.g., from CLI --token flag).
                           If provided, all other sources are skipped.

        Returns:
            A valid GitHub Personal Access Token string.

        Raises:
            GitHubAuthError: If no token can be resolved or all sources are unavailable.
        """
        # 1. Explicit token has highest priority
        if explicit_token:
            return explicit_token

        # 2. Check environment variable
        env_token = os.environ.get(self.TOKEN_ENV_VAR)
        if env_token:
            return env_token

        # 3. Check secrets file
        file_token = self._load_token_from_file()
        if file_token:
            return file_token

        # 4. Prompt user (not persisted)
        user_token = self._prompt_for_token()
        if user_token:
            return user_token

        raise GitHubAuthError(
            "No GitHub token found. Please provide one via:\n"
            "  1. --token flag on CLI\n"
            "  2. GITHUB_TOKEN environment variable\n"
            "  3. secrets/.env file (GITHUB_TOKEN=...)\n"
            "  4. Interactive prompt"
        )

    def validate_token(self, token: str) -> bool:
        """
        Validate GitHub token format.

        Checks if token follows GitHub's Personal Access Token (PAT) format.
        GitHub tokens have prefixes: ghp_ (classic), ghu_ (user), ghs_ (server), gho_ (oauth).

        This is a format-only check; actual validity is verified during API calls.

        Args:
            token: Token string to validate.

        Returns:
            True if token format is valid, False otherwise.
        """
        # GitHub PAT format validation
        # Matches tokens like: ghp_abc123...xyz (36+ chars after prefix, up to 255 total)
        return bool(re.match(self.TOKEN_PREFIX_PATTERN, token))

    def _load_token_from_file(self) -> Optional[str]:
        """
        Load GitHub token from secrets/.env file.

        Expected file format:
            GITHUB_TOKEN=ghp_abc123...xyz

        Args:
            None

        Returns:
            Token string if found in file, None otherwise.
        """
        env_file = Path(self.SECRETS_FILE_PATH)

        if not env_file.exists():
            return None

        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith(self.TOKEN_ENV_VAR + "="):
                        token = line.split("=", 1)[1].strip()
                        if token:
                            return token
        except Exception:
            # Silently fail if file read error; will try other sources
            pass

        return None

    def _prompt_for_token(self) -> Optional[str]:
        """
        Securely prompt user for GitHub token.

        Uses getpass() to hide input from terminal echo.
        Token is NOT persisted to disk.

        Args:
            None

        Returns:
            Token string entered by user, or None if user cancels.
        """
        try:
            token = getpass(
                "GitHub token not found. Enter your GitHub Personal Access Token "
                "(hidden input): "
            )
            if token:
                return token
        except (KeyboardInterrupt, EOFError):
            # User cancelled input
            pass

        return None
