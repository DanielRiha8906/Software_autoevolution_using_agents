from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


@dataclass
class TaskComment:
    task_id: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone(timedelta(hours=2))))

    def to_dict(self) -> dict:
        """Serialize TaskComment to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:
        """Deserialize TaskComment from dictionary with validation."""
        # Validate required fields
        if "id" not in data:
            raise ValueError("Missing required field: id")
        if "task_id" not in data:
            raise ValueError("Missing required field: task_id")
        if "content" not in data:
            raise ValueError("Missing required field: content")
        if "created_at" not in data:
            raise ValueError("Missing required field: created_at")

        # Validate content is not empty
        if not data["content"] or not data["content"].strip():
            raise ValueError("Content cannot be empty")

        # Parse created_at datetime
        try:
            created_at = datetime.fromisoformat(data["created_at"])
        except ValueError:
            raise ValueError(f"Invalid created_at format: {data['created_at']}")

        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            created_at=created_at,
        )
