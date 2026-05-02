from datetime import datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo


def to_cest(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to CEST timezone (UTC+2).

    Args:
        dt: A datetime object (naive or aware) or None

    Returns:
        Datetime with CEST timezone, or None if input is None
    """
    if dt is None:
        return None

    cest = ZoneInfo("Europe/Paris")
    if dt.tzinfo is None:
        # Naive datetime: assume it's already in CEST and add tzinfo
        return dt.replace(tzinfo=cest)
    else:
        # Aware datetime: convert to CEST
        return dt.astimezone(cest)


def parse_datetime_or_iso_string(value: Union[datetime, str, None]) -> Optional[datetime]:
    """Parse datetime object or ISO string to CEST datetime.

    Args:
        value: A datetime object, ISO 8601 string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+02:00),
               short date string (YYYY-MM-DD), None, or empty string

    Returns:
        Datetime with CEST timezone, or None if value is None or empty

    Raises:
        ValueError: If parsing fails
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return to_cest(value)

    if not isinstance(value, str):
        raise ValueError(f"Expected datetime, str, or None, got {type(value).__name__}")

    value = value.strip()
    if not value:
        return None

    try:
        # Try to parse as ISO 8601 string
        dt = datetime.fromisoformat(value)
        return to_cest(dt)
    except ValueError:
        pass

    try:
        # Try to parse as short date string (YYYY-MM-DD)
        dt = datetime.strptime(value, "%Y-%m-%d")
        return to_cest(dt)
    except ValueError:
        pass

    raise ValueError(
        f"Could not parse '{value}'. "
        "Expected ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+02:00) "
        "or short date format (YYYY-MM-DD)"
    )
