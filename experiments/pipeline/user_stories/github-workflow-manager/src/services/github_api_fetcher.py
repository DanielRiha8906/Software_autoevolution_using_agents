"""GitHub REST API fetcher for retrieving workflow runs."""

from datetime import datetime
from typing import List, Optional

import requests

from ..models.workflow_run import WorkflowRun
from ..models.github_workflow_run_factory import GitHubWorkflowRunFactory
from ..exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)


class GitHubAPIFetcher:
    """Fetch workflow runs from GitHub REST API."""

    BASE_URL = "https://api.github.com"
    DEFAULT_PER_PAGE = 30
    TIMEOUT_SECONDS = 10

    def __init__(self, token: str):
        """
        Initialize GitHub API fetcher with authentication token.

        Args:
            token: GitHub Personal Access Token for authentication.
        """
        self._token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "workflow-tracker",
        }

    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs from GitHub repository.

        Retrieves workflow runs from the specified repository, with optional filtering
        by status, branch, and creation date. Handles pagination automatically.

        Args:
            owner: GitHub repository owner (username or organization).
            repo: GitHub repository name.
            status: Optional workflow status filter (e.g., "completed", "in_progress").
            branch: Optional branch name filter.
            created_after: Optional datetime; only fetch runs created on or after this date.
            per_page: Number of results per API page (default 30, max 100).

        Returns:
            List of WorkflowRun objects fetched from GitHub.

        Raises:
            GitHubAuthError: If authentication fails (invalid/expired token).
            GitHubRateLimitError: If GitHub API rate limit is exceeded.
            GitHubAPIError: If API request fails (404, malformed response, etc.).
            GitHubNetworkError: If network connection fails.
        """
        runs: List[WorkflowRun] = []
        page = 1

        while True:
            try:
                response = self._fetch_page(
                    owner, repo, status, branch, created_after, page, per_page
                )

                # Check for successful response
                if response.status_code == 401:
                    raise GitHubAuthError(
                        "Authentication failed. Check that your token is valid and not expired."
                    )

                if response.status_code == 403:
                    # Check if rate limited
                    remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
                    if remaining == "0":
                        raise GitHubRateLimitError(
                            "GitHub API rate limit exceeded. Please try again later."
                        )
                    raise GitHubAPIError(
                        f"GitHub API returned 403 Forbidden. "
                        f"Check token permissions (need 'repo' scope). "
                        f"Rate limit remaining: {remaining}"
                    )

                if response.status_code == 404:
                    raise GitHubAPIError(
                        f"Repository not found: {owner}/{repo}. "
                        "Check owner and repo names."
                    )

                if response.status_code >= 400:
                    raise GitHubAPIError(
                        f"GitHub API request failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )

                data = response.json()
                workflow_runs = data.get("workflow_runs", [])

                # Convert each API response to WorkflowRun object
                for run_data in workflow_runs:
                    try:
                        run = GitHubWorkflowRunFactory.from_github_api_response(
                            run_data
                        )
                        runs.append(run)
                    except (ValueError, KeyError) as e:
                        # Skip malformed records; log but don't fail entire fetch
                        print(f"Warning: Skipping malformed run record: {e}")
                        continue

                # Check if there are more pages
                if len(workflow_runs) < per_page:
                    # Last page reached
                    break

                page += 1

            except (requests.ConnectionError, requests.Timeout) as e:
                raise GitHubNetworkError(
                    f"Network error while fetching from GitHub API: {e}"
                )
            except requests.RequestException as e:
                raise GitHubNetworkError(f"Request failed: {e}")

        return runs

    def _fetch_page(
        self,
        owner: str,
        repo: str,
        status: Optional[str],
        branch: Optional[str],
        created_after: Optional[datetime],
        page: int,
        per_page: int,
    ) -> requests.Response:
        """
        Fetch a single page of workflow runs from GitHub API.

        Args:
            owner: Repository owner.
            repo: Repository name.
            status: Optional status filter.
            branch: Optional branch filter.
            created_after: Optional created-after date filter.
            page: Page number (1-indexed).
            per_page: Results per page.

        Returns:
            requests.Response object from GitHub API.

        Raises:
            Network-related exceptions from requests library.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs"

        # Build query parameters
        params = {
            "page": page,
            "per_page": per_page,
        }

        if status:
            params["status"] = status

        if branch:
            params["branch"] = branch

        if created_after:
            # GitHub API uses 'created' filter in format 'YYYY-MM-DDTHH:MM:SSZ'
            # Build a filter: '>=' (greater than or equal)
            created_str = created_after.isoformat().replace("+00:00", "Z")
            params["created"] = f">={created_str}"

        response = requests.get(
            url,
            headers=self._headers,
            params=params,
            timeout=self.TIMEOUT_SECONDS,
        )

        return response
