"""Date and datetime formatting utilities for GUI display."""

from datetime import datetime, timezone, timedelta


def format_date(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD for display.

    Args:
        dt: datetime object (UTC or timezone-aware)

    Returns:
        String in YYYY-MM-DD format
    """
    return dt.strftime("%Y-%m-%d")


def format_datetime(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD HH:MM for display.

    Args:
        dt: datetime object (UTC or timezone-aware)

    Returns:
        String in YYYY-MM-DD HH:MM format
    """
    return dt.strftime("%Y-%m-%d %H:%M")


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time (e.g., "2 days ago").

    Args:
        dt: datetime object (UTC or timezone-aware)

    Returns:
        String describing time relative to now
    """
    now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}h ago"
    elif diff.total_seconds() < 604800:
        days = int(diff.total_seconds() // 86400)
        return f"{days}d ago"
    else:
        return format_date(dt)
