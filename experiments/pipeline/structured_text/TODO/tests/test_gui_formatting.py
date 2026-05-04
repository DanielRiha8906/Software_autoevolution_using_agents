"""Tests for GUI formatting utilities."""

import pytest
from datetime import datetime, timezone, timedelta
from src.gui.utils.formatting import format_date, format_datetime, format_relative_time


class TestFormatDate:
    """Tests for format_date() function."""

    def test_format_date_basic(self):
        """Test basic date formatting."""
        dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "2025-01-15"

    def test_format_date_year(self):
        """Test formatting different years."""
        dt = datetime(2020, 5, 1, tzinfo=timezone.utc)
        assert format_date(dt) == "2020-05-01"

    def test_format_date_month_boundaries(self):
        """Test edge month values."""
        dt_first = datetime(2025, 1, 1, tzinfo=timezone.utc)
        dt_last = datetime(2025, 12, 31, tzinfo=timezone.utc)
        assert format_date(dt_first) == "2025-01-01"
        assert format_date(dt_last) == "2025-12-31"

    def test_format_date_ignores_time(self):
        """Test that time components are ignored."""
        dt1 = datetime(2025, 3, 20, 0, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 3, 20, 23, 59, 59, tzinfo=timezone.utc)
        assert format_date(dt1) == format_date(dt2) == "2025-03-20"

    def test_format_date_naive_datetime(self):
        """Test formatting naive (non-UTC) datetime."""
        dt = datetime(2025, 6, 15, 14, 30)
        result = format_date(dt)
        assert result == "2025-06-15"


class TestFormatDatetime:
    """Tests for format_datetime() function."""

    def test_format_datetime_basic(self):
        """Test basic datetime formatting."""
        dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = format_datetime(dt)
        assert result == "2025-01-15 10:30"

    def test_format_datetime_with_seconds(self):
        """Test that seconds are truncated."""
        dt = datetime(2025, 5, 20, 14, 45, 59, tzinfo=timezone.utc)
        result = format_datetime(dt)
        assert result == "2025-05-20 14:45"

    def test_format_datetime_midnight(self):
        """Test formatting midnight."""
        dt = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert format_datetime(dt) == "2025-02-01 00:00"

    def test_format_datetime_end_of_day(self):
        """Test formatting just before midnight."""
        dt = datetime(2025, 2, 1, 23, 59, 0, tzinfo=timezone.utc)
        assert format_datetime(dt) == "2025-02-01 23:59"

    def test_format_datetime_naive(self):
        """Test formatting naive datetime."""
        dt = datetime(2025, 8, 15, 9, 5)
        result = format_datetime(dt)
        assert result == "2025-08-15 09:05"


class TestFormatRelativeTime:
    """Tests for format_relative_time() function."""

    def test_relative_time_just_now(self):
        """Test very recent timestamps."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(seconds=30)
        result = format_relative_time(recent)
        assert result == "just now"

    def test_relative_time_minutes_ago(self):
        """Test time in minutes ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=5)
        result = format_relative_time(past)
        assert result == "5m ago"

    def test_relative_time_one_minute_ago(self):
        """Test exactly one minute ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=1)
        result = format_relative_time(past)
        assert result == "1m ago"

    def test_relative_time_almost_one_hour(self):
        """Test 59 minutes ago (should be in minutes)."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=59)
        result = format_relative_time(past)
        assert result == "59m ago"

    def test_relative_time_hours_ago(self):
        """Test time in hours ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=3)
        result = format_relative_time(past)
        assert result == "3h ago"

    def test_relative_time_one_hour_ago(self):
        """Test exactly one hour ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        result = format_relative_time(past)
        assert result == "1h ago"

    def test_relative_time_almost_one_day(self):
        """Test 23 hours ago (should be in hours)."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=23)
        result = format_relative_time(past)
        assert result == "23h ago"

    def test_relative_time_days_ago(self):
        """Test time in days ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=5)
        result = format_relative_time(past)
        assert result == "5d ago"

    def test_relative_time_one_day_ago(self):
        """Test exactly one day ago."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=1)
        result = format_relative_time(past)
        assert result == "1d ago"

    def test_relative_time_almost_one_week(self):
        """Test 6 days ago (should be in days)."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=6)
        result = format_relative_time(past)
        assert result == "6d ago"

    def test_relative_time_one_week_or_older(self):
        """Test 7+ days ago (should be formatted as date)."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=7)
        result = format_relative_time(past)
        # Should use format_date format: YYYY-MM-DD
        assert result == format_date(past)

    def test_relative_time_old_date(self):
        """Test old date formatting."""
        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        result = format_relative_time(old)
        assert result == "2020-01-01"

    def test_relative_time_naive_datetime(self):
        """Test relative time with naive datetime."""
        # Use a fixed past time without timezone for testing
        now = datetime.now()
        past = now - timedelta(minutes=10)
        result = format_relative_time(past)
        assert result == "10m ago"
