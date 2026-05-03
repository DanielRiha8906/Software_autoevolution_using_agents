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
    author: Optional[str] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.content or self.content.strip() == "":
            raise ValueError("content cannot be empty")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
        }
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        updated_at_str = data.get("updated_at")
        updated_at = None
        if updated_at_str is not None:
            updated_at = datetime.fromisoformat(updated_at_str)

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            author=data.get("author"),
            updated_at=updated_at,
        )
