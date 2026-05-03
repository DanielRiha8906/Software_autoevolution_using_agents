from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

CEST = ZoneInfo("Europe/Paris")


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(CEST))
    updated_at: Optional[datetime] = None
    author: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate content after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty or whitespace-only")
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at.isoformat()
        if self.author is not None:
            result["author"] = self.author
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
            updated_at=updated_at,
            author=data.get("author"),
        )
