"""GitHub API response to domain model converter."""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from ...models.workflow_attempt import WorkflowRunAttempt
from ...models.workflow_conclusion import WorkflowConclusion
from ...models.workflow_run import WorkflowRun
from ...models.workflow_status import WorkflowStatus

logger = logging.getLogger(__name__)


class GitHubToWorkflowConverter:
    """Converts GitHub API responses to domain models."""

    def __init__(self) -> None:
        """Initialize the converter."""
        pass

    def convert_run(self, api_data: Dict, repo: str = "") -> WorkflowRun:
        """
        Convert GitHub API run data to WorkflowRun domain model.

        Args:
            api_data: Raw API response dict
            repo: Repository name (for reference, optional)

        Returns:
            WorkflowRun instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Parse timestamps
        created_at_str = api_data.get("createdAt") or api_data.get("created_at")
        updated_at_str = api_data.get("updatedAt") or api_data.get("updated_at")

        if not created_at_str:
            raise ValueError("Missing createdAt field in API response")

        # Handle timezone-aware strings from GitHub API (with Z suffix)
        created_at = self._parse_github_timestamp(created_at_str)
        updated_at = self._parse_github_timestamp(updated_at_str) if updated_at_str else None

        # Calculate duration
        duration_seconds = 0.0
        if updated_at and created_at:
            duration_seconds = (updated_at - created_at).total_seconds()

        # Parse status and conclusion
        status_val = api_data.get("status")
        if not status_val:
            raise ValueError("Missing status field in API response")

        try:
            status = WorkflowStatus(status_val)
        except ValueError:
            raise ValueError(f"Invalid status value: {status_val}")

        conclusion_val = api_data.get("conclusion")
        conclusion = None
        if conclusion_val:
            try:
                conclusion = WorkflowConclusion(conclusion_val)
            except ValueError:
                logger.warning(f"Invalid conclusion value: {conclusion_val}")

        run = WorkflowRun(
            id=str(api_data.get("id", "")),
            workflow_name=api_data.get("name", ""),
            branch=api_data.get("headBranch") or api_data.get("head_branch", ""),
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=api_data.get("runNumber") or api_data.get("run_number"),
            commit_sha=api_data.get("headSha") or api_data.get("head_sha"),
            duration_seconds=duration_seconds,
        )
        return run

    def convert_attempt(self, api_data: Dict, run_id: str, repo: str = "") -> WorkflowRunAttempt:
        """
        Convert GitHub API attempt data to WorkflowRunAttempt domain model.

        Args:
            api_data: Raw API response dict
            run_id: The run ID this attempt belongs to
            repo: Repository name (for reference, optional)

        Returns:
            WorkflowRunAttempt instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Parse timestamps
        started_at_str = (
            api_data.get("startedAt")
            or api_data.get("created_at")
            or api_data.get("started_at")
        )
        completed_at_str = api_data.get("completedAt") or api_data.get("completed_at")

        if not started_at_str:
            raise ValueError("Missing startedAt field in API response")

        started_at = self._parse_github_timestamp(started_at_str)
        completed_at = self._parse_github_timestamp(completed_at_str) if completed_at_str else None

        # Calculate duration
        duration_seconds = 0.0
        if completed_at and started_at:
            duration_seconds = (completed_at - started_at).total_seconds()

        # Parse status and conclusion
        status_val = api_data.get("status")
        if not status_val:
            raise ValueError("Missing status field in API response")

        try:
            status = WorkflowStatus(status_val)
        except ValueError:
            raise ValueError(f"Invalid status value: {status_val}")

        conclusion_val = api_data.get("conclusion")
        conclusion = None
        if conclusion_val:
            try:
                conclusion = WorkflowConclusion(conclusion_val)
            except ValueError:
                logger.warning(f"Invalid conclusion value: {conclusion_val}")

        attempt = WorkflowRunAttempt(
            id=str(api_data.get("id", "")),
            run_id=run_id,
            attempt_number=api_data.get("attemptNumber") or api_data.get("attempt_number", 1),
            status=status,
            conclusion=conclusion,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            logs_url=api_data.get("logsUrl") or api_data.get("logs_url"),
        )
        return attempt

    def _parse_github_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse a GitHub API timestamp string to datetime.

        GitHub API returns ISO 8601 strings, often with Z suffix for UTC.

        Args:
            timestamp_str: Timestamp string from GitHub API

        Returns:
            datetime object in UTC timezone

        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Remove Z suffix if present (GitHub uses it for UTC)
        timestamp_str = timestamp_str.rstrip("Z")

        try:
            # Try parsing with fromisoformat
            dt = datetime.fromisoformat(timestamp_str)
            # Ensure it's UTC aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError as e:
            raise ValueError(f"Failed to parse timestamp '{timestamp_str}': {e}")
