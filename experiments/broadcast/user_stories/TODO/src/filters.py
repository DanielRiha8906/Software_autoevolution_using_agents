"""Composable filter builder for tasks."""

from datetime import datetime, timezone
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from .models.task import Task, CEST
from .models.task_status import TaskStatus

FilterPredicate = Callable[[Task], bool]


class FilterBuilder:
    """Builder for composable task filters using method chaining."""

    def __init__(self) -> None:
        self._predicates: list[FilterPredicate] = []

    def status(self, status: TaskStatus) -> "FilterBuilder":
        """Filter by task status."""
        self._predicates.append(lambda t: t.status == status)
        return self

    def due_before(self, dt: datetime) -> "FilterBuilder":
        """Filter tasks due before a given datetime."""
        if dt.tzinfo is None:
            raise ValueError("due_before requires a timezone-aware datetime")
        dt_cest = dt.astimezone(CEST)

        def pred(t: Task) -> bool:
            if t.due_date is None:
                return False
            due_cest = t.due_date.astimezone(CEST)
            return due_cest < dt_cest

        self._predicates.append(pred)
        return self

    def due_after(self, dt: datetime) -> "FilterBuilder":
        """Filter tasks due after a given datetime."""
        if dt.tzinfo is None:
            raise ValueError("due_after requires a timezone-aware datetime")
        dt_cest = dt.astimezone(CEST)

        def pred(t: Task) -> bool:
            if t.due_date is None:
                return False
            due_cest = t.due_date.astimezone(CEST)
            return due_cest > dt_cest

        self._predicates.append(pred)
        return self

    def due_on_or_before(self, dt: datetime) -> "FilterBuilder":
        """Filter tasks due on or before a given datetime."""
        if dt.tzinfo is None:
            raise ValueError("due_on_or_before requires a timezone-aware datetime")
        dt_cest = dt.astimezone(CEST)

        def pred(t: Task) -> bool:
            if t.due_date is None:
                return False
            due_cest = t.due_date.astimezone(CEST)
            return due_cest <= dt_cest

        self._predicates.append(pred)
        return self

    def due_on_or_after(self, dt: datetime) -> "FilterBuilder":
        """Filter tasks due on or after a given datetime."""
        if dt.tzinfo is None:
            raise ValueError("due_on_or_after requires a timezone-aware datetime")
        dt_cest = dt.astimezone(CEST)

        def pred(t: Task) -> bool:
            if t.due_date is None:
                return False
            due_cest = t.due_date.astimezone(CEST)
            return due_cest >= dt_cest

        self._predicates.append(pred)
        return self

    def overdue(self, include_overdue: bool = True) -> "FilterBuilder":
        """Filter by overdue status.

        Args:
            include_overdue: If True, returns only overdue tasks.
                           If False, returns only non-overdue tasks.
        """

        def pred(t: Task) -> bool:
            is_overdue = t.is_overdue()
            return is_overdue if include_overdue else not is_overdue

        self._predicates.append(pred)
        return self

    def apply(self, tasks: list[Task]) -> list[Task]:
        """Apply all filters to a task list."""
        result = tasks
        for predicate in self._predicates:
            result = [t for t in result if predicate(t)]
        return result


def parse_date_string(date_str: str) -> datetime:
    """Parse a flexible date string into a timezone-aware datetime.

    Supports formats:
    - YYYY-MM-DD (assumes 00:00 CEST)
    - YYYY-MM-DD HH:MM:SS (assumes CEST)
    - YYYY-MM-DDTHH:MM:SS (ISO format with CEST if no tzinfo)
    - ISO format with timezone

    Args:
        date_str: Date string to parse

    Returns:
        Timezone-aware datetime in CEST

    Raises:
        ValueError: If format is not recognized
    """
    try:
        # Try ISO format first
        dt = datetime.fromisoformat(date_str)
        # If naive, assume CEST
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CEST)
        return dt
    except ValueError:
        pass

    # Try YYYY-MM-DD format
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.replace(tzinfo=CEST)
    except ValueError:
        pass

    # Try YYYY-MM-DD HH:MM:SS format
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=CEST)
    except ValueError:
        pass

    raise ValueError(
        f"Could not parse date: '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format."
    )
