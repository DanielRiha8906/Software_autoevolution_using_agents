from datetime import datetime, timezone, timedelta

CEST = timezone(timedelta(hours=2))


class DatetimeService:
    """Service providing centralized datetime utilities."""

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC time.

        Returns:
            Current datetime in UTC timezone
        """
        return datetime.now(timezone.utc)
