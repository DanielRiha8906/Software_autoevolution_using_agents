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
    updated_at: datetime = field(default_factory=lambda: datetime.now(CEST))

    def __post_init__(self) -> None:
        """Validate that content is not empty."""
        if not self.content or not self.content.strip():
            raise ValueError("Comment content cannot be empty")

    def to_dict(self) -> dict:
        """Serialize TaskComment to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        """Deserialize TaskComment from dictionary."""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            author=data.get("author"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
