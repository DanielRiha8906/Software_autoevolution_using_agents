from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Project:
    """Domain class representing a project that can contain tasks."""

    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate project after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        created_at = None
        if "created_at" in data and data["created_at"] is not None:
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            created_at=created_at or datetime.now(timezone.utc),
        )
