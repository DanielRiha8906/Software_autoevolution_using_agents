"""Service for importing workflow runs from GitHub."""

from datetime import datetime
from typing import Optional

from ..github_api.client import GitHubApiClient
from ..github_api.mapper import GitHubRunMapper
from ..github_api.token_resolver import TokenResolver
from ..github_api.exceptions import GitHubApiError, TokenResolutionError, GitHubImportError
from ..models.import_result import ImportResult
from .workflow_run_service import WorkflowRunService


class GitHubImportService:
    """Service for importing workflow runs from GitHub with deduplication.

    Handles:
    - Token resolution from multiple sources
    - GitHub API calls
    - Response mapping to domain models
    - Deduplication by run_number + workflow_name
    - Force mode updates
    - Incremental importing
    """

    def __init__(self, run_service: WorkflowRunService):
        """Initialize GitHubImportService.

        Args:
            run_service: The WorkflowRunService for persistence
        """
        self._run_service = run_service

    def import_from_github(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        github_token: Optional[str] = None,
        force: bool = False,
        incremental: bool = False,
    ) -> ImportResult:
        """Import workflow runs from GitHub.

        Args:
            owner: GitHub owner/organization
            repo: GitHub repository name
            branch: Optional branch filter
            status: Optional status filter (queued, in_progress, completed)
            github_token: GitHub token (optional, can be resolved from env)
            force: If True, update existing runs with same run_number
            incremental: If True, only fetch runs with created_at > latest stored run

        Returns:
            ImportResult with import statistics

        Raises:
            TokenResolutionError: If GitHub token cannot be resolved
            GitHubImportError: If import operation fails
        """
        # Resolve token from priority chain
        try:
            token = TokenResolver.resolve(github_token, prompt_if_missing=True)
        except TokenResolutionError as e:
            return ImportResult(
                total=0,
                imported=0,
                skipped=0,
                errors=[str(e)],
            )

        # Create API client
        try:
            client = GitHubApiClient(token)
        except GitHubApiError as e:
            return ImportResult(
                total=0,
                imported=0,
                skipped=0,
                errors=[f"Failed to initialize GitHub client: {str(e)}"],
            )

        # Fetch workflow runs from GitHub
        try:
            github_runs = client.fetch_workflow_runs(
                owner=owner,
                repo=repo,
                branch=branch,
                status=status,
            )
        except GitHubApiError as e:
            return ImportResult(
                total=0,
                imported=0,
                skipped=0,
                errors=[f"Failed to fetch workflow runs: {str(e)}"],
            )

        # Process incremental import
        if incremental:
            github_runs = self._filter_incremental(github_runs)

        # Map and deduplicate
        imported_count = 0
        skipped_count = 0
        updated_count = 0
        error_messages = []

        total = len(github_runs)

        for github_run in github_runs:
            try:
                # Map GitHub run to domain model
                run_number = github_run.get("run_number")
                workflow_name = github_run.get("name", "unknown")

                domain_run = GitHubRunMapper.map_run(github_run, workflow_name)

                # Check for duplicates by run_number + workflow_name
                existing = self._find_duplicate(run_number, workflow_name)

                if existing is not None:
                    if force:
                        # Update existing run
                        domain_run.attempts = existing.attempts  # Preserve attempts
                        self._run_service.update_workflow_run(domain_run)
                        updated_count += 1
                    else:
                        # Skip duplicate
                        skipped_count += 1
                else:
                    # Add new run
                    self._run_service.add_workflow_run(domain_run)
                    imported_count += 1

                # Fetch and add attempts if run completed
                if domain_run.status.value == "completed":
                    try:
                        attempts = client.fetch_attempts(owner, repo, int(domain_run.id))
                        for github_attempt in attempts:
                            try:
                                attempt = GitHubRunMapper.map_attempt(
                                    github_attempt,
                                    domain_run.id,
                                )
                                # Check if attempt already exists
                                if not any(
                                    a.attempt_number == attempt.attempt_number
                                    for a in domain_run.attempts
                                ):
                                    domain_run.attempts.append(attempt)
                            except ValueError as e:
                                error_messages.append(
                                    f"Run {domain_run.id}, attempt mapping: {str(e)}"
                                )
                        # Update run with attempts
                        if domain_run.attempts:
                            self._run_service.update_workflow_run(domain_run)
                    except GitHubApiError as e:
                        error_messages.append(
                            f"Failed to fetch attempts for run {domain_run.id}: {str(e)}"
                        )

            except ValueError as e:
                error_messages.append(f"Run mapping error: {str(e)}")
            except Exception as e:
                error_messages.append(f"Unexpected error: {str(e)}")

        return ImportResult(
            total=total,
            imported=imported_count,
            skipped=skipped_count,
            errors=error_messages,
            updated=updated_count,
        )

    def _find_duplicate(self, run_number: Optional[int], workflow_name: str) -> Optional:
        """Find existing run by run_number + workflow_name (natural key).

        Args:
            run_number: The GitHub run number
            workflow_name: The workflow name

        Returns:
            Existing WorkflowRun if found, None otherwise
        """
        if run_number is None:
            return None

        for run in self._run_service.list_runs():
            if run.run_number == run_number and run.workflow_name == workflow_name:
                return run

        return None

    def _filter_incremental(self, github_runs: list) -> list:
        """Filter runs to only include those created after latest stored run.

        Args:
            github_runs: List of GitHub run dicts

        Returns:
            Filtered list of GitHub run dicts
        """
        # Find latest created_at from stored runs
        all_stored = self._run_service.list_runs()
        if not all_stored:
            return github_runs

        latest_stored = max(all_stored, key=lambda r: r.created_at)
        latest_time = latest_stored.created_at

        # Filter to only runs created after latest stored run
        filtered = []
        for github_run in github_runs:
            created_at_str = github_run.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                if created_at > latest_time:
                    filtered.append(github_run)
            except (ValueError, AttributeError):
                # Skip runs with invalid timestamps
                pass

        return filtered
