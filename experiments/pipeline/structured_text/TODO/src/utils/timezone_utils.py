"""Timezone utilities for CEST (Central European Summer Time) handling."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now_in_cest() -> datetime:
    """Get the current time in CEST (Europe/Paris timezone).

    Returns:
        A timezone-aware datetime object in CEST (UTC+2 during summer, UTC+1 during winter).
    """
    return datetime.now(ZoneInfo("Europe/Paris"))


def is_overdue_cest(due_date: datetime) -> bool:
    """Check if a due date is in the past, using CEST for comparison.

    Args:
        due_date: The due date datetime (assumed to be UTC internally).

    Returns:
        True if due_date is in the past when compared to current CEST time, False otherwise.
    """
    current_cest = now_in_cest()
    # Convert due_date to CEST for comparison
    if due_date.tzinfo is None:
        # Naive datetime - assume UTC
        due_date_cest = due_date.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Paris"))
    else:
        # Already timezone-aware, convert to CEST
        due_date_cest = due_date.astimezone(ZoneInfo("Europe/Paris"))
    return current_cest > due_date_cest


def utc_to_cest(dt: datetime) -> datetime:
    """Convert a UTC datetime to CEST (Europe/Paris timezone).

    Args:
        dt: A UTC datetime (or timezone-aware datetime).

    Returns:
        The same instant in time, represented in CEST.
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        # Already timezone-aware
        dt_utc = dt
    return dt_utc.astimezone(ZoneInfo("Europe/Paris"))
