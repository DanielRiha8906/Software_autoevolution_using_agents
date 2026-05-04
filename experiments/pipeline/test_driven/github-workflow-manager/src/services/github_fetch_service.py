import os
import json
import subprocess
from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class GitHubFetchService:
    """
    Service for fetching workflow runs from GitHub using the GitHub CLI.

    Handles GitHub token resolution, subprocess invocation of the gh command,
    and conversion of GitHub API responses to WorkflowRun domain objects.
    """

    def __init__(self, secrets_path: Optional[str] = None) -> None:
        """
        Initialize the GitHubFetchService.

        Args:
            secrets_path: Optional path to a .env file containing GITHUB_TOKEN.
                         Defaults to None.
        """
        self._secrets_path = secrets_path
        self._token: Optional[str] = None

    def resolve_token(self) -> str:
        """
        Resolve GitHub token using a 3-step priority algorithm.

        1. Environment variable: os.environ.get("GITHUB_TOKEN")
        2. Secrets file: Parse secrets_path for GITHUB_TOKEN= line (if provided)
        3. User input: Call input("GitHub token: ")

        Returns:
            The resolved GitHub token as a string.

        Raises:
            ValueError: If user input is empty.
        """
        # Step 1: Check environment variable
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            self._token = token
            return token

        # Step 2: Check secrets file (if provided)
        if self._secrets_path:
            env_token = self._parse_env_file(self._secrets_path)
            if env_token:
                self._token = env_token
                return env_token

        # Step 3: Request from user input
        token = input("GitHub token: ")
        if not token:
            raise ValueError("GitHub token cannot be empty")
        self._token = token
        return token

    def fetch(self, owner: str, repo: str) -> List[WorkflowRun]:
        """
        Fetch workflow runs for a GitHub repository.

        Uses the GitHub CLI (gh command) to retrieve runs and converts them
        to WorkflowRun domain objects.

        Args:
            owner: GitHub repository owner/organization.
            repo: GitHub repository name.

        Returns:
            List of WorkflowRun objects, in insertion order.

        Raises:
            Exception: If the gh CLI command returns non-zero exit code.
            json.JSONDecodeError: If the gh response is malformed JSON.
            KeyError: If a required field is missing from the GitHub response.
        """
        # Ensure token is resolved
        if not self._token:
            self.resolve_token()

        # Build the gh command
        repo_path = f"{owner}/{repo}"
        cmd = [
            "gh",
            "run",
            "list",
            "--repo",
            repo_path,
            "--json",
            "id,name,headBranch,status,conclusion,createdAt,updatedAt,number,headSha",
            "--limit",
            "100",
        ]

        # Execute the gh command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise Exception(
                f"gh command failed with exit code {result.returncode}: {result.stderr}"
            )

        # Parse the JSON response
        response_data = json.loads(result.stdout)

        # Extract workflow runs array from response
        gh_runs = response_data.get("workflow_runs", response_data)

        # Convert to WorkflowRun objects
        workflow_runs = []
        for gh_data in gh_runs:
            workflow_run = self._convert_to_workflow_run(gh_data)
            workflow_runs.append(workflow_run)

        return workflow_runs

    def _parse_env_file(self, path: str) -> Optional[str]:
        """
        Parse a .env file and extract the GITHUB_TOKEN value.

        Args:
            path: Path to the .env file.

        Returns:
            The GITHUB_TOKEN value if found, None otherwise.
            Returns None if file does not exist (no exception raised).
        """
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        # Extract value after the equals sign
                        token = line.split("=", 1)[1]
                        return token if token else None
            return None
        except FileNotFoundError:
            return None

    def _convert_to_workflow_run(self, gh_data: dict) -> WorkflowRun:
        """
        Convert GitHub API JSON response to a WorkflowRun domain object.

        Maps GitHub JSON field names to WorkflowRun attributes:
        - id → id
        - name → workflow_name
        - headBranch or head_branch → branch
        - status → status (convert to WorkflowStatus enum)
        - conclusion → conclusion (convert to WorkflowConclusion enum or None)
        - createdAt or created_at → created_at (ISO 8601 datetime, timezone-aware)
        - updatedAt or updated_at → updated_at (ISO 8601 datetime or None)
        - number or run_number → run_number
        - headSha or head_sha → commit_sha

        duration_seconds is computed from (updated_at - created_at).total_seconds()
        or defaults to 0.0 if updated_at is None.

        Args:
            gh_data: Dictionary from GitHub API response.

        Returns:
            WorkflowRun domain object.

        Raises:
            KeyError: If a required field is missing.
            ValueError: If enum conversion fails.
        """
        # Parse timestamps (handle both camelCase and snake_case)
        created_at_str = gh_data.get("createdAt") or gh_data.get("created_at")
        updated_at_str = gh_data.get("updatedAt") or gh_data.get("updated_at")

        # Handle Z suffix for UTC timezone (Python 3.11+ handles this, older versions need replacement)
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str.replace("Z", "+00:00")
        created_at = datetime.fromisoformat(created_at_str)

        updated_at = None
        if updated_at_str:
            if updated_at_str.endswith("Z"):
                updated_at_str = updated_at_str.replace("Z", "+00:00")
            updated_at = datetime.fromisoformat(updated_at_str)

        # Compute duration_seconds
        duration_seconds = 0.0
        if updated_at:
            duration_delta = updated_at - created_at
            duration_seconds = duration_delta.total_seconds()

        # Convert status enum (GitHub returns lowercase, matching enum values)
        status_value = gh_data["status"].lower()
        # Map GitHub status values to WorkflowStatus enum
        status_mapping = {
            "queued": WorkflowStatus.QUEUED,
            "in_progress": WorkflowStatus.IN_PROGRESS,
            "completed": WorkflowStatus.COMPLETED,
            "waiting": WorkflowStatus.WAITING,
            "requested": WorkflowStatus.REQUESTED,
            "pending": WorkflowStatus.PENDING,
        }
        status = status_mapping.get(status_value)
        if not status:
            # Fallback to direct enum creation if mapping doesn't match
            status = WorkflowStatus(status_value)

        # Convert conclusion enum (GitHub returns lowercase, or None)
        conclusion = None
        conclusion_value = gh_data.get("conclusion")
        if conclusion_value:
            conclusion_value = conclusion_value.lower()
            # Map GitHub conclusion values to WorkflowConclusion enum
            conclusion_mapping = {
                "success": WorkflowConclusion.SUCCESS,
                "failure": WorkflowConclusion.FAILURE,
                "cancelled": WorkflowConclusion.CANCELLED,
                "skipped": WorkflowConclusion.SKIPPED,
                "timed_out": WorkflowConclusion.TIMED_OUT,
                "action_required": WorkflowConclusion.ACTION_REQUIRED,
                "neutral": WorkflowConclusion.NEUTRAL,
                "stale": WorkflowConclusion.STALE,
            }
            conclusion = conclusion_mapping.get(conclusion_value)
            if not conclusion and conclusion_value:
                # Fallback to direct enum creation if mapping doesn't match
                conclusion = WorkflowConclusion(conclusion_value)

        return WorkflowRun(
            id=str(gh_data["id"]),
            workflow_name=gh_data["name"],
            branch=gh_data.get("headBranch") or gh_data.get("head_branch"),
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=gh_data.get("number") or gh_data.get("run_number"),
            commit_sha=gh_data.get("headSha") or gh_data.get("head_sha"),
            duration_seconds=duration_seconds,
        )
