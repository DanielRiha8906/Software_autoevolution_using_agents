from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task import _validate_timezone_aware_datetime


CEST = timezone(timedelta(hours=2))


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(CEST))
    author: Optional[str] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Content must not be empty")
        if self.updated_at is not None:
            _validate_timezone_aware_datetime(self.updated_at)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        created_at = datetime.fromisoformat(data["created_at"])
        _validate_timezone_aware_datetime(created_at)

        updated_at = None
        if data.get("updated_at") is not None:
            updated_at = datetime.fromisoformat(data["updated_at"])
            _validate_timezone_aware_datetime(updated_at)

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            author=data.get("author"),
            created_at=created_at,
            updated_at=updated_at,
        )
