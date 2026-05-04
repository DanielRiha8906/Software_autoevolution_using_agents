"""GitHub REST API client for fetching workflow data."""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GitHubApiClient:
    """Client for GitHub REST API calls."""

    API_BASE_URL = "https://api.github.com"

    def __init__(self, token: str) -> None:
        """
        Initialize the API client.

        Args:
            token: GitHub authentication token
        """
        self.token = token
        self.headers = {"Authorization": f"token {token}"}

    def get_runs(
        self,
        owner: str,
        repo: str,
        limit: int = 30,
    ) -> List[Dict]:
        """
        Fetch workflow runs from GitHub API.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            limit: Maximum number of runs to fetch (default 30)

        Returns:
            List of raw run data dictionaries

        Raises:
            RuntimeError: If API call fails
        """
        url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/actions/runs"
        params = {"per_page": min(limit, 100)}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch runs from GitHub API: {e}")

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON response from GitHub API: {e}")

        runs = data.get("workflow_runs", [])
        return runs[:limit]

    def get_run_attempts(
        self,
        owner: str,
        repo: str,
        run_id: str,
    ) -> List[Dict]:
        """
        Fetch workflow attempts for a specific run.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            run_id: GitHub workflow run ID

        Returns:
            List of raw attempt data dictionaries

        Raises:
            RuntimeError: If API call fails
        """
        url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/attempts"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch attempts from GitHub API: {e}")

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON response from GitHub API: {e}")

        attempts = data.get("workflow_runs", [])
        return attempts
