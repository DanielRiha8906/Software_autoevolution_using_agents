from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

CEST = timezone(timedelta(hours=2))


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(CEST))
    updated_at: Optional[datetime] = None
    author: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.content, str) or not self.content.strip():
            raise Exception("Content cannot be empty")
        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                raise ValueError("updated_at must be a datetime object")
            if self.updated_at.tzinfo is None:
                raise ValueError("updated_at must have timezone information (not naive)")
            if self.updated_at.tzinfo != CEST:
                raise ValueError(f"updated_at must be in CEST timezone, got {self.updated_at.tzinfo}")

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
            updated_at=updated_at,
            author=data.get("author"),
        )
