"""Service for fetching workflow runs and attempts from GitHub."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..adapters.github.api_client import GitHubApiClient
from ..adapters.github.cli_adapter import GitHubCliAdapter
from ..adapters.github.converter import GitHubToWorkflowConverter
from ..adapters.github.token_resolver import GitHubTokenResolver
from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_run import WorkflowRun

logger = logging.getLogger(__name__)


class GitHubIntegrationService:
    """Service for fetching workflow runs and attempts from GitHub."""

    def __init__(
        self,
        fetch_mode: str = "api",
        token_resolver: Optional[GitHubTokenResolver] = None,
    ):
        """
        Initialize the GitHub integration service.

        Args:
            fetch_mode: "api" for requests-based REST API, "cli" for gh CLI
            token_resolver: Optional GitHubTokenResolver instance. If None, creates default.
        """
        self.fetch_mode = fetch_mode
        self.token_resolver = token_resolver or GitHubTokenResolver()
        self.converter = GitHubToWorkflowConverter()
        self._api_client: Optional[GitHubApiClient] = None
        self._cli_adapter: Optional[GitHubCliAdapter] = None
        self._token: Optional[str] = None

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
        api_client = GitHubApiClient(token)
        api_runs = api_client.get_runs(owner, repo, limit)

        runs = []
        for api_run in api_runs:
            if len(runs) >= limit:
                break

            # Filter by workflow name if specified
            if workflow_name and api_run.get("name") != workflow_name:
                continue

            try:
                run = self.converter.convert_run(api_run, repo)
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
                run = self.converter.convert_run(api_run, repo)
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
        api_client = GitHubApiClient(token)

        try:
            api_attempts = api_client.get_run_attempts(owner, repo, run_id)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to fetch attempts from GitHub API: {e}")

        attempts = []
        for api_attempt in api_attempts:
            try:
                attempt = self.converter.convert_attempt(api_attempt, run_id, repo)
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
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON output from gh CLI: {e}")

        # Parse the structure returned by gh
        if "attempts" not in attempt_data:
            raise RuntimeError("Invalid gh CLI output: missing 'attempts' key")

        attempts_list = attempt_data["attempts"]

        attempts = []
        for api_attempt in attempts_list:
            try:
                attempt = self.converter.convert_attempt(api_attempt, run_id, repo)
                attempts.append(attempt)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to convert CLI attempt: {e}")
                continue

        logger.info(f"Fetched {len(attempts)} attempts for run {run_id} via gh CLI")
        return attempts

    # Backward compatibility: delegate to adapters
    def _resolve_token(self) -> str:
        """
        Resolve GitHub token from environment, secrets file, or prompt.

        DEPRECATED: Use GitHubTokenResolver directly instead.

        Returns:
            The resolved token string.

        Raises:
            RuntimeError: If token cannot be resolved.
        """
        return self.token_resolver.resolve()

    def _validate_token(self, token: str) -> bool:
        """
        Validate the GitHub token by testing connectivity.

        DEPRECATED: Use GitHubTokenResolver.validate() directly instead.

        Args:
            token: The GitHub token to validate

        Returns:
            True if token is valid, False otherwise
        """
        return self.token_resolver.validate(token, self.fetch_mode)

    def _convert_api_run(self, api_data: Dict, repo: str) -> WorkflowRun:
        """
        Convert GitHub API run data to WorkflowRun domain model.

        DEPRECATED: Use GitHubToWorkflowConverter.convert_run() directly instead.

        Args:
            api_data: Raw API response dict
            repo: Repository name (for reference)

        Returns:
            WorkflowRun instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        return self.converter.convert_run(api_data, repo)

    def _convert_api_attempt(self, api_data: Dict, run_id: str, repo: str) -> WorkflowRunAttempt:
        """
        Convert GitHub API attempt data to WorkflowRunAttempt domain model.

        DEPRECATED: Use GitHubToWorkflowConverter.convert_attempt() directly instead.

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
        return self.converter.convert_attempt(api_data, run_id, repo)

    @staticmethod
    def _parse_github_timestamp(timestamp_str: str) -> datetime:
        """
        Parse a GitHub API timestamp string to datetime.

        DEPRECATED: Use GitHubToWorkflowConverter._parse_github_timestamp() directly instead.

        GitHub API returns ISO 8601 strings, often with Z suffix for UTC.

        Args:
            timestamp_str: Timestamp string from GitHub API

        Returns:
            datetime object in UTC timezone

        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Delegate to the static implementation in the converter
        return GitHubToWorkflowConverter()._parse_github_timestamp(timestamp_str)

    def _call_gh_cli(self, args: List[str]) -> str:
        """
        Execute a gh CLI command and return output.

        DEPRECATED: Use GitHubCliAdapter directly instead.

        Args:
            args: Command arguments (first element should be "gh")

        Returns:
            Standard output as string

        Raises:
            RuntimeError: If command fails
        """
        cli_adapter = GitHubCliAdapter()
        return cli_adapter._execute_command(args)

    def _call_api(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute an API request.

        DEPRECATED: Use GitHubApiClient directly instead.

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
        api_client = GitHubApiClient(token)

        import requests
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
