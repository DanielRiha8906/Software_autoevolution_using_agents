from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate that name is not empty."""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        self.name = self.name.strip()

    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        """Reconstruct from JSON-compatible dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
        )
