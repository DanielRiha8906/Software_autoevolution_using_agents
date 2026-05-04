"""GitHub API service for fetching workflow runs."""

from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..adapters.protocols import GitHubAPIClient, GitHubDataMapper


class GitHubFetchService:
    """Service for fetching workflow runs from GitHub API."""

    def __init__(
        self,
        owner: str,
        repo: str,
        github_api_client: Optional[GitHubAPIClient] = None,
        data_mapper: Optional[GitHubDataMapper] = None,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        """Initialize GitHubFetchService.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.
            github_api_client: GitHubAPIClient instance for API requests.
                If None, defaults to GhCliGitHubAdapter.
            data_mapper: GitHubDataMapper instance for data mapping.
                If None, defaults to GithubDataMapperImpl.
            token: GitHub API token for authentication (optional).
            base_url: Base URL for GitHub API (default: https://api.github.com).
        """
        # Lazy import to avoid circular dependencies
        if github_api_client is None:
            from ..adapters.github_cli_adapter import GhCliGitHubAdapter
            github_api_client = GhCliGitHubAdapter()

        if data_mapper is None:
            from ..adapters.github_data_mapper import GithubDataMapperImpl
            data_mapper = GithubDataMapperImpl()

        self.owner = owner
        self.repo = repo
        self.github_api_client = github_api_client
        self.data_mapper = data_mapper
        self.token = token
        self.base_url = base_url


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
        response = self.github_api_client.make_request(endpoint, params)

        runs = []
        for github_run in response.get("workflow_runs", []):
            try:
                run = self.data_mapper.map_github_run_to_workflow_run(github_run)
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
        github_run = self.github_api_client.make_request(endpoint)
        return self.data_mapper.map_github_run_to_workflow_run(github_run)

    def get_available_workflows(self) -> List[dict]:
        """Fetch list of available workflows in the repository.

        Returns:
            List of workflow dictionaries with 'id' and 'name' keys.

        Raises:
            GitHubException: If API call fails.
        """
        endpoint = f"/repos/{self.owner}/{self.repo}/actions/workflows"
        response = self.github_api_client.make_request(endpoint)

        workflows = []
        for workflow in response.get("workflows", []):
            workflows.append({
                "id": workflow.get("id"),
                "name": workflow.get("name"),
            })

        return workflows
