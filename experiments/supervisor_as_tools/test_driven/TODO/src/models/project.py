from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Project:
    """Represents a project that can contain multiple tasks.

    Attributes:
        name: The project name (required, non-empty).
        id: Unique identifier for the project (auto-generated UUID).
    """
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate that name is not empty or whitespace-only.

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")

    def to_dict(self) -> dict:
        """Convert Project to dictionary representation.

        Returns:
            Dictionary with keys: id, name
        """
        return {
            "id": self.id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        """Create a Project instance from dictionary data.

        Args:
            data: Dictionary with keys: id, name

        Returns:
            A new Project instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
        )
