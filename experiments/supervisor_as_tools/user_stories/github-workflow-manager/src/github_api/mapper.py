"""Mapper for converting GitHub API responses to domain models."""

from datetime import datetime
from typing import Optional, List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_attempt_status import WorkflowAttemptStatus
from ..models.workflow_attempt_conclusion import WorkflowAttemptConclusion


class GitHubRunMapper:
    """Map GitHub API response objects to domain models."""

    @staticmethod
    def map_run(github_run: dict, workflow_name: str) -> WorkflowRun:
        """Convert GitHub API workflow run to WorkflowRun domain model.

        Args:
            github_run: Workflow run dict from GitHub API
            workflow_name: Name of the workflow

        Returns:
            WorkflowRun domain model

        Raises:
            ValueError: If required fields are missing or invalid
        """
        run_id = str(github_run.get("id", ""))
        if not run_id:
            raise ValueError("Missing 'id' field in GitHub run response")

        status_str = github_run.get("status", "").lower()
        status = GitHubRunMapper._map_status(status_str)

        conclusion_str = github_run.get("conclusion")
        conclusion = GitHubRunMapper._map_conclusion(conclusion_str) if conclusion_str else None

        created_at_str = github_run.get("created_at")
        if not created_at_str:
            raise ValueError("Missing 'created_at' field in GitHub run response")

        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

        updated_at_str = github_run.get("updated_at")
        updated_at = (
            datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            if updated_at_str
            else None
        )

        # Extract branch from head_branch
        branch = github_run.get("head_branch", "")

        # Extract run number
        run_number = github_run.get("run_number")

        # Extract commit SHA
        commit_sha = github_run.get("head_sha")

        # Calculate duration in seconds if timing info is available
        duration_seconds = GitHubRunMapper._calculate_duration(github_run)

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
            attempts=[],
        )

    @staticmethod
    def map_attempt(github_attempt: dict, run_id: str) -> WorkflowRunAttempt:
        """Convert GitHub API attempt to WorkflowRunAttempt domain model.

        Args:
            github_attempt: Attempt dict from GitHub API
            run_id: The workflow run ID this attempt belongs to

        Returns:
            WorkflowRunAttempt domain model

        Raises:
            ValueError: If required fields are missing or invalid
        """
        attempt_id = github_attempt.get("id")
        if attempt_id is None:
            raise ValueError("Missing 'id' field in GitHub attempt response")

        attempt_number = github_attempt.get("attempt_number")
        if attempt_number is None:
            raise ValueError("Missing 'attempt_number' field in GitHub attempt response")

        status_str = github_attempt.get("status", "").lower()
        status = GitHubRunMapper._map_attempt_status(status_str)

        conclusion_str = github_attempt.get("conclusion")
        conclusion = (
            GitHubRunMapper._map_attempt_conclusion(conclusion_str)
            if conclusion_str
            else None
        )

        created_at_str = github_attempt.get("created_at")
        if not created_at_str:
            raise ValueError("Missing 'created_at' field in GitHub attempt response")

        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

        # Calculate duration
        duration_seconds = GitHubRunMapper._calculate_attempt_duration(github_attempt)

        return WorkflowRunAttempt(
            id=int(attempt_id),
            run_id=int(run_id),
            attempt_number=int(attempt_number),
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _map_status(github_status: str) -> WorkflowStatus:
        """Map GitHub status string to WorkflowStatus enum.

        Args:
            github_status: Status from GitHub API (queued, in_progress, completed, etc.)

        Returns:
            WorkflowStatus enum value

        Raises:
            ValueError: If status cannot be mapped
        """
        mapping = {
            "queued": WorkflowStatus.QUEUED,
            "in_progress": WorkflowStatus.IN_PROGRESS,
            "completed": WorkflowStatus.COMPLETED,
            "waiting": WorkflowStatus.WAITING,
            "requested": WorkflowStatus.REQUESTED,
            "pending": WorkflowStatus.PENDING,
        }

        if github_status in mapping:
            return mapping[github_status]

        # Default to the closest match or raise error
        raise ValueError(f"Unknown workflow status from GitHub: {github_status}")

    @staticmethod
    def _map_conclusion(github_conclusion: str) -> Optional[WorkflowConclusion]:
        """Map GitHub conclusion string to WorkflowConclusion enum.

        Args:
            github_conclusion: Conclusion from GitHub API

        Returns:
            WorkflowConclusion enum value or None if unknown

        Raises:
            ValueError: If conclusion cannot be mapped
        """
        mapping = {
            "success": WorkflowConclusion.SUCCESS,
            "failure": WorkflowConclusion.FAILURE,
            "cancelled": WorkflowConclusion.CANCELLED,
        }

        if github_conclusion in mapping:
            return mapping[github_conclusion]

        raise ValueError(f"Unknown workflow conclusion from GitHub: {github_conclusion}")

    @staticmethod
    def _map_attempt_status(github_status: str) -> WorkflowAttemptStatus:
        """Map GitHub attempt status string to WorkflowAttemptStatus enum.

        Args:
            github_status: Status from GitHub API

        Returns:
            WorkflowAttemptStatus enum value

        Raises:
            ValueError: If status cannot be mapped
        """
        mapping = {
            "queued": WorkflowAttemptStatus.QUEUED,
            "in_progress": WorkflowAttemptStatus.IN_PROGRESS,
            "completed": WorkflowAttemptStatus.COMPLETED,
        }

        if github_status in mapping:
            return mapping[github_status]

        raise ValueError(f"Unknown attempt status from GitHub: {github_status}")

    @staticmethod
    def _map_attempt_conclusion(github_conclusion: str) -> Optional[WorkflowAttemptConclusion]:
        """Map GitHub attempt conclusion string to WorkflowAttemptConclusion enum.

        Args:
            github_conclusion: Conclusion from GitHub API

        Returns:
            WorkflowAttemptConclusion enum value or None

        Raises:
            ValueError: If conclusion cannot be mapped
        """
        mapping = {
            "success": WorkflowAttemptConclusion.SUCCESS,
            "failure": WorkflowAttemptConclusion.FAILURE,
            "cancelled": WorkflowAttemptConclusion.CANCELLED,
            "skipped": WorkflowAttemptConclusion.SKIPPED,
            "timed_out": WorkflowAttemptConclusion.TIMED_OUT,
            "action_required": WorkflowAttemptConclusion.ACTION_REQUIRED,
            "neutral": WorkflowAttemptConclusion.NEUTRAL,
            "stale": WorkflowAttemptConclusion.STALE,
        }

        if github_conclusion in mapping:
            return mapping[github_conclusion]

        raise ValueError(f"Unknown attempt conclusion from GitHub: {github_conclusion}")

    @staticmethod
    def _calculate_duration(github_run: dict) -> float:
        """Calculate duration in seconds from GitHub run data.

        Args:
            github_run: Workflow run dict from GitHub API

        Returns:
            Duration in seconds or 0.0 if cannot be calculated
        """
        try:
            run_durationms = github_run.get("run_durationms")
            if run_durationms is not None:
                return float(run_durationms) / 1000.0
        except (TypeError, ValueError):
            pass

        return 0.0

    @staticmethod
    def _calculate_attempt_duration(github_attempt: dict) -> Optional[float]:
        """Calculate duration in seconds from GitHub attempt data.

        Args:
            github_attempt: Attempt dict from GitHub API

        Returns:
            Duration in seconds or None if cannot be calculated
        """
        try:
            # GitHub API may provide various duration fields
            # Check for common ones
            if "run_duration_ms" in github_attempt:
                return float(github_attempt["run_duration_ms"]) / 1000.0
            elif "duration_ms" in github_attempt:
                return float(github_attempt["duration_ms"]) / 1000.0
        except (TypeError, ValueError):
            pass

        return None
