from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion
from .workflow_run_attempt import WorkflowRunAttempt
from .validation_error import ValidationError


@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float = 0.0
    attempts: list[WorkflowRunAttempt] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError(f"duration_seconds cannot be negative, got {self.duration_seconds}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "branch": self.branch,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_number": self.run_number,
            "commit_sha": self.commit_sha,
            "duration_seconds": self.duration_seconds,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }

    @classmethod
    def validate_dict(cls, data: dict) -> None:
        """Validate a dictionary for WorkflowRun creation.

        Args:
            data: Dictionary to validate

        Raises:
            ValidationError: If any validation fails
        """
        errors = []

        # Check required fields
        required_fields = ["id", "workflow_name", "branch", "status", "created_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if errors:
            raise ValidationError(errors)

        # Validate status enum
        try:
            WorkflowStatus(data["status"])
        except ValueError:
            errors.append(f"Invalid status: {data['status']}")

        # Validate conclusion enum if present
        if data.get("conclusion") is not None:
            try:
                WorkflowConclusion(data["conclusion"])
            except ValueError:
                errors.append(f"Invalid conclusion: {data['conclusion']}")

        # Validate datetime fields
        try:
            datetime.fromisoformat(data["created_at"])
        except (ValueError, TypeError):
            errors.append(f"created_at must be valid ISO 8601, got {data['created_at']}")

        if data.get("updated_at") is not None:
            try:
                datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                errors.append(f"updated_at must be valid ISO 8601, got {data['updated_at']}")

        # Validate duration_seconds is non-negative
        if "duration_seconds" in data:
            try:
                duration = float(data["duration_seconds"])
                if duration < 0:
                    errors.append(f"duration_seconds cannot be negative, got {duration}")
            except (TypeError, ValueError):
                errors.append(f"duration_seconds must be a number, got {type(data['duration_seconds']).__name__}")

        # Validate run_number is int if present
        if data.get("run_number") is not None:
            if not isinstance(data["run_number"], int):
                errors.append(f"run_number must be int, got {type(data['run_number']).__name__}")

        # Validate commit_sha is string if present
        if data.get("commit_sha") is not None:
            if not isinstance(data["commit_sha"], str):
                errors.append(f"commit_sha must be string, got {type(data['commit_sha']).__name__}")

        # Validate attempts array items
        if "attempts" in data:
            attempts_data = data.get("attempts", [])
            if not isinstance(attempts_data, list):
                errors.append(f"attempts must be array, got {type(attempts_data).__name__}")
            else:
                for idx, attempt_data in enumerate(attempts_data):
                    try:
                        WorkflowRunAttempt.validate_dict(attempt_data)
                    except ValidationError as e:
                        for msg in e.messages:
                            errors.append(f"attempts[{idx}]: {msg}")

        if errors:
            raise ValidationError(errors)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        attempts_data = data.get("attempts", [])
        attempts = [WorkflowRunAttempt.from_dict(attempt_data) for attempt_data in attempts_data]
        return cls(
            id=data["id"],
            workflow_name=data["workflow_name"],
            branch=data["branch"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_number=data.get("run_number"),
            commit_sha=data.get("commit_sha"),
            duration_seconds=data.get("duration_seconds", 0.0),
            attempts=attempts,
        )

    def is_terminal(self) -> bool:
        """Run has completed (regardless of success/failure)."""
        return self.status == WorkflowStatus.COMPLETED

    def is_running(self) -> bool:
        """Run is actively executing."""
        return self.status == WorkflowStatus.IN_PROGRESS

    def is_successful(self) -> bool:
        """Run completed with success conclusion."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion == WorkflowConclusion.SUCCESS)

    def is_failed(self) -> bool:
        """Run completed with failure conclusion."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion == WorkflowConclusion.FAILURE)

    def is_cancelled(self) -> bool:
        """Run completed with cancelled conclusion (bonus)."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion == WorkflowConclusion.CANCELLED)
