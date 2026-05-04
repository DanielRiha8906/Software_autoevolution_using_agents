"""GitHub CLI (gh) fetcher for retrieving workflow runs."""

import json
import subprocess
from datetime import datetime
from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.github_workflow_run_factory import GitHubWorkflowRunFactory
from ..exceptions import GitHubAPIError, GitHubNetworkError


class GitHubCLIFetcher:
    """Fetch workflow runs using the GitHub CLI (gh command)."""

    def is_available(self) -> bool:
        """
        Check if gh CLI is installed and available.

        Args:
            None

        Returns:
            True if gh CLI is found in PATH and responsive, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                timeout=5,
                text=True,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs using gh CLI.

        Uses 'gh run list' command with JSON output. The gh CLI automatically
        uses the authenticated user's token, so explicit token is not required.

        Args:
            owner: GitHub repository owner (username or organization).
            repo: GitHub repository name.
            status: Optional workflow status filter (e.g., "completed", "in_progress").
            branch: Optional branch name filter.
            created_after: Optional datetime; only fetch runs created on or after this date.
                          Note: gh CLI filtering is limited; post-processing may be needed.

        Returns:
            List of WorkflowRun objects fetched via gh CLI.

        Raises:
            GitHubAPIError: If gh CLI returns an error or malformed output.
            GitHubNetworkError: If gh CLI execution fails.
        """
        if not self.is_available():
            raise GitHubNetworkError(
                "GitHub CLI (gh) is not installed or not authenticated. "
                "Install via: https://cli.github.com/"
            )

        try:
            # Build gh run list command with JSON output
            cmd = [
                "gh",
                "run",
                "list",
                "--repo",
                f"{owner}/{repo}",
                "--json",
                "id,name,status,conclusion,createdAt,updatedAt,databaseId,headBranch,headSha,runNumber",
                "--limit",
                "1000",  # Fetch up to 1000 runs (practical maximum for gh CLI)
            ]

            # Add optional filters if provided
            if status:
                cmd.extend(["--status", status])

            # Note: gh CLI doesn't have direct branch filter, so we'll filter post-fetch
            # Note: gh CLI doesn't have direct created_after filter, so we'll filter post-fetch

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise GitHubAPIError(
                    f"gh CLI command failed: {result.stderr or result.stdout}"
                )

            # Parse JSON output
            try:
                runs_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise GitHubAPIError(
                    f"Failed to parse gh CLI JSON output: {e}\nOutput: {result.stdout[:200]}"
                )

            # Convert gh CLI field names to GitHub API field names and create WorkflowRun objects
            runs: List[WorkflowRun] = []

            for run_data in runs_data:
                try:
                    # Map gh CLI field names to GitHub API field names
                    # gh CLI: createdAt, updatedAt, headBranch, headSha, databaseId
                    # GitHub API: created_at, updated_at, head_branch, head_sha, id, run_number
                    api_data = {
                        "id": run_data.get("databaseId") or run_data.get("id"),
                        "name": run_data.get("name", ""),
                        "status": run_data.get("status", "").lower(),
                        "conclusion": run_data.get("conclusion", "").lower() if run_data.get("conclusion") else None,
                        "created_at": run_data.get("createdAt", ""),
                        "updated_at": run_data.get("updatedAt"),
                        "run_number": run_data.get("runNumber"),
                        "head_sha": run_data.get("headSha"),
                        "head_branch": run_data.get("headBranch", ""),
                    }

                    # Apply post-fetch filters (since gh CLI has limited filter options)
                    if branch and api_data["head_branch"] != branch:
                        continue

                    if created_after:
                        run_created = GitHubWorkflowRunFactory._parse_datetime(
                            api_data["created_at"]
                        )
                        if run_created < created_after:
                            continue

                    # Convert to WorkflowRun
                    run = GitHubWorkflowRunFactory.from_github_api_response(api_data)
                    runs.append(run)

                except (ValueError, KeyError) as e:
                    # Skip malformed records
                    print(f"Warning: Skipping malformed run record from gh CLI: {e}")
                    continue

            return runs

        except subprocess.TimeoutExpired:
            raise GitHubNetworkError("gh CLI command timed out")
        except Exception as e:
            raise GitHubNetworkError(f"Failed to execute gh CLI: {e}")
