from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from .task_status import TaskStatus

CEST = ZoneInfo("Europe/Paris")


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate due_date after initialization."""
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise ValueError(f"due_date must be a datetime object, got {type(self.due_date)}")
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.due_date is not None:
            result["due_date"] = self.due_date.isoformat()
            # Store the timezone key if it's a ZoneInfo for proper deserialization
            if isinstance(self.due_date.tzinfo, ZoneInfo):
                result["due_date_tz"] = self.due_date.tzinfo.key
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        due_date = None
        if "due_date" in data and data["due_date"] is not None:
            dt = datetime.fromisoformat(data["due_date"])
            # If we have the timezone key stored, use it to reconstruct the ZoneInfo
            if "due_date_tz" in data and data["due_date_tz"] is not None:
                tz = ZoneInfo(data["due_date_tz"])
                naive_dt = dt.replace(tzinfo=None)
                due_date = naive_dt.replace(tzinfo=tz)
            else:
                due_date = dt

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )
