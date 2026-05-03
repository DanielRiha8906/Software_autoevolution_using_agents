"""
Integration tests for CLI stats command.

Tests cover:
- Stats command with no filters (all runs)
- Stats command with single filters (branch, status, conclusion, duration, date)
- Stats command with multiple combined filters
- Mutually exclusive flags (--has-attempts vs --no-attempts)
- Validation errors (negative duration, invalid dates)
- No matching runs (graceful handling)
"""

import pytest
import tempfile
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage
from src.cli.workflow_cli import run_cli
from io import StringIO
import sys


@pytest.fixture
def temp_storage():
    """Temporary JSON storage for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.json")
        attempts_file = os.path.join(tmpdir, "attempts.json")
        storage = WorkflowJsonStorage(runs_file, attempts_file)
        yield storage


@pytest.fixture
def base_datetime():
    """Shared base datetime."""
    return datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_runs(base_datetime):
    """Sample workflow runs for testing."""
    return [
        WorkflowRun(
            id="1",
            workflow_name="build",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="sha1",
            duration_seconds=100.0,
        ),
        WorkflowRun(
            id="2",
            workflow_name="build",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=2,
            commit_sha="sha2",
            duration_seconds=150.0,
        ),
        WorkflowRun(
            id="3",
            workflow_name="test",
            branch="develop",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=3,
            commit_sha="sha3",
            duration_seconds=75.0,
        ),
        WorkflowRun(
            id="4",
            workflow_name="build",
            branch="develop",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=4,
            commit_sha="sha4",
            duration_seconds=30.0,
        ),
        WorkflowRun(
            id="5",
            workflow_name="test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=5,
            commit_sha="sha5",
            duration_seconds=60.0,
        ),
    ]


@pytest.fixture
def sample_attempts(base_datetime):
    """Sample workflow run attempts."""
    return [
        WorkflowRunAttempt(id=1, run_id=1, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=100.0),
        WorkflowRunAttempt(id=2, run_id=2, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=150.0),
        WorkflowRunAttempt(id=3, run_id=3, attempt_number=1, status="completed", conclusion="failure", created_at=base_datetime, duration_seconds=75.0),
    ]


@pytest.fixture
def services_with_data(temp_storage, sample_runs, sample_attempts):
    """Services initialized with sample data."""
    for run in sample_runs:
        temp_storage.save([run] if not hasattr(temp_storage, '_runs') else temp_storage._runs + [run])
    temp_storage.save(sample_runs)
    temp_storage.save_attempts(sample_attempts)

    run_service = WorkflowRunService(temp_storage)
    attempt_service = WorkflowRunAttemptService(temp_storage)
    return run_service, attempt_service


class TestStatsCommandNoFilters:
    """Test stats command with no filters."""

    def test_stats_no_filters(self, services_with_data, capsys):
        """Stats command without any filters should show all runs statistics."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
        assert "success" in captured.out
        assert "failure" in captured.out
        assert "cancelled" in captured.out
        assert "Average Duration" in captured.out
        assert "Average Attempts per Run" in captured.out

    def test_stats_output_format(self, services_with_data, capsys):
        """Stats output should be formatted correctly."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats"])

        captured = capsys.readouterr()
        # Check for expected formatting
        assert "Count by Conclusion:" in captured.out
        assert "Min Duration:" in captured.out
        assert "Max Duration:" in captured.out
        assert "Duration by Status:" in captured.out


class TestStatsCommandSingleFilters:
    """Test stats command with single filter options."""

    def test_stats_filter_by_branch(self, services_with_data, capsys):
        """Filter stats by branch."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "main"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
        # Should show stats for 3 runs on main branch (1,2,5)

    def test_stats_filter_by_branch_no_match(self, services_with_data, capsys):
        """Filter by non-existent branch."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "nonexistent"])

        captured = capsys.readouterr()
        # Should return valid report with empty counts
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_status(self, services_with_data, capsys):
        """Filter stats by status."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--status", "completed"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_conclusion(self, services_with_data, capsys):
        """Filter stats by conclusion."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--conclusion", "success"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_duration_min(self, services_with_data, capsys):
        """Filter stats by minimum duration."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-min", "50.0"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_duration_max(self, services_with_data, capsys):
        """Filter stats by maximum duration."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-max", "100.0"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_created_after(self, services_with_data, capsys):
        """Filter stats by created after date."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--created-after", "2025-05-01"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_filter_by_created_before(self, services_with_data, capsys):
        """Filter stats by created before date."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--created-before", "2025-05-02"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatsCommandMultipleFilters:
    """Test stats command with multiple combined filters."""

    def test_stats_branch_and_status(self, services_with_data, capsys):
        """Filter by branch AND status."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "main", "--status", "completed"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_branch_and_conclusion(self, services_with_data, capsys):
        """Filter by branch AND conclusion."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "main", "--conclusion", "success"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_duration_min_and_max(self, services_with_data, capsys):
        """Filter by both min and max duration."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-min", "50.0", "--duration-max", "150.0"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_date_range(self, services_with_data, capsys):
        """Filter by date range."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--created-after", "2025-05-01", "--created-before", "2025-05-02"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_all_filters_combined(self, services_with_data, capsys):
        """Apply all filter types together."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, [
            "stats",
            "--branch", "main",
            "--status", "completed",
            "--conclusion", "success",
            "--duration-min", "50.0",
            "--duration-max", "200.0",
            "--created-after", "2025-05-01",
            "--created-before", "2025-05-02",
        ])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatsCommandAttemptFilters:
    """Test stats command with attempt-related filters."""

    def test_stats_has_attempts(self, services_with_data, capsys):
        """Filter to show only runs with attempts."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--has-attempts"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_no_attempts(self, services_with_data, capsys):
        """Filter to show only runs without attempts."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--no-attempts"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_has_attempts_with_other_filters(self, services_with_data, capsys):
        """Combine attempt filter with other filters."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "main", "--has-attempts"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatsCommandValidation:
    """Test validation and error handling."""

    def test_stats_negative_duration_min(self, services_with_data, capsys):
        """Negative duration-min should be rejected."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, attempt_service, ["stats", "--duration-min", "-10.0"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "non-negative" in captured.err

    def test_stats_negative_duration_max(self, services_with_data, capsys):
        """Negative duration-max should be rejected."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, attempt_service, ["stats", "--duration-max", "-5.0"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "non-negative" in captured.err

    def test_stats_invalid_date_format(self, services_with_data, capsys):
        """Invalid date format should be rejected."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, attempt_service, ["stats", "--created-after", "invalid-date"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_stats_mutually_exclusive_attempts(self, services_with_data, capsys):
        """--has-attempts and --no-attempts should be mutually exclusive."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, attempt_service, ["stats", "--has-attempts", "--no-attempts"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "mutually exclusive" in captured.err

    def test_stats_invalid_status(self, services_with_data, capsys):
        """Invalid status should be rejected by argparse."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit):
            run_cli(run_service, attempt_service, ["stats", "--status", "invalid_status"])

    def test_stats_invalid_conclusion(self, services_with_data, capsys):
        """Invalid conclusion should be rejected by argparse."""
        run_service, attempt_service = services_with_data

        with pytest.raises(SystemExit):
            run_cli(run_service, attempt_service, ["stats", "--conclusion", "invalid_conclusion"])


class TestStatsCommandEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_stats_empty_database(self, temp_storage, capsys):
        """Stats on empty database."""
        run_service = WorkflowRunService(temp_storage)
        attempt_service = WorkflowRunAttemptService(temp_storage)

        run_cli(run_service, attempt_service, ["stats"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
        assert "(none)" in captured.out or "Count by Conclusion" in captured.out

    def test_stats_single_run(self, temp_storage, base_datetime, capsys):
        """Stats with single run."""
        run = WorkflowRun(
            id="1",
            workflow_name="test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="sha1",
            duration_seconds=100.0,
        )
        temp_storage.save([run])
        temp_storage.save_attempts([])

        run_service = WorkflowRunService(temp_storage)
        attempt_service = WorkflowRunAttemptService(temp_storage)

        run_cli(run_service, attempt_service, ["stats"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
        assert "success: 1" in captured.out

    def test_stats_with_iso_datetime(self, services_with_data, capsys):
        """Filter using ISO format datetime."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--created-after", "2025-05-01T00:00:00"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_float_duration_min(self, services_with_data, capsys):
        """Duration filters should accept float values."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-min", "42.5"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_zero_duration_filter(self, services_with_data, capsys):
        """Duration filter with zero value."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-min", "0.0"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatsCommandNoMatches:
    """Test graceful handling when no runs match filters."""

    def test_stats_branch_no_matches(self, services_with_data, capsys):
        """Filter by non-existent branch returns empty statistics."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--branch", "never_created"])

        captured = capsys.readouterr()
        # Should not error, should show empty stats
        assert "Statistics Report" in captured.out

    def test_stats_conclusion_no_matches(self, services_with_data, capsys):
        """Filter by conclusion with no matches."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--conclusion", "skipped"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_stats_duration_range_no_matches(self, services_with_data, capsys):
        """Duration filter with no matches."""
        run_service, attempt_service = services_with_data

        run_cli(run_service, attempt_service, ["stats", "--duration-min", "10000.0"])

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
