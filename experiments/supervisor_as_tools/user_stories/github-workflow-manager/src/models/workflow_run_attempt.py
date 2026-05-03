from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .workflow_attempt_status import WorkflowAttemptStatus
from .workflow_attempt_conclusion import WorkflowAttemptConclusion
from .validation_error import ValidationError


@dataclass
class WorkflowRunAttempt:
    id: int
    run_id: int
    attempt_number: int
    status: WorkflowAttemptStatus
    conclusion: Optional[WorkflowAttemptConclusion]
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.attempt_number < 1:
            raise ValueError(f"attempt_number must be >= 1, got {self.attempt_number}")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError(f"duration_seconds cannot be negative, got {self.duration_seconds}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def validate_dict(cls, data: dict) -> None:
        """Validate a dictionary for WorkflowRunAttempt creation.

        Args:
            data: Dictionary to validate

        Raises:
            ValidationError: If any validation fails
        """
        errors = []

        # Check required fields
        required_fields = ["id", "run_id", "attempt_number", "status", "created_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if errors:
            raise ValidationError(errors)

        # Validate status enum
        try:
            WorkflowAttemptStatus(data["status"])
        except ValueError:
            errors.append(f"Invalid status: {data['status']}")

        # Validate conclusion enum if present
        if data.get("conclusion") is not None:
            try:
                WorkflowAttemptConclusion(data["conclusion"])
            except ValueError:
                errors.append(f"Invalid conclusion: {data['conclusion']}")

        # Validate attempt_number is int
        if not isinstance(data["attempt_number"], int):
            errors.append(f"attempt_number must be int, got {type(data['attempt_number']).__name__}")

        # Validate duration_seconds is non-negative if present
        if data.get("duration_seconds") is not None:
            try:
                duration = float(data["duration_seconds"])
                if duration < 0:
                    errors.append(f"duration_seconds cannot be negative, got {duration}")
            except (TypeError, ValueError):
                errors.append(f"duration_seconds must be a number, got {type(data.get('duration_seconds')).__name__}")

        # Validate created_at is valid ISO 8601
        try:
            datetime.fromisoformat(data["created_at"])
        except (ValueError, TypeError):
            errors.append(f"created_at must be valid ISO 8601, got {data['created_at']}")

        if errors:
            raise ValidationError(errors)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=WorkflowAttemptStatus(data["status"]),
            conclusion=WorkflowAttemptConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds"),
        )
