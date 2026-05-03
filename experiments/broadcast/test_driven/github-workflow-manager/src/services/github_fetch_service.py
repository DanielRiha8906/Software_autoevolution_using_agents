import json
import os
import subprocess
from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class GitHubFetchService:
    """Service for fetching GitHub workflow runs using the gh CLI."""

    def __init__(self, secrets_path: Optional[str] = None):
        """Initialize the GitHubFetchService.

        Args:
            secrets_path: Optional path to a .env file containing the GITHUB_TOKEN.
                         If not provided, defaults to the current working directory's .env.
        """
        self._secrets_path = secrets_path or ".env"
        self._token: Optional[str] = None

    def resolve_token(self) -> str:
        """Resolve the GitHub token from environment, .env file, or user input.

        Resolution order:
        1. GITHUB_TOKEN environment variable
        2. GITHUB_TOKEN from secrets file (.env)
        3. Prompt user for token

        Returns:
            The resolved GitHub token.
        """
        # Try environment variable
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self._token = token
            return token

        # Try secrets file
        token = self._load_token_from_file()
        if token:
            self._token = token
            return token

        # Prompt user
        token = input("Enter your GitHub token: ")
        self._token = token
        return token

    def _load_token_from_file(self) -> Optional[str]:
        """Load GITHUB_TOKEN from the secrets file.

        Returns:
            The token if found, None otherwise.
        """
        if not os.path.exists(self._secrets_path):
            return None

        try:
            with open(self._secrets_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        # Extract the token after the '=' sign
                        return line.split("=", 1)[1]
        except (IOError, OSError):
            pass

        return None

    def fetch(self, owner: str, repo: str) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub using gh CLI.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.

        Returns:
            A list of WorkflowRun objects.

        Raises:
            Exception: If the gh CLI command fails (non-zero exit code).
        """
        token = self._token or self.resolve_token()

        # Build the gh CLI command
        cmd = [
            "gh",
            "api",
            f"repos/{owner}/{repo}/actions/runs",
        ]

        # Run the command with the token
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = token

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            raise Exception(f"GitHub CLI command failed: {result.stderr}")

        # Parse the JSON output
        try:
            response_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GitHub API response: {e}")

        # Extract workflow_runs array
        runs_data = response_data.get("workflow_runs", [])

        # Convert to WorkflowRun objects
        runs = []
        for run_data in runs_data:
            run = self._convert_to_workflow_run(run_data)
            runs.append(run)

        return runs

    def _convert_to_workflow_run(self, data: dict) -> WorkflowRun:
        """Convert GitHub API response data to a WorkflowRun object.

        Args:
            data: The workflow run data from GitHub API.

        Returns:
            A WorkflowRun object.
        """
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get("created_at", "").replace("Z", "+00:00"))
        updated_at_str = data.get("updated_at")
        updated_at = None
        if updated_at_str:
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))

        # Map status
        status_str = data.get("status", "queued")
        status = WorkflowStatus(status_str)

        # Map conclusion
        conclusion = None
        conclusion_str = data.get("conclusion")
        if conclusion_str:
            conclusion = WorkflowConclusion(conclusion_str)

        return WorkflowRun(
            id=str(data.get("id", "")),
            workflow_name=data.get("name", ""),
            branch=data.get("head_branch", ""),
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=data.get("run_number"),
            commit_sha=data.get("head_sha"),
            duration_seconds=0.0,  # Calculate if needed
        )
