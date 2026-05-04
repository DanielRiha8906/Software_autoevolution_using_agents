"""GitHub data mapper for API responses."""

from datetime import datetime, timezone

from .protocols import GitHubDataMapper
from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class GithubDataMapperImpl(GitHubDataMapper):
    """Implementation of GitHub data mapper."""

    def parse_datetime(self, iso_string: str) -> datetime:
        """Parse ISO 8601 datetime string from GitHub API.

        Args:
            iso_string: ISO 8601 datetime string (e.g., "2026-05-03T10:30:00Z").

        Returns:
            datetime object with UTC timezone.
        """
        return datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def map_github_run_to_workflow_run(self, github_run: dict) -> WorkflowRun:
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
        created_at = self.parse_datetime(created_at_str) if created_at_str else datetime.now(timezone.utc)
        updated_at = self.parse_datetime(updated_at_str) if updated_at_str else None

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
