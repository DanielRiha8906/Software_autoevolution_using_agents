from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TaskComment:
    """A comment attached to a task.

    Attributes:
        id: Unique identifier (UUID), auto-generated
        task_id: ID of the task this comment belongs to
        content: The text content of the comment
        created_at: Timestamp when comment was created (UTC)
        author: Optional name or identifier of the comment author
        updated_at: Optional timestamp when comment was last updated (UTC)
    """

    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        """Create TaskComment from dictionary (e.g., loaded from JSON).

        Handles missing optional fields gracefully.
        """
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
