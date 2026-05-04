from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty or whitespace")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }
        if self.description is not None:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
