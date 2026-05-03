"""Timezone conversion utilities for workflow timestamps."""

from datetime import datetime
from zoneinfo import ZoneInfo


def parse_datetime_with_timezone(dt_string: str, timezone_str: str = "UTC") -> datetime:
    """
    Parse a datetime string with explicit timezone support.

    Args:
        dt_string: ISO 8601 datetime string (with or without timezone info).
        timezone_str: Timezone name (e.g., "UTC", "Europe/Paris" for CEST).
                      Defaults to "UTC".

    Returns:
        datetime object in UTC timezone.

    Raises:
        ValueError: If the datetime string is invalid or timezone is not recognized.
    """
    try:
        # Parse the datetime string
        if "T" in dt_string and ("+" in dt_string or dt_string.endswith("Z")):
            # ISO 8601 with timezone info already present
            dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        else:
            # Naive datetime string - assume it's in the specified timezone
            dt = datetime.fromisoformat(dt_string)

        # If timezone is already aware (has tzinfo), convert to UTC
        if dt.tzinfo is not None:
            return dt.astimezone(ZoneInfo("UTC"))

        # If naive, assume it's in the specified timezone and convert to UTC
        tz = ZoneInfo(timezone_str)
        dt_aware = dt.replace(tzinfo=tz)
        return dt_aware.astimezone(ZoneInfo("UTC"))

    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Invalid datetime '{dt_string}' or timezone '{timezone_str}': {e}"
        ) from e


def datetime_to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC timezone.

    Args:
        dt: datetime object (can be naive or timezone-aware).

    Returns:
        datetime object in UTC timezone.

    Raises:
        ValueError: If dt is None or invalid.
    """
    if dt is None:
        raise ValueError("datetime cannot be None")

    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=ZoneInfo("UTC"))

    # Convert to UTC if it has timezone info
    return dt.astimezone(ZoneInfo("UTC"))


def format_datetime_for_display(dt: datetime, timezone_str: str = "UTC") -> str:
    """
    Format a datetime for display in a specified timezone.

    Args:
        dt: datetime object (can be naive or timezone-aware).
        timezone_str: Target timezone for display (e.g., "UTC", "Europe/Paris").
                      Defaults to "UTC".

    Returns:
        ISO 8601 formatted datetime string in the specified timezone.

    Raises:
        ValueError: If timezone is not recognized.
    """
    try:
        # Ensure we have UTC datetime
        utc_dt = datetime_to_utc(dt)

        # Convert to target timezone
        target_tz = ZoneInfo(timezone_str)
        display_dt = utc_dt.astimezone(target_tz)

        return display_dt.isoformat()

    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid timezone '{timezone_str}': {e}") from e
