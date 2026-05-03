"""GitHub token resolution with priority chain."""

import os
from typing import Optional

from .exceptions import TokenResolutionError


class TokenResolver:
    """Resolve GitHub token from multiple sources with priority chain.

    Priority (highest to lowest):
    1. CLI argument (--github-token)
    2. Environment variable GITHUB_TOKEN
    3. secrets/.env file with GITHUB_TOKEN=value
    4. Interactive prompt
    """

    @staticmethod
    def resolve(cli_arg: Optional[str] = None, prompt_if_missing: bool = True) -> str:
        """Resolve GitHub token from priority sources.

        Args:
            cli_arg: Token from CLI argument (highest priority)
            prompt_if_missing: If True, prompt user if token not found in other sources

        Returns:
            GitHub token string

        Raises:
            TokenResolutionError: If token cannot be resolved from any source
        """
        # Priority 1: CLI argument
        if cli_arg:
            return cli_arg

        # Priority 2: Environment variable
        env_token = os.environ.get("GITHUB_TOKEN")
        if env_token:
            return env_token

        # Priority 3: secrets/.env file
        env_token = TokenResolver._read_from_env_file()
        if env_token:
            return env_token

        # Priority 4: Interactive prompt
        if prompt_if_missing:
            return TokenResolver._prompt_user()

        # All sources exhausted
        raise TokenResolutionError(
            "Could not resolve GitHub token. Provide via --github-token, "
            "GITHUB_TOKEN environment variable, secrets/.env file, or interactive prompt."
        )

    @staticmethod
    def _read_from_env_file() -> Optional[str]:
        """Read GITHUB_TOKEN from secrets/.env file.

        Returns:
            Token if found, None otherwise
        """
        env_file = "secrets/.env"
        if not os.path.exists(env_file):
            return None

        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        if token:
                            return token
        except (IOError, OSError):
            pass

        return None

    @staticmethod
    def _prompt_user() -> str:
        """Prompt user for GitHub token interactively (do not persist).

        Returns:
            Token entered by user

        Raises:
            TokenResolutionError: If user provides empty input
        """
        token = input("GitHub Token: ").strip()
        if not token:
            raise TokenResolutionError("Empty token provided via prompt.")
        return token
