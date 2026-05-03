"""
Integration tests for interactive menu statistics option.

Tests cover:
- Menu option exists and is callable
- Statistics display with/without filters
- Input validation (non-numeric duration, unparseable dates)
- Multiple filters combined
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage
from src.cli.interactive_menu import _get_statistics, MENU


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
    """Sample workflow runs."""
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
    ]


@pytest.fixture
def sample_attempts(base_datetime):
    """Sample workflow run attempts."""
    return [
        WorkflowRunAttempt(id=1, run_id=1, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=100.0),
        WorkflowRunAttempt(id=2, run_id=2, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=150.0),
    ]


@pytest.fixture
def services_with_data(temp_storage, sample_runs, sample_attempts):
    """Services with sample data."""
    temp_storage.save(sample_runs)
    temp_storage.save_attempts(sample_attempts)

    run_service = WorkflowRunService(temp_storage)
    attempt_service = WorkflowRunAttemptService(temp_storage)
    return run_service, attempt_service


class TestMenuOptionExists:
    """Test that statistics menu option exists."""

    def test_statistics_option_in_menu(self):
        """Statistics option should be in MENU list."""
        menu_labels = [label for label, _ in MENU]
        assert "Get statistics" in menu_labels

    def test_statistics_handler_callable(self):
        """Statistics handler should be callable."""
        for label, handler in MENU:
            if label == "Get statistics":
                assert callable(handler)
                assert handler == _get_statistics
                break
        else:
            pytest.fail("Get statistics option not found in MENU")


class TestStatisticsWithoutFilters:
    """Test statistics display without any filters."""

    def test_statistics_no_filters(self, services_with_data, capsys):
        """Show statistics without applying filters."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Answer "No" to all filter questions (option 2 = No)
            # 8 questions: branch, status, conclusion, created-after, created-before, duration-min, duration-max, attempts
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out
        assert "Count by Conclusion:" in captured.out
        assert "Average Duration:" in captured.out
        assert "Average Attempts per Run:" in captured.out

    def test_statistics_output_structure(self, services_with_data, capsys):
        """Output should have proper structure and formatting."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Answer "No" to all filters (option 2)
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Min Duration:" in captured.out
        assert "Max Duration:" in captured.out
        assert "Duration by Status:" in captured.out


class TestStatisticsWithFilters:
    """Test statistics with various filter combinations."""

    def test_statistics_filter_by_branch(self, services_with_data, capsys):
        """Apply branch filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Yes (1) to branch, "main" as branch name
            # No (2) to: status, conclusion, created-after, created-before, duration-min, duration-max, attempts
            mock_input.side_effect = ["1", "main", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_status(self, services_with_data, capsys):
        """Apply status filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No (2) to branch
            # Yes (1) to status, choose completed (3)
            # No (2) to: conclusion, created-after, created-before, duration-min, duration-max, attempts
            mock_input.side_effect = ["2", "1", "3", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_conclusion(self, services_with_data, capsys):
        """Apply conclusion filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No (2) to branch and status
            # Yes (1) to conclusion, choose success (1)
            # No (2) to: created-after, created-before, duration-min, duration-max, attempts
            mock_input.side_effect = ["2", "2", "1", "1", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_duration_min(self, services_with_data, capsys):
        """Apply minimum duration filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion, created-after, created-before
            # Yes to duration-min, specify 50.0
            # No to duration-max and attempts
            mock_input.side_effect = ["2", "2", "2", "2", "2", "1", "50.0", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_duration_max(self, services_with_data, capsys):
        """Apply maximum duration filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to all until duration-max
            # Yes to duration-max, specify 100.0
            # No to attempts
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "1", "100.0", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_date_range(self, services_with_data, capsys):
        """Apply date range filters."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion
            # Yes to created-after, specify date
            # Yes to created-before, specify date
            # No to duration filters and attempts
            mock_input.side_effect = [
                "2", "2", "2",  # branch, status, conclusion
                "1", "2025-05-01",  # created-after
                "1", "2025-05-02",  # created-before
                "2",  # duration-min
                "2",  # duration-max
                "2",  # attempts
            ]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_filter_by_attempts(self, services_with_data, capsys):
        """Apply attempt presence filter."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to all filters until attempts
            # Yes to attempts, choose "With attempts" (option 1)
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "1", "1"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_multiple_filters_combined(self, services_with_data, capsys):
        """Apply multiple filters together."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Yes (1) to branch "main"
            # Yes (1) to status, choose completed (3)
            # No (2) to: conclusion, created-after, created-before, duration-min, duration-max, attempts
            # That's 2 + 2 + 6 = 10 inputs total
            mock_input.side_effect = ["1", "main", "1", "3", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatisticsInputValidation:
    """Test input validation in interactive menu."""

    def test_invalid_duration_min_non_numeric(self, services_with_data, capsys):
        """Non-numeric duration-min input."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion, created-after, created-before
            # Yes to duration-min with invalid input
            mock_input.side_effect = ["2", "2", "2", "2", "2", "1", "not_a_number"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        # Should show error about invalid duration
        assert "Duration must be a number" in captured.out or "Error" in captured.out

    def test_invalid_duration_min_negative(self, services_with_data, capsys):
        """Negative duration-min input."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion, created-after, created-before
            # Yes to duration-min with negative value
            mock_input.side_effect = ["2", "2", "2", "2", "2", "1", "-50.0"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        # Should show error about non-negative
        assert "non-negative" in captured.out or "Error" in captured.out

    def test_invalid_duration_max_non_numeric(self, services_with_data, capsys):
        """Non-numeric duration-max input."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to most, yes to duration-max with invalid input
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "1", "abc123"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Duration must be a number" in captured.out or "Error" in captured.out

    def test_invalid_date_format_created_after(self, services_with_data, capsys):
        """Invalid date format for created-after."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion
            # Yes to created-after with invalid date
            mock_input.side_effect = ["2", "2", "2", "1", "invalid-date"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        # Should show error about invalid date
        assert "Error" in captured.out or "parse" in captured.out

    def test_invalid_date_format_created_before(self, services_with_data, capsys):
        """Invalid date format for created-before."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # No to branch, status, conclusion, created-after
            # Yes to created-before with invalid date
            mock_input.side_effect = ["2", "2", "2", "2", "1", "not-a-date"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Error" in captured.out or "parse" in captured.out


class TestStatisticsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_statistics_empty_database(self, temp_storage, capsys):
        """Statistics on empty database."""
        run_service = WorkflowRunService(temp_storage)
        attempt_service = WorkflowRunAttemptService(temp_storage)

        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_valid_date_formats(self, services_with_data, capsys):
        """Both YYYY-MM-DD and ISO date formats should work."""
        run_service, attempt_service = services_with_data

        # Test YYYY-MM-DD format
        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "1", "2025-05-01", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

        # Test ISO format
        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "1", "2025-05-01T12:00:00", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_zero_duration_filter(self, services_with_data, capsys):
        """Zero duration value should be accepted."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Yes to duration-min with 0.0
            mock_input.side_effect = ["2", "2", "2", "2", "2", "1", "0.0", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_large_duration_values(self, services_with_data, capsys):
        """Large duration values should be handled."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Yes to duration-min with large value
            mock_input.side_effect = ["2", "2", "2", "2", "2", "1", "999999.99", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_with_no_matching_runs(self, services_with_data, capsys):
        """Statistics when filters result in no matching runs."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            # Yes (1) to branch "nonexistent_branch"
            # No (2) to: status, conclusion, created-after, created-before, duration-min, duration-max, attempts
            mock_input.side_effect = ["1", "nonexistent_branch", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out

    def test_statistics_single_run_in_database(self, temp_storage, base_datetime, capsys):
        """Statistics with only one run."""
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

        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Statistics Report" in captured.out


class TestStatisticsOutputContent:
    """Test the content of statistics output."""

    def test_output_includes_all_sections(self, services_with_data, capsys):
        """Output should include all required sections."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        assert "Count by Conclusion:" in captured.out
        assert "Average Duration:" in captured.out
        assert "Average Attempts per Run:" in captured.out
        assert "Min Duration:" in captured.out
        assert "Max Duration:" in captured.out
        assert "Duration by Status:" in captured.out

    def test_output_shows_conclusion_counts(self, services_with_data, capsys):
        """Output should show conclusion counts."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        # Should show at least success and failure from sample data
        assert "success" in captured.out or "failure" in captured.out

    def test_output_shows_duration_values(self, services_with_data, capsys):
        """Output should show duration values with 2 decimal places."""
        run_service, attempt_service = services_with_data

        with patch("builtins.input") as mock_input:
            mock_input.side_effect = ["2", "2", "2", "2", "2", "2", "2", "2"]

            _get_statistics(run_service, attempt_service)

        captured = capsys.readouterr()
        # Check for decimal places in output (e.g., "123.45")
        import re
        assert re.search(r"\d+\.\d{2}", captured.out)
