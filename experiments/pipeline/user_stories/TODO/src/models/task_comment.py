from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TaskComment:
    """A comment attached to a task."""

    content: str
    task_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate comment fields."""
        if not self.content or not self.content.strip():
            raise ValueError("Comment content cannot be empty")

    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
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
        """Reconstruct from JSON-compatible dictionary."""
        updated_at_str = data.get("updated_at")
        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            author=data.get("author"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=updated_at,
        )
