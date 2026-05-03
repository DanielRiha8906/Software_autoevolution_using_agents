import os
import json
import subprocess
from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class GitHubFetchService:
    """Fetches workflow runs from GitHub using GitHub CLI."""

    def __init__(self, secrets_path: Optional[str] = None):
        """Initialize the service with optional path to .env file.

        Args:
            secrets_path: Optional path to .env file containing GITHUB_TOKEN
        """
        self._secrets_path = secrets_path

    def resolve_token(self) -> str:
        """Resolve GitHub token from environment, file, or user input.

        Returns:
            GitHub token string.

        Raises:
            Exception: If token cannot be resolved.
        """
        # Check environment variable first
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return token

        # Check secrets file
        if self._secrets_path:
            token = self._read_token_from_file(self._secrets_path)
            if token:
                return token

        # Prompt user
        token = input("Enter your GitHub token: ")
        return token

    def _read_token_from_file(self, file_path: str) -> Optional[str]:
        """Read GITHUB_TOKEN from .env file.

        Args:
            file_path: Path to .env file.

        Returns:
            Token string if found, None otherwise.
        """
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        return line.split("=", 1)[1]
        except Exception:
            pass

        return None

    def fetch(self, owner: str, repo: str) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub CLI.

        Args:
            owner: Repository owner (username or org).
            repo: Repository name.

        Returns:
            List of WorkflowRun objects.

        Raises:
            Exception: If gh CLI call fails.
        """
        token = self.resolve_token()

        # Prepare environment with GitHub token
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = token

        # Call gh CLI
        cmd = [
            "gh",
            "run",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "id,name,headBranch,status,conclusion,createdAt,updatedAt,runNumber,headSha",
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"GitHub CLI error: {result.stderr}")

        # Parse JSON output
        data = json.loads(result.stdout)
        runs = []

        # Handle both direct list and wrapped format
        if isinstance(data, dict) and "workflow_runs" in data:
            run_list = data["workflow_runs"]
        else:
            run_list = data

        for run_data in run_list:
            workflow_run = self._convert_to_workflow_run(run_data)
            runs.append(workflow_run)

        return runs

    def _convert_to_workflow_run(self, data: dict) -> WorkflowRun:
        """Convert GitHub CLI output to WorkflowRun object.

        Args:
            data: Dictionary from gh CLI JSON output.

        Returns:
            WorkflowRun object.
        """
        # Convert id to string
        run_id = str(data["id"])

        # Map field names
        workflow_name = data["name"]
        branch = data["headBranch"]
        status = WorkflowStatus(data["status"])
        conclusion = (
            WorkflowConclusion(data["conclusion"])
            if data.get("conclusion")
            else None
        )

        # Parse timestamps
        created_at = datetime.fromisoformat(
            data["createdAt"].replace("Z", "+00:00")
        )
        updated_at = None
        if data.get("updatedAt"):
            updated_at = datetime.fromisoformat(
                data["updatedAt"].replace("Z", "+00:00")
            )

        run_number = data.get("runNumber")
        commit_sha = data.get("headSha")

        return WorkflowRun(
            id=run_id,
            workflow_name=workflow_name,
            branch=branch,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=run_number,
            commit_sha=commit_sha,
        )
