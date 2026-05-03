"""Tests for timezone conversion utilities."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.timezone_converter import (
    parse_datetime_with_timezone,
    datetime_to_utc,
    format_datetime_for_display,
)


class TestParseDatetimeWithTimezone:
    """Test parse_datetime_with_timezone function."""

    def test_parse_utc_iso8601_with_z_suffix(self):
        """Test parsing ISO 8601 datetime with Z (UTC) suffix."""
        result = parse_datetime_with_timezone("2026-05-03T10:30:00Z")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
        assert result.tzinfo == ZoneInfo("UTC")

    def test_parse_utc_iso8601_with_explicit_offset(self):
        """Test parsing ISO 8601 datetime with explicit UTC offset."""
        result = parse_datetime_with_timezone("2026-05-03T10:30:00+00:00")
        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 10

    def test_parse_naive_datetime_default_utc(self):
        """Test parsing naive datetime defaults to UTC."""
        result = parse_datetime_with_timezone("2026-05-03T10:30:00")
        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_naive_datetime_with_explicit_timezone(self):
        """Test parsing naive datetime with explicit timezone."""
        result = parse_datetime_with_timezone("2026-05-03T10:30:00", timezone_str="Europe/Paris")
        # Europe/Paris is CEST (UTC+2) in May
        assert result.tzinfo == ZoneInfo("UTC")
        # When 10:30 in CEST (UTC+2), UTC time is 08:30
        assert result.hour == 8
        assert result.minute == 30

    def test_parse_with_cest_timezone(self):
        """Test parsing with CEST timezone (Europe/Paris in summer)."""
        result = parse_datetime_with_timezone("2026-05-03T14:00:00", timezone_str="Europe/Paris")
        assert result.tzinfo == ZoneInfo("UTC")
        # 14:00 CEST (UTC+2) = 12:00 UTC
        assert result.hour == 12

    def test_parse_with_utc_plus_2_offset(self):
        """Test parsing ISO 8601 with UTC+2 offset."""
        result = parse_datetime_with_timezone("2026-05-03T14:00:00+02:00")
        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 12

    def test_parse_invalid_datetime_string_raises(self):
        """Test parsing invalid datetime string raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime_with_timezone("not-a-datetime")

    def test_parse_space_separator_accepted(self):
        """Test ISO format with space separator is accepted."""
        result = parse_datetime_with_timezone("2026-05-03 10:30:00")
        assert result.year == 2026
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_invalid_timezone_raises(self):
        """Test invalid timezone string raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime_with_timezone("2026-05-03T10:30:00", timezone_str="InvalidZone")

    def test_parse_empty_string_raises(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime_with_timezone("")

    def test_parse_date_only_accepted(self):
        """Test date-only string is accepted (time defaults to 00:00:00)."""
        result = parse_datetime_with_timezone("2026-05-03")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 0
        assert result.minute == 0


class TestDatetimeToUtc:
    """Test datetime_to_utc function."""

    def test_aware_datetime_utc(self):
        """Test timezone-aware datetime in UTC."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = datetime_to_utc(dt)
        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 10

    def test_aware_datetime_cest(self):
        """Test timezone-aware datetime in CEST (Europe/Paris)."""
        dt = datetime(2026, 5, 3, 14, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
        result = datetime_to_utc(dt)
        assert result.tzinfo == ZoneInfo("UTC")
        # 14:00 CEST (UTC+2) = 12:00 UTC
        assert result.hour == 12

    def test_aware_datetime_utc_plus_5(self):
        """Test timezone-aware datetime with UTC+5."""
        from datetime import timezone as tz_module
        dt = datetime(2026, 5, 3, 15, 0, 0, tzinfo=tz_module.utc).replace(
            tzinfo=ZoneInfo("Asia/Karachi")  # UTC+5
        )
        result = datetime_to_utc(dt)
        assert result.tzinfo == ZoneInfo("UTC")

    def test_naive_datetime_assumed_utc(self):
        """Test naive datetime is assumed to be UTC."""
        dt = datetime(2026, 5, 3, 10, 30, 0)
        result = datetime_to_utc(dt)
        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 10

    def test_naive_datetime_preserves_time(self):
        """Test naive datetime values are preserved (assumed UTC)."""
        dt = datetime(2026, 5, 3, 15, 45, 30)
        result = datetime_to_utc(dt)
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 15
        assert result.minute == 45
        assert result.second == 30

    def test_none_datetime_raises(self):
        """Test None datetime raises ValueError."""
        with pytest.raises(ValueError, match="datetime cannot be None"):
            datetime_to_utc(None)


class TestFormatDatetimeForDisplay:
    """Test format_datetime_for_display function."""

    def test_format_utc_to_utc(self):
        """Test formatting UTC datetime to UTC display."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_display(dt)
        assert "2026-05-03" in result
        assert "10:30:00" in result

    def test_format_utc_to_cest(self):
        """Test formatting UTC datetime to CEST display."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_display(dt, timezone_str="Europe/Paris")
        # 10:30 UTC = 12:30 CEST (UTC+2)
        assert "12:30:00" in result

    def test_format_naive_to_cest(self):
        """Test formatting naive datetime to CEST display."""
        dt = datetime(2026, 5, 3, 10, 30, 0)  # Assumed UTC
        result = format_datetime_for_display(dt, timezone_str="Europe/Paris")
        assert "12:30:00" in result

    def test_format_aware_datetime_to_different_tz(self):
        """Test formatting aware datetime in different timezone."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("Europe/Paris"))
        result = format_datetime_for_display(dt, timezone_str="UTC")
        # 10:30 CEST (UTC+2) = 08:30 UTC
        assert "08:30:00" in result

    def test_format_returns_iso_format(self):
        """Test result is ISO 8601 formatted."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_display(dt)
        assert "T" in result  # ISO 8601 separator
        assert "+" in result or "Z" in result or result.endswith("+00:00")

    def test_format_invalid_timezone_raises(self):
        """Test invalid timezone string raises ValueError."""
        dt = datetime(2026, 5, 3, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        with pytest.raises(ValueError):
            format_datetime_for_display(dt, timezone_str="InvalidZone")

    def test_format_none_datetime_raises(self):
        """Test None datetime raises ValueError."""
        with pytest.raises(ValueError):
            format_datetime_for_display(None)

    def test_format_preserves_all_components(self):
        """Test formatting preserves all datetime components."""
        dt = datetime(2026, 5, 3, 14, 35, 45, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_display(dt)
        assert "2026-05-03" in result
        assert "14:35:45" in result
