from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TaskComment:
    """A comment on a task.

    Attributes:
        task_id: Foreign key reference to the Task this comment belongs to
        content: The comment text (required, non-empty)
        id: Unique identifier (auto-generated UUID as string)
        author: Optional author name
        created_at: Datetime when comment was created (UTC)
        updated_at: Optional datetime when comment was last modified (UTC)
    """
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert comment to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields; optional fields with None value are omitted.
        """
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        """Create a comment from a dictionary (JSON deserialization).

        Required fields: id, task_id, content, created_at
        Optional fields: author, updated_at (defaults to None if missing)

        Args:
            data: Dictionary with comment data

        Returns:
            TaskComment instance

        Raises:
            KeyError: If required fields are missing
        """
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
