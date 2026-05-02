from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        # Validate content is non-empty
        if self.content is None or not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Comment content cannot be empty")

        # Validate created_at has timezone
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        author = data.get("author")
        updated_at_str = data.get("updated_at")
        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            author=author,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=updated_at,
        )
