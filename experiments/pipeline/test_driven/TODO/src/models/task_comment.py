from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


# CEST: Central European Summer Time (UTC+2)
CEST = timezone(timedelta(hours=2))


def _validate_comment_datetime_timezone(dt: datetime) -> None:
    """Validate that a datetime is timezone-aware and uses CEST."""
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (got naive datetime)")
    if dt.tzinfo != CEST:
        raise ValueError(f"datetime must use CEST (UTC+2); got {dt.tzinfo}")


@dataclass
class TaskComment:
    """A comment on a task."""
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(CEST))
    author: Optional[str] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.task_id or not isinstance(self.task_id, str):
            raise ValueError("task_id must be a non-empty string")
        if not self.content or not isinstance(self.content, str):
            raise ValueError("content must be a non-empty string")

        # Validate created_at is timezone-aware and uses CEST
        _validate_comment_datetime_timezone(self.created_at)

        # Validate updated_at if present
        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                raise TypeError(f"updated_at must be a datetime object, got {type(self.updated_at).__name__}")
            _validate_comment_datetime_timezone(self.updated_at)

    def to_dict(self) -> dict:
        """Serialize to dictionary with ISO 8601 datetime strings."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        """Deserialize from dictionary with ISO 8601 datetime strings."""
        # Parse created_at and validate timezone
        created_at = datetime.fromisoformat(data["created_at"])
        _validate_comment_datetime_timezone(created_at)

        # Parse updated_at if present and validate timezone
        updated_at_str = data.get("updated_at")
        updated_at = None
        if updated_at_str is not None:
            updated_at = datetime.fromisoformat(updated_at_str)
            _validate_comment_datetime_timezone(updated_at)

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            created_at=created_at,
            author=data.get("author"),
            updated_at=updated_at,
        )
