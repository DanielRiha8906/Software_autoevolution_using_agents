from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

# CEST timezone (UTC+2)
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
        """Validate content and timezone-aware datetimes."""
        if not self.content or not self.content.strip():
            raise ValueError("content must be non-empty")

        if not isinstance(self.created_at, datetime):
            raise TypeError(f"created_at must be a datetime object, got {type(self.created_at)}")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.created_at.tzinfo != CEST:
            raise ValueError(f"created_at must use CEST timezone (UTC+2), got {self.created_at.tzinfo}")

        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                raise TypeError(f"updated_at must be a datetime object, got {type(self.updated_at)}")
            if self.updated_at.tzinfo is None:
                raise ValueError("updated_at must be timezone-aware")
            if self.updated_at.tzinfo != CEST:
                raise ValueError(f"updated_at must use CEST timezone (UTC+2), got {self.updated_at.tzinfo}")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }
        if self.author is not None:
            result["author"] = self.author
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        updated_at = None
        if "updated_at" in data and data["updated_at"] is not None:
            updated_at = datetime.fromisoformat(data["updated_at"])
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            author=data.get("author"),
            updated_at=updated_at,
        )
