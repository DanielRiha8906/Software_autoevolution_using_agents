"""GitHub CLI (gh) adapter for fetching workflow data."""

import json
import logging
import subprocess
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitHubCliAdapter:
    """Adapter for GitHub CLI (gh) commands."""

    def __init__(self) -> None:
        """Initialize the CLI adapter."""
        pass

    def get_runs(
        self,
        owner: str,
        repo: str,
        limit: int = 30,
    ) -> List[Dict]:
        """
        Fetch workflow runs using gh CLI.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            limit: Maximum number of runs to fetch (default 30)

        Returns:
            List of raw run data dictionaries

        Raises:
            RuntimeError: If CLI command fails
        """
        args = [
            "gh",
            "run",
            "list",
            "-R",
            f"{owner}/{repo}",
            "-L",
            str(limit),
            "--json",
            "id,name,status,conclusion,headBranch,runNumber,headSha,createdAt,updatedAt",
        ]

        output = self._execute_command(args)

        try:
            runs_data = json.loads(output)
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON output from gh CLI: {e}")

        return runs_data

    def get_run_attempts(
        self,
        owner: str,
        repo: str,
        run_id: str,
    ) -> List[Dict]:
        """
        Fetch workflow attempts for a specific run using gh CLI.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            run_id: GitHub workflow run ID

        Returns:
            List of raw attempt data dictionaries

        Raises:
            RuntimeError: If CLI command fails
        """
        args = [
            "gh",
            "run",
            "view",
            run_id,
            "-R",
            f"{owner}/{repo}",
            "--json",
            "attemptNumber,status,conclusion,startedAt,completedAt",
        ]

        output = self._execute_command(args)

        try:
            attempt_data = json.loads(output)
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON output from gh CLI: {e}")

        # Parse the structure returned by gh
        if "attempts" not in attempt_data:
            raise RuntimeError("Invalid gh CLI output: missing 'attempts' key")

        return attempt_data["attempts"]

    def _execute_command(self, args: List[str]) -> str:
        """
        Execute a gh CLI command and return output.

        Args:
            args: Command arguments (first element should be "gh")

        Returns:
            Standard output as string

        Raises:
            RuntimeError: If command fails
        """
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                timeout=30,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"gh CLI failed: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("gh CLI command timed out")
        except FileNotFoundError:
            raise RuntimeError("gh CLI not found in PATH")
