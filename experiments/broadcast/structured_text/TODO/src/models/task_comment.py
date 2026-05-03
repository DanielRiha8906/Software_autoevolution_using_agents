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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate that content and task_id are not empty."""
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
        if not self.task_id or not self.task_id.strip():
            raise ValueError("task_id cannot be empty")

    def to_dict(self) -> dict:
        """Serialize TaskComment to a dictionary."""
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
        """Deserialize TaskComment from a dictionary."""
        updated_at_str = data.get("updated_at")
        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            author=data.get("author"),
            updated_at=updated_at,
        )
