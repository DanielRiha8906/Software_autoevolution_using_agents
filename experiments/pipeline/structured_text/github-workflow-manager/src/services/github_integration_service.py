import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus


logger = logging.getLogger(__name__)


class GitHubIntegrationService:
    """Service for fetching workflow runs and attempts from GitHub."""

    API_BASE_URL = "https://api.github.com"
    TOKEN_PREFIX = "ghp_"

    def __init__(self, fetch_mode: str = "api"):
        """
        Initialize the GitHub integration service.

        Args:
            fetch_mode: "api" for requests-based REST API, "cli" for gh CLI
        """
        self.fetch_mode = fetch_mode
        self._token: Optional[str] = None

    def _resolve_token(self) -> str:
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

    def _validate_token(self, token: str) -> bool:
        """
        Validate the GitHub token by testing connectivity.

        Args:
            token: The GitHub token to validate

        Returns:
            True if token is valid, False otherwise
        """
        if self.fetch_mode == "cli":
            try:
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

        # API mode: test with a simple request
        try:
            headers = {"Authorization": f"token {token}"}
            response = requests.get(
                f"{self.API_BASE_URL}/user",
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
        except requests.RequestException as e:
            logger.warning(f"Failed to validate GitHub token: {e}")
            return False

    def fetch_runs(
        self,
        owner: str,
        repo: str,
        workflow_name: Optional[str] = None,
        limit: int = 30,
        token: Optional[str] = None,
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs from GitHub.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            workflow_name: Optional filter for specific workflow
            limit: Maximum number of runs to fetch (default 30)
            token: Optional explicit token (uses resolved token if omitted)

        Returns:
            List of WorkflowRun instances

        Raises:
            RuntimeError: If token validation fails or API call fails
        """
        token = token or self._resolve_token()

        if not self._validate_token(token):
            raise RuntimeError("GitHub token validation failed")

        if self.fetch_mode == "cli":
            return self._fetch_runs_cli(owner, repo, workflow_name, limit, token)
        else:
            return self._fetch_runs_api(owner, repo, workflow_name, limit, token)

    def _fetch_runs_api(
        self,
        owner: str,
        repo: str,
        workflow_name: Optional[str] = None,
        limit: int = 30,
        token: str = "",
    ) -> List[WorkflowRun]:
        """Fetch runs using REST API."""
        url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/actions/runs"
        headers = {"Authorization": f"token {token}"}
        params = {"per_page": min(limit, 100)}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch runs from GitHub: {e}")

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON response from GitHub: {e}")

        runs = []
        for api_run in data.get("workflow_runs", []):
            if len(runs) >= limit:
                break

            # Filter by workflow name if specified
            if workflow_name and api_run.get("name") != workflow_name:
                continue

            try:
                run = self._convert_api_run(api_run, repo)
                runs.append(run)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to convert API run: {e}")
                continue

        logger.info(f"Fetched {len(runs)} runs from {owner}/{repo}")
        return runs

    def _fetch_runs_cli(
        self,
        owner: str,
        repo: str,
        workflow_name: Optional[str] = None,
        limit: int = 30,
        token: str = "",
    ) -> List[WorkflowRun]:
        """Fetch runs using gh CLI."""
        try:
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
            output = self._call_gh_cli(args)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to fetch runs using gh CLI: {e}")

        try:
            import json
            runs_data = json.loads(output)
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON output from gh CLI: {e}")

        runs = []
        for api_run in runs_data:
            if workflow_name and api_run.get("name") != workflow_name:
                continue

            try:
                run = self._convert_api_run(api_run, repo)
                runs.append(run)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to convert CLI run: {e}")
                continue

        logger.info(f"Fetched {len(runs)} runs from {owner}/{repo} via gh CLI")
        return runs

    def fetch_run_attempts(
        self,
        owner: str,
        repo: str,
        run_id: str,
        token: Optional[str] = None,
    ) -> List[WorkflowRunAttempt]:
        """
        Fetch workflow attempts for a specific run.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            run_id: GitHub workflow run ID
            token: Optional explicit token (uses resolved token if omitted)

        Returns:
            List of WorkflowRunAttempt instances

        Raises:
            RuntimeError: If token validation fails or API call fails
        """
        token = token or self._resolve_token()

        if not self._validate_token(token):
            raise RuntimeError("GitHub token validation failed")

        if self.fetch_mode == "cli":
            return self._fetch_attempts_cli(owner, repo, run_id, token)
        else:
            return self._fetch_attempts_api(owner, repo, run_id, token)

    def _fetch_attempts_api(
        self,
        owner: str,
        repo: str,
        run_id: str,
        token: str = "",
    ) -> List[WorkflowRunAttempt]:
        """Fetch attempts using REST API."""
        url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/attempts"
        headers = {"Authorization": f"token {token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch attempts from GitHub: {e}")

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON response from GitHub: {e}")

        attempts = []
        for api_attempt in data.get("workflow_runs", []):
            try:
                attempt = self._convert_api_attempt(api_attempt, run_id, repo)
                attempts.append(attempt)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to convert API attempt: {e}")
                continue

        logger.info(f"Fetched {len(attempts)} attempts for run {run_id}")
        return attempts

    def _fetch_attempts_cli(
        self,
        owner: str,
        repo: str,
        run_id: str,
        token: str = "",
    ) -> List[WorkflowRunAttempt]:
        """Fetch attempts using gh CLI."""
        try:
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
            output = self._call_gh_cli(args)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to fetch attempts using gh CLI: {e}")

        try:
            import json
            attempt_data = json.loads(output)
            # Parse the structure returned by gh
            if "attempts" not in attempt_data:
                raise RuntimeError("Invalid gh CLI output: missing 'attempts' key")
            attempts_list = attempt_data["attempts"]
        except (ValueError, KeyError) as e:
            raise RuntimeError(f"Invalid JSON output from gh CLI: {e}")

        attempts = []
        for api_attempt in attempts_list:
            try:
                attempt = self._convert_api_attempt(api_attempt, run_id, repo)
                attempts.append(attempt)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to convert CLI attempt: {e}")
                continue

        logger.info(f"Fetched {len(attempts)} attempts for run {run_id} via gh CLI")
        return attempts

    def _convert_api_run(self, api_data: Dict, repo: str) -> WorkflowRun:
        """
        Convert GitHub API run data to WorkflowRun domain model.

        Args:
            api_data: Raw API response dict
            repo: Repository name (for reference)

        Returns:
            WorkflowRun instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Parse timestamps
        created_at_str = api_data.get("createdAt") or api_data.get("created_at")
        updated_at_str = api_data.get("updatedAt") or api_data.get("updated_at")

        if not created_at_str:
            raise ValueError("Missing createdAt field in API response")

        # Handle timezone-aware strings from GitHub API (with Z suffix)
        created_at = self._parse_github_timestamp(created_at_str)
        updated_at = self._parse_github_timestamp(updated_at_str) if updated_at_str else None

        # Calculate duration
        duration_seconds = 0.0
        if updated_at and created_at:
            duration_seconds = (updated_at - created_at).total_seconds()

        # Parse status and conclusion
        status_val = api_data.get("status")
        if not status_val:
            raise ValueError("Missing status field in API response")

        try:
            status = WorkflowStatus(status_val)
        except ValueError:
            raise ValueError(f"Invalid status value: {status_val}")

        conclusion_val = api_data.get("conclusion")
        conclusion = None
        if conclusion_val:
            try:
                conclusion = WorkflowConclusion(conclusion_val)
            except ValueError:
                logger.warning(f"Invalid conclusion value: {conclusion_val}")

        run = WorkflowRun(
            id=str(api_data.get("id", "")),
            workflow_name=api_data.get("name", ""),
            branch=api_data.get("headBranch") or api_data.get("head_branch", ""),
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=api_data.get("runNumber") or api_data.get("run_number"),
            commit_sha=api_data.get("headSha") or api_data.get("head_sha"),
            duration_seconds=duration_seconds,
        )
        return run

    def _convert_api_attempt(self, api_data: Dict, run_id: str, repo: str) -> WorkflowRunAttempt:
        """
        Convert GitHub API attempt data to WorkflowRunAttempt domain model.

        Args:
            api_data: Raw API response dict
            run_id: The run ID this attempt belongs to
            repo: Repository name (for reference)

        Returns:
            WorkflowRunAttempt instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Parse timestamps
        started_at_str = api_data.get("startedAt") or api_data.get("created_at") or api_data.get("started_at")
        completed_at_str = api_data.get("completedAt") or api_data.get("completed_at")

        if not started_at_str:
            raise ValueError("Missing startedAt field in API response")

        started_at = self._parse_github_timestamp(started_at_str)
        completed_at = self._parse_github_timestamp(completed_at_str) if completed_at_str else None

        # Calculate duration
        duration_seconds = 0.0
        if completed_at and started_at:
            duration_seconds = (completed_at - started_at).total_seconds()

        # Parse status and conclusion
        status_val = api_data.get("status")
        if not status_val:
            raise ValueError("Missing status field in API response")

        try:
            status = WorkflowStatus(status_val)
        except ValueError:
            raise ValueError(f"Invalid status value: {status_val}")

        conclusion_val = api_data.get("conclusion")
        conclusion = None
        if conclusion_val:
            try:
                conclusion = WorkflowConclusion(conclusion_val)
            except ValueError:
                logger.warning(f"Invalid conclusion value: {conclusion_val}")

        attempt = WorkflowRunAttempt(
            id=str(api_data.get("id", "")),
            run_id=run_id,
            attempt_number=api_data.get("attemptNumber") or api_data.get("attempt_number", 1),
            status=status,
            conclusion=conclusion,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            logs_url=api_data.get("logsUrl") or api_data.get("logs_url"),
        )
        return attempt

    def _call_gh_cli(self, args: List[str]) -> str:
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

    def _call_api(
        self,
        url: str,
        method: str = "GET",
        data: Optional[dict] = None,
    ) -> dict:
        """
        Execute an API request.

        Args:
            url: Full URL to request
            method: HTTP method ("GET", "POST", etc.)
            data: Optional request body

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If request fails
        """
        token = self._token or self._resolve_token()
        headers = {"Authorization": f"token {token}"}

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                    timeout=10,
                )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

    @staticmethod
    def _parse_github_timestamp(timestamp_str: str) -> datetime:
        """
        Parse a GitHub API timestamp string to datetime.

        GitHub API returns ISO 8601 strings, often with Z suffix for UTC.

        Args:
            timestamp_str: Timestamp string from GitHub API

        Returns:
            datetime object in UTC timezone

        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Remove Z suffix if present (GitHub uses it for UTC)
        timestamp_str = timestamp_str.rstrip("Z")

        try:
            # Try parsing with fromisoformat
            dt = datetime.fromisoformat(timestamp_str)
            # Ensure it's UTC aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError as e:
            raise ValueError(f"Failed to parse timestamp '{timestamp_str}': {e}")
