"""GitHub API service for fetching workflow runs."""

from typing import List, Optional
from datetime import datetime, timezone
import subprocess
import json

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..exceptions import (
    GitHubAuthenticationError,
    GitHubRepositoryNotFoundError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubDataParseError,
)


class GitHubFetchService:
    """Service for fetching workflow runs from GitHub API."""

    def __init__(
        self,
        owner: str,
        repo: str,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
    ) -> None:
        """Initialize GitHubFetchService.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.
            token: GitHub API token for authentication (optional).
            base_url: Base URL for GitHub API (default: https://api.github.com).
            timeout: Request timeout in seconds (default: 30).
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = base_url
        self.timeout = timeout

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GitHub API request using gh CLI.

        Args:
            endpoint: API endpoint path (may have leading slash).
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubAuthenticationError: If authentication fails (401/403).
            GitHubRepositoryNotFoundError: If 404 response.
            GitHubAPIError: If API error occurs.
            GitHubNetworkError: If gh CLI not found or network error occurs.
            GitHubDataParseError: If response cannot be parsed as JSON.
        """
        # Remove leading slash if present (gh CLI expects no leading slash)
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]

        # Build gh api command
        cmd = ["gh", "api", endpoint]

        # Add query parameters as CLI flags
        if params:
            for key, value in params.items():
                if value is not None:
                    # Use -F for field values (automatically converts to proper JSON)
                    cmd.extend(["-F", f"{key}={value}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError:
            raise GitHubNetworkError("gh CLI not installed or not in PATH")
        except subprocess.TimeoutExpired:
            raise GitHubNetworkError("gh CLI request timeout")

        # Check for errors in stderr or non-zero exit code
        if result.returncode != 0:
            stderr = result.stderr.lower()

            # Check for authentication errors
            if "401" in stderr or "unauthorized" in stderr:
                raise GitHubAuthenticationError(
                    "Authentication failed. Check your GitHub token or gh CLI authentication."
                )
            # Check for 403 (forbidden/rate limit)
            elif "403" in stderr or "rate limit" in stderr or "forbidden" in stderr:
                raise GitHubAuthenticationError(
                    "Authentication failed or rate limited. Check your token permissions."
                )
            # Check for 404 (not found)
            elif "404" in stderr or "not found" in stderr:
                raise GitHubRepositoryNotFoundError(
                    "Repository not found. Check owner/repo names."
                )
            # Generic API error
            else:
                raise GitHubAPIError(f"GitHub API error: {result.stderr}")

        # Parse JSON response
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise GitHubDataParseError(f"Failed to parse GitHub API response: {e}")

    def _parse_datetime(self, iso_string: str) -> datetime:
        """Parse ISO 8601 datetime string from GitHub API.

        Args:
            iso_string: ISO 8601 datetime string (e.g., "2026-05-03T10:30:00Z").

        Returns:
            datetime object with UTC timezone.
        """
        return datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def _map_github_run_to_workflow_run(self, github_run: dict) -> WorkflowRun:
        """Map GitHub API run object to WorkflowRun model.

        Args:
            github_run: GitHub API run response object.

        Returns:
            WorkflowRun instance.
        """
        run_id = str(github_run["id"])
        workflow_name = github_run.get("name", "unknown")
        branch = github_run.get("head_branch", "unknown")
        status_str = github_run.get("status", "completed").lower()
        conclusion_str = github_run.get("conclusion")
        created_at_str = github_run.get("created_at", "")
        updated_at_str = github_run.get("updated_at")
        run_number = github_run.get("run_number")
        commit_sha = github_run.get("head_sha")

        # Convert status to WorkflowStatus enum
        try:
            status = WorkflowStatus(status_str)
        except ValueError:
            status = WorkflowStatus.COMPLETED

        # Convert conclusion to WorkflowConclusion enum if present
        conclusion = None
        if conclusion_str:
            try:
                conclusion = WorkflowConclusion(conclusion_str.lower())
            except ValueError:
                conclusion = None

        # Parse datetimes
        created_at = self._parse_datetime(created_at_str) if created_at_str else datetime.now(timezone.utc)
        updated_at = self._parse_datetime(updated_at_str) if updated_at_str else None

        # Calculate duration
        duration_seconds = 0.0
        if created_at and updated_at:
            delta = updated_at - created_at
            duration_seconds = delta.total_seconds()

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
            duration_seconds=duration_seconds,
        )

    def _validate_params(
        self,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        limit: int = 30,
    ) -> None:
        """Validate input parameters.

        Args:
            status: Workflow status filter.
            conclusion: Workflow conclusion filter.
            limit: Maximum number of runs to fetch.

        Raises:
            ValueError: If parameters are invalid.
        """
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        if status:
            valid_statuses = {s.value for s in WorkflowStatus}
            if status.lower() not in valid_statuses:
                raise ValueError(f"status must be one of {valid_statuses}")

        if conclusion:
            valid_conclusions = {c.value for c in WorkflowConclusion}
            if conclusion.lower() not in valid_conclusions:
                raise ValueError(f"conclusion must be one of {valid_conclusions}")

    def fetch_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        limit: int = 30,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub.

        Args:
            workflow_id: Filter by workflow ID (optional).
            status: Filter by status (optional).
            conclusion: Filter by conclusion (optional).
            limit: Maximum number of runs to fetch (1-100, default 30).

        Returns:
            List of WorkflowRun objects.

        Raises:
            ValueError: If parameters are invalid.
            GitHubException: If API call fails.
        """
        self._validate_params(status, conclusion, limit)

        params = {"per_page": limit, "page": 1}

        if workflow_id:
            params["workflow_id"] = workflow_id

        if status:
            params["status"] = status.lower()

        if conclusion:
            params["conclusion"] = conclusion.lower()

        endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs"
        response = self._make_request(endpoint, params)

        runs = []
        for github_run in response.get("workflow_runs", []):
            try:
                run = self._map_github_run_to_workflow_run(github_run)
                runs.append(run)
            except Exception:
                # Skip runs that fail to parse
                pass

        return runs

    def fetch_workflow_run_detail(self, run_id: str) -> WorkflowRun:
        """Fetch details for a single workflow run.

        Args:
            run_id: Run ID to fetch.

        Returns:
            WorkflowRun object.

        Raises:
            GitHubException: If API call fails.
        """
        endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"
        github_run = self._make_request(endpoint)
        return self._map_github_run_to_workflow_run(github_run)

    def get_available_workflows(self) -> List[dict]:
        """Fetch list of available workflows in the repository.

        Returns:
            List of workflow dictionaries with 'id' and 'name' keys.

        Raises:
            GitHubException: If API call fails.
        """
        endpoint = f"/repos/{self.owner}/{self.repo}/actions/workflows"
        response = self._make_request(endpoint)

        workflows = []
        for workflow in response.get("workflows", []):
            workflows.append({
                "id": workflow.get("id"),
                "name": workflow.get("name"),
            })

        return workflows
