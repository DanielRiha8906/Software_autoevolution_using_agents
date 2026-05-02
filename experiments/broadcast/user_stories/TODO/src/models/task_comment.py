from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

# CEST is UTC+2
CEST = timezone(timedelta(hours=2))


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(CEST))
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate TaskComment fields after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
        if not self.task_id or not self.task_id.strip():
            raise ValueError("task_id cannot be empty")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        created_at_str = data.get("created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(CEST)

        updated_at_str = data.get("updated_at")
        updated_at = None
        if updated_at_str is not None:
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid updated_at format: {e}")

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            author=data.get("author"),
            created_at=created_at,
            updated_at=updated_at,
        )
