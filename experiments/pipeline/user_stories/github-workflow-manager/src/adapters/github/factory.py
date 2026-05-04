"""Factory for converting GitHub API responses to WorkflowRun domain objects."""

from datetime import datetime
from typing import Optional

from ...models.workflow_run import WorkflowRun
from ...models.workflow_status import WorkflowStatus
from ...models.workflow_conclusion import WorkflowConclusion


class GitHubWorkflowRunFactory:
    """Convert GitHub API response data to WorkflowRun domain model."""

    @staticmethod
    def from_github_api_response(data: dict) -> WorkflowRun:
        """
        Convert a GitHub API workflow run response to a WorkflowRun object.

        Maps GitHub API field names to WorkflowRun attributes, handling type conversions,
        enum conversions, and datetime parsing.

        Args:
            data: Dictionary from GitHub API response containing workflow run data.
                  Expected fields: id, name, status, conclusion, created_at, updated_at,
                  run_number, head_sha, head_branch, and optionally other fields.

        Returns:
            WorkflowRun object with mapped fields.

        Raises:
            ValueError: If required fields are missing or enum conversion fails.
            KeyError: If critical fields are missing from the API response.
        """
        # Map and convert fields from GitHub API to WorkflowRun
        run_id = str(data["id"])  # GitHub API returns int; convert to string
        workflow_name = data["name"]
        branch = data["head_branch"]
        status = GitHubWorkflowRunFactory._parse_status(data["status"])
        conclusion = GitHubWorkflowRunFactory._parse_conclusion(data.get("conclusion"))
        created_at = GitHubWorkflowRunFactory._parse_datetime(data["created_at"])
        updated_at = (
            GitHubWorkflowRunFactory._parse_datetime(data["updated_at"])
            if data.get("updated_at")
            else None
        )
        run_number = data.get("run_number")
        commit_sha = data.get("head_sha")

        # Calculate duration from timestamps
        duration_seconds = GitHubWorkflowRunFactory._calculate_duration(
            created_at, updated_at
        )

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

    @staticmethod
    def _parse_status(status_str: str) -> WorkflowStatus:
        """
        Convert GitHub API status string to WorkflowStatus enum.

        GitHub API returns lowercase status values that match enum values.

        Args:
            status_str: Status string from GitHub API (e.g., "completed", "in_progress")

        Returns:
            WorkflowStatus enum value.

        Raises:
            ValueError: If status_str does not match any WorkflowStatus enum value.
        """
        try:
            return WorkflowStatus(status_str.lower())
        except ValueError:
            raise ValueError(
                f"Unknown workflow status '{status_str}' from GitHub API. "
                f"Valid values: {', '.join(s.value for s in WorkflowStatus)}"
            )

    @staticmethod
    def _parse_conclusion(conclusion_str: Optional[str]) -> Optional[WorkflowConclusion]:
        """
        Convert GitHub API conclusion string to WorkflowConclusion enum.

        GitHub API returns lowercase conclusion values (or None) that match enum values.

        Args:
            conclusion_str: Conclusion string from GitHub API or None if not concluded.

        Returns:
            WorkflowConclusion enum value or None.

        Raises:
            ValueError: If conclusion_str does not match any WorkflowConclusion enum value.
        """
        if conclusion_str is None:
            return None
        try:
            # GitHub API uses "action_required", we use "action_required" - should match
            return WorkflowConclusion(conclusion_str.lower())
        except ValueError:
            raise ValueError(
                f"Unknown workflow conclusion '{conclusion_str}' from GitHub API. "
                f"Valid values: {', '.join(c.value for c in WorkflowConclusion)} or null"
            )

    @staticmethod
    def _parse_datetime(datetime_str: str) -> datetime:
        """
        Parse ISO 8601 datetime string from GitHub API.

        GitHub API returns UTC timestamps in ISO 8601 format (e.g., "2025-05-03T10:30:00Z").

        Args:
            datetime_str: ISO 8601 formatted datetime string.

        Returns:
            timezone-aware datetime object in UTC.

        Raises:
            ValueError: If datetime string cannot be parsed.
        """
        try:
            dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            return dt
        except ValueError as e:
            raise ValueError(
                f"Could not parse datetime '{datetime_str}' from GitHub API. "
                f"Expected ISO 8601 format (e.g., 2025-05-03T10:30:00Z): {e}"
            )

    @staticmethod
    def _calculate_duration(
        created_at: datetime, updated_at: Optional[datetime]
    ) -> float:
        """
        Calculate workflow run duration from timestamps.

        Duration is computed as (updated_at - created_at).total_seconds().
        If updated_at is missing or in the future (clock skew), returns 0.0.

        Args:
            created_at: Workflow creation timestamp.
            updated_at: Workflow update timestamp (may be None).

        Returns:
            Duration in seconds as float. Returns 0.0 if duration cannot be calculated.
        """
        if updated_at is None:
            return 0.0

        duration = (updated_at - created_at).total_seconds()

        # Handle edge case of negative duration due to clock skew
        if duration < 0:
            return 0.0

        return duration
