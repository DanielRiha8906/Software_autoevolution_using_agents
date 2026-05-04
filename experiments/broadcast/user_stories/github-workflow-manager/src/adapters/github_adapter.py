import os
import getpass
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

try:
    import requests
except ImportError:
    requests = None

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class GitHubFetchService:
    """Service to fetch workflow runs from GitHub REST API and convert to domain model.

    Supports both requests library and gh CLI for API calls.
    Prefers gh CLI if available, falls back to requests.
    """

    def __init__(self):
        """Initialize the GitHub fetch service."""
        self._token: Optional[str] = None
        self._repo_owner: Optional[str] = None
        self._repo_name: Optional[str] = None
        self._use_gh_cli: bool = False

    def _resolve_token(self) -> str:
        """Resolve PAT in priority order: env var, secrets/.env file, getpass.

        Returns:
            GitHub personal access token.

        Raises:
            ValueError: If no token can be resolved.
        """
        # 1. Check GITHUB_TOKEN env var
        if "GITHUB_TOKEN" in os.environ:
            token = os.environ["GITHUB_TOKEN"]
            if token:
                return token

        # 2. Check secrets/.env file
        env_path = Path("secrets/.env")
        if env_path.exists():
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GITHUB_TOKEN="):
                            token = line.split("=", 1)[1].strip('"\'')
                            if token:
                                return token
            except Exception:
                pass

        # 3. Prompt user securely (getpass)
        token = getpass.getpass("Enter GitHub personal access token: ")
        if token:
            return token

        raise ValueError("No GitHub token provided or found.")

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is available and authenticated.

        Returns:
            True if gh CLI is available, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _validate_token(self, token: str) -> bool:
        """Validate token by making a test API call.

        Args:
            token: GitHub personal access token.

        Returns:
            True if token is valid, False otherwise.
        """
        # Try gh CLI first (if available)
        if self._use_gh_cli:
            try:
                env = os.environ.copy()
                env["GH_TOKEN"] = token
                result = subprocess.run(
                    ["gh", "api", "user"],
                    capture_output=True,
                    timeout=10,
                    env=env,
                )
                return result.returncode == 0
            except Exception:
                return False

        # Fall back to requests
        if requests is None:
            raise RuntimeError("Neither requests library nor gh CLI is available for GitHub API calls")

        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _map_github_status(self, github_status: str) -> WorkflowStatus:
        """Map GitHub API status to WorkflowStatus enum.

        Args:
            github_status: Status string from GitHub API.

        Returns:
            Corresponding WorkflowStatus enum value.
        """
        status_map = {
            "queued": WorkflowStatus.QUEUED,
            "in_progress": WorkflowStatus.IN_PROGRESS,
            "completed": WorkflowStatus.COMPLETED,
            "waiting": WorkflowStatus.WAITING,
            "requested": WorkflowStatus.REQUESTED,
            "pending": WorkflowStatus.PENDING,
        }
        return status_map.get(github_status, WorkflowStatus.COMPLETED)

    def _map_github_conclusion(self, github_conclusion: Optional[str]) -> Optional[WorkflowConclusion]:
        """Map GitHub API conclusion to WorkflowConclusion enum.

        Args:
            github_conclusion: Conclusion string from GitHub API or None.

        Returns:
            Corresponding WorkflowConclusion enum value or None.
        """
        if not github_conclusion:
            return None

        conclusion_map = {
            "success": WorkflowConclusion.SUCCESS,
            "failure": WorkflowConclusion.FAILURE,
            "cancelled": WorkflowConclusion.CANCELLED,
            "skipped": WorkflowConclusion.SKIPPED,
            "timed_out": WorkflowConclusion.TIMED_OUT,
            "action_required": WorkflowConclusion.ACTION_REQUIRED,
            "neutral": WorkflowConclusion.NEUTRAL,
            "stale": WorkflowConclusion.STALE,
        }
        return conclusion_map.get(github_conclusion)

    def _parse_iso_datetime(self, dt_str: str) -> datetime:
        """Parse ISO 8601 datetime string from GitHub API.

        Args:
            dt_str: Datetime string in ISO format.

        Returns:
            Parsed datetime object in UTC.
        """
        # GitHub returns datetimes in format like "2024-01-15T10:30:45Z"
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)

    def _convert_github_run_to_workflow_run(self, github_run: dict, workflow_name: str) -> WorkflowRun:
        """Convert GitHub API workflow run to domain model.

        Args:
            github_run: Dictionary from GitHub API workflow runs endpoint.
            workflow_name: Workflow name to include in the model.

        Returns:
            WorkflowRun domain model instance.
        """
        return WorkflowRun(
            id=str(github_run["id"]),
            workflow_name=workflow_name,
            branch=github_run.get("head_branch", "unknown"),
            status=self._map_github_status(github_run.get("status", "completed")),
            conclusion=self._map_github_conclusion(github_run.get("conclusion")),
            created_at=self._parse_iso_datetime(github_run["created_at"]),
            updated_at=self._parse_iso_datetime(github_run["updated_at"]) if github_run.get("updated_at") else None,
            run_number=github_run.get("run_number"),
            commit_sha=github_run.get("head_sha"),
        )

    def _fetch_with_gh_cli(
        self,
        owner: str,
        repo: str,
        workflow: Optional[str] = None,
        token: Optional[str] = None,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs using gh CLI.

        Args:
            owner: Repository owner.
            repo: Repository name.
            workflow: Optional workflow ID or filename.
            token: Optional GitHub PAT.

        Returns:
            List of WorkflowRun instances.

        Raises:
            RuntimeError: If gh CLI call fails.
        """
        runs = []
        env = os.environ.copy()
        if token:
            env["GH_TOKEN"] = token

        page = 1
        per_page = 100

        try:
            while True:
                # Build gh command
                if workflow:
                    cmd = [
                        "gh",
                        "api",
                        f"repos/{owner}/{repo}/actions/workflows/{workflow}/runs",
                        f"--paginate",
                        "--per-page",
                        str(per_page),
                    ]
                else:
                    cmd = [
                        "gh",
                        "api",
                        f"repos/{owner}/{repo}/actions/runs",
                        f"--paginate",
                        "--per-page",
                        str(per_page),
                    ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                )

                if result.returncode != 0:
                    if "Unauthorized" in result.stderr or "401" in result.stderr:
                        raise ValueError("Invalid GitHub token (401 Unauthorized). Please check your credentials.")
                    elif "rate limit" in result.stderr.lower() or "403" in result.stderr:
                        raise ValueError("GitHub API rate limit exceeded or access forbidden (403).")
                    elif "not found" in result.stderr.lower() or "404" in result.stderr:
                        raise ValueError(f"Repository not found: {owner}/{repo}")
                    else:
                        raise RuntimeError(f"gh CLI error: {result.stderr}")

                data = json.loads(result.stdout)
                workflow_runs = data.get("workflow_runs", [])

                if not workflow_runs:
                    break

                for github_run in workflow_runs:
                    workflow_name = github_run.get("name", "Unknown Workflow")
                    run = self._convert_github_run_to_workflow_run(github_run, workflow_name)
                    runs.append(run)

                if len(workflow_runs) < per_page:
                    break

                page += 1

        except subprocess.TimeoutExpired:
            raise RuntimeError("gh CLI call timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse gh CLI JSON output: {e}")

        return runs

    def _fetch_with_requests(
        self,
        owner: str,
        repo: str,
        workflow: Optional[str] = None,
        token: Optional[str] = None,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs using requests library.

        Args:
            owner: Repository owner.
            repo: Repository name.
            workflow: Optional workflow ID or filename.
            token: Optional GitHub PAT.

        Returns:
            List of WorkflowRun instances.

        Raises:
            RuntimeError: If requests library is not available or request fails.
        """
        if requests is None:
            raise RuntimeError("requests library is not installed. Please install it or use gh CLI.")

        runs = []
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Build URL based on whether workflow is specified
        if workflow:
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs"
        else:
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

        page = 1
        per_page = 100

        try:
            while True:
                params = {"page": page, "per_page": per_page}
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 401:
                    raise ValueError("Invalid GitHub token (401 Unauthorized). Please check your credentials.")
                elif response.status_code == 403:
                    raise ValueError("GitHub API rate limit exceeded or access forbidden (403).")
                elif response.status_code == 404:
                    raise ValueError(f"Repository not found: {owner}/{repo}")
                elif response.status_code != 200:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

                data = response.json()
                workflow_runs = data.get("workflow_runs", [])

                if not workflow_runs:
                    break

                for github_run in workflow_runs:
                    workflow_name = github_run.get("name", "Unknown Workflow")
                    run = self._convert_github_run_to_workflow_run(github_run, workflow_name)
                    runs.append(run)

                if len(workflow_runs) < per_page:
                    break

                page += 1

        except Exception as e:
            # Handle requests exceptions without importing RequestException
            if type(e).__name__ == "RequestException" or "requests" in str(type(e).__module__):
                raise RuntimeError(f"Network error fetching workflow runs: {e}")
            raise

        return runs

    def fetch_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow: Optional[str] = None,
        token: Optional[str] = None,
        validate: bool = True,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub API.

        Uses gh CLI if available, otherwise falls back to requests library.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.
            workflow: Optional workflow ID or filename to filter by.
            token: Optional GitHub PAT. If not provided, will be resolved.
            validate: If True, validate token before fetching.

        Returns:
            List of WorkflowRun instances fetched from GitHub.

        Raises:
            ValueError: If token cannot be resolved or is invalid.
            RuntimeError: If no API client is available.
        """
        # Resolve token if not provided
        if token is None:
            token = self._resolve_token()

        # Validate token
        if validate and not self._validate_token(token):
            raise ValueError("Invalid GitHub token. Please check your credentials.")

        self._token = token
        self._repo_owner = owner
        self._repo_name = repo

        # Try gh CLI first, fall back to requests
        if self._check_gh_cli():
            self._use_gh_cli = True
            return self._fetch_with_gh_cli(owner, repo, workflow, token)
        else:
            self._use_gh_cli = False
            return self._fetch_with_requests(owner, repo, workflow, token)

    def fetch_incremental(
        self,
        owner: str,
        repo: str,
        latest_run_timestamp: Optional[datetime] = None,
        workflow: Optional[str] = None,
        token: Optional[str] = None,
    ) -> List[WorkflowRun]:
        """Fetch only workflow runs newer than the latest stored run.

        Args:
            owner: Repository owner.
            repo: Repository name.
            latest_run_timestamp: Timestamp of the latest stored run. If provided,
                                 only fetch runs created after this timestamp.
            workflow: Optional workflow ID or filename to filter by.
            token: Optional GitHub PAT.

        Returns:
            List of new WorkflowRun instances.
        """
        all_runs = self.fetch_workflow_runs(owner, repo, workflow=workflow, token=token)

        if latest_run_timestamp is None:
            return all_runs

        # Filter to only runs created after the latest timestamp
        new_runs = [run for run in all_runs if run.created_at > latest_run_timestamp]
        return new_runs


__all__ = ["GitHubFetchService"]
