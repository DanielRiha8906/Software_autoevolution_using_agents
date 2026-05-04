"""GitHub API client for fetching workflow runs and attempts."""

from typing import Any, List, Optional
import requests

from .exceptions import GitHubApiError
from .token_validator import GitHubTokenValidator


class GitHubApiClient:
    """Client for GitHub Actions API with workflow run and attempt retrieval."""

    BASE_URL = "https://api.github.com"
    TIMEOUT = 30

    def __init__(self, token: str):
        """Initialize GitHub API client.

        Args:
            token: GitHub authentication token

        Raises:
            GitHubApiError: If token validation fails
        """
        GitHubTokenValidator.validate(token)
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        })

    def fetch_workflow_runs(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 100,
    ) -> List[dict]:
        """Fetch workflow runs for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Optional branch filter
            status: Optional status filter (queued, in_progress, completed)
            per_page: Results per page (max 100)

        Returns:
            List of workflow run dictionaries from GitHub API

        Raises:
            GitHubApiError: If API request fails
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs"
        params = {"per_page": per_page}

        if branch:
            params["head"] = branch
        if status:
            params["status"] = status

        all_runs = []

        try:
            while url:
                response = self._session.get(url, params=params, timeout=self.TIMEOUT)

                if response.status_code == 401:
                    raise GitHubApiError("Authentication failed (401). Check token validity.")
                elif response.status_code == 403:
                    raise GitHubApiError("Rate limited or forbidden (403). Check token permissions.")
                elif response.status_code == 404:
                    raise GitHubApiError(f"Repository not found: {owner}/{repo}")
                elif response.status_code >= 400:
                    raise GitHubApiError(f"GitHub API error {response.status_code}: {response.text}")

                data = response.json()
                all_runs.extend(data.get("workflow_runs", []))

                # Handle pagination via Link header
                url = self._get_next_page_url(response)
                params = {}  # Clear params for subsequent pagination requests

        except requests.exceptions.ConnectionError as e:
            raise GitHubApiError(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise GitHubApiError(f"Request timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise GitHubApiError(f"Request failed: {str(e)}")

        return all_runs

    def fetch_attempts(self, owner: str, repo: str, run_id: int) -> List[dict]:
        """Fetch attempts for a specific workflow run.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            List of attempt dictionaries from GitHub API

        Raises:
            GitHubApiError: If API request fails
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/attempts"

        try:
            response = self._session.get(url, timeout=self.TIMEOUT)

            if response.status_code == 401:
                raise GitHubApiError("Authentication failed (401). Check token validity.")
            elif response.status_code == 403:
                raise GitHubApiError("Rate limited or forbidden (403). Check token permissions.")
            elif response.status_code == 404:
                raise GitHubApiError(f"Run not found: {owner}/{repo}#{run_id}")
            elif response.status_code >= 400:
                raise GitHubApiError(f"GitHub API error {response.status_code}: {response.text}")

            data = response.json()
            return data.get("workflow_run_attempts", [])

        except requests.exceptions.ConnectionError as e:
            raise GitHubApiError(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise GitHubApiError(f"Request timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise GitHubApiError(f"Request failed: {str(e)}")

    @staticmethod
    def _get_next_page_url(response: requests.Response) -> Optional[str]:
        """Extract next page URL from Link header.

        Args:
            response: HTTP response with Link header

        Returns:
            Next page URL or None if no more pages
        """
        link_header = response.headers.get("Link", "")
        if not link_header:
            return None

        links = link_header.split(",")
        for link in links:
            if 'rel="next"' in link:
                # Extract URL from <URL>; rel="next"
                url_part = link.split(";")[0].strip()
                if url_part.startswith("<") and url_part.endswith(">"):
                    return url_part[1:-1]

        return None
