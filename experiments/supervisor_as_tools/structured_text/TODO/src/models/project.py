from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        self.name = self.name.strip()

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(name=data["name"], id=data["id"])
