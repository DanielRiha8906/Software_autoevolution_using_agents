"""GitHub API adapter for external communication.

This module handles all communication with GitHub APIs via the gh CLI tool.
It translates GitHub API responses into domain models.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from getpass import getpass
from pathlib import Path
from typing import List, Optional

from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus


class GitHubAdapter:
    """Adapter for fetching workflow runs from GitHub via the gh CLI.

    Handles token resolution, API communication, and data conversion to the domain model.
    This adapter is intentionally isolated in the adapters layer to separate
    external API concerns from business logic.
    """

    def __init__(self) -> None:
        """Initialize the GitHub adapter."""
        self._token: Optional[str] = None

    def _resolve_token(self, token: Optional[str] = None) -> str:
        """Resolve GitHub token in priority order.

        Priority:
        1. Provided token parameter
        2. GITHUB_TOKEN environment variable
        3. .env file in current directory
        4. secrets/.env file in project root
        5. Prompt user for token (not persisted)

        Args:
            token: Optional provided token to use first.

        Returns:
            str: The resolved GitHub token.

        Raises:
            ValueError: If no token could be resolved.
        """
        # Check provided token
        if token:
            return token

        # Check GITHUB_TOKEN environment variable
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token

        # Check .env file in current directory
        env_path = Path(".env")
        if env_path.exists():
            token = self._read_env_file(env_path)
            if token:
                return token

        # Check secrets/.env file in project root
        secrets_env_path = Path("secrets/.env")
        if secrets_env_path.exists():
            token = self._read_env_file(secrets_env_path)
            if token:
                return token

        # Prompt user for token
        print("No GitHub token found in environment or .env files.")
        token = getpass("Enter your GitHub Personal Access Token (not persisted): ")
        if not token:
            raise ValueError("No GitHub token provided.")
        return token

    def _read_env_file(self, env_path: Path) -> Optional[str]:
        """Read GITHUB_TOKEN from a .env file.

        Args:
            env_path: Path to the .env file.

        Returns:
            str or None: The token if found, None otherwise.
        """
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        return line.split("=", 1)[1].strip('"').strip("'")
        except Exception:
            pass
        return None

    def validate_token(self, token: str) -> bool:
        """Validate the GitHub token by testing against /user endpoint.

        Args:
            token: The token to validate.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gh", "api", "user"],
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "GITHUB_TOKEN": token},
            )
            return result.returncode == 0
        except Exception:
            return False

    def fetch_workflow_runs(
        self, owner: str, repo: str, workflow_id: Optional[str] = None, token: Optional[str] = None
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.
            workflow_id: Optional workflow ID or filename to filter runs.
            token: Optional GitHub token (uses resolution chain if not provided).

        Returns:
            List[WorkflowRun]: List of converted workflow runs.

        Raises:
            ValueError: If API request fails or data is invalid.
        """
        resolved_token = self._resolve_token(token)

        # Validate token
        if not self.validate_token(resolved_token):
            raise ValueError("Invalid or expired GitHub token.")

        # Fetch runs from GitHub API using gh CLI
        try:
            cmd = [
                "gh",
                "run",
                "list",
                "--repo",
                f"{owner}/{repo}",
                "--json",
                "id,name,headBranch,status,conclusion,createdAt,updatedAt,number,headSha",
                "--limit",
                "100",
            ]

            # Add workflow_id filter if provided
            if workflow_id:
                cmd.extend(["--workflow", workflow_id])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "GITHUB_TOKEN": resolved_token},
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                raise ValueError(f"Failed to fetch runs from GitHub: {error_msg}")

            data = json.loads(result.stdout)
            if not isinstance(data, list):
                raise ValueError("GitHub API returned unexpected data format.")

            runs = []
            for item in data:
                try:
                    run = self._convert_github_run(item)
                    runs.append(run)
                except Exception as e:
                    print(f"Warning: skipping invalid run {item.get('id')}: {e}", file=sys.stderr)
                    continue

            return runs

        except subprocess.TimeoutExpired:
            raise ValueError("GitHub API request timed out.")
        except json.JSONDecodeError:
            raise ValueError("Failed to parse GitHub API response.")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching from GitHub: {e}")

    def _convert_github_run(self, github_run: dict) -> WorkflowRun:
        """Convert a GitHub API run object to a WorkflowRun domain model.

        Args:
            github_run: Dictionary from GitHub API response.

        Returns:
            WorkflowRun: Converted domain model.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Validate required fields first
        run_id = str(github_run.get("id")) if github_run.get("id") else None
        if not run_id:
            raise ValueError("Missing 'id' field.")

        created_at_str = github_run.get("createdAt")
        if not created_at_str:
            raise ValueError("Missing 'createdAt' field.")

        workflow_name = github_run.get("name", "Unknown")
        branch = github_run.get("headBranch", "unknown")
        status_str = github_run.get("status", "").lower()
        conclusion_str = github_run.get("conclusion", "")
        updated_at_str = github_run.get("updatedAt")
        run_number = github_run.get("number")
        commit_sha = github_run.get("headSha")

        # Convert status
        status = self._map_github_status(status_str)

        # Convert conclusion
        conclusion = None
        if conclusion_str:
            conclusion = self._map_github_conclusion(conclusion_str)

        # Parse timestamps
        created_at = self._parse_timestamp(created_at_str)
        updated_at = None
        if updated_at_str:
            try:
                updated_at = self._parse_timestamp(updated_at_str)
            except Exception:
                pass

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
            duration_seconds=0.0,
        )

    def _map_github_status(self, github_status: str) -> WorkflowStatus:
        """Map GitHub status to WorkflowStatus enum.

        Args:
            github_status: Status string from GitHub API.

        Returns:
            WorkflowStatus: Mapped status.

        Raises:
            ValueError: If status is not recognized.
        """
        # GitHub statuses: queued, in_progress, completed, waiting, requested, pending
        mapping = {
            "queued": WorkflowStatus.QUEUED,
            "in_progress": WorkflowStatus.IN_PROGRESS,
            "completed": WorkflowStatus.COMPLETED,
            "waiting": WorkflowStatus.WAITING,
            "requested": WorkflowStatus.REQUESTED,
            "pending": WorkflowStatus.PENDING,
        }
        status = mapping.get(github_status.lower())
        if not status:
            raise ValueError(f"Unknown GitHub status: {github_status}")
        return status

    def _map_github_conclusion(self, github_conclusion: str) -> WorkflowConclusion:
        """Map GitHub conclusion to WorkflowConclusion enum.

        Args:
            github_conclusion: Conclusion string from GitHub API.

        Returns:
            WorkflowConclusion: Mapped conclusion.

        Raises:
            ValueError: If conclusion is not recognized.
        """
        # GitHub conclusions: success, failure, cancelled, skipped, timed_out,
        # action_required, neutral, stale
        mapping = {
            "success": WorkflowConclusion.SUCCESS,
            "failure": WorkflowConclusion.FAILURE,
            "cancelled": WorkflowConclusion.CANCELLED,
            "skipped": WorkflowConclusion.SKIPPED,
            "timed_out": WorkflowConclusion.TIMED_OUT,
            "action_required": WorkflowConclusion.ACTION_REQUIRED,
            "neutral": WorkflowConclusion.NEUTRAL,
            "stale": WorkflowConclusion.STALE,
        }
        conclusion = mapping.get(github_conclusion.lower())
        if not conclusion:
            raise ValueError(f"Unknown GitHub conclusion: {github_conclusion}")
        return conclusion

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO 8601 timestamp string to datetime.

        Args:
            timestamp_str: Timestamp string in ISO format.

        Returns:
            datetime: Parsed datetime object.

        Raises:
            ValueError: If timestamp format is invalid.
        """
        try:
            # GitHub API returns ISO 8601 format, may include 'Z' suffix
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}") from e
