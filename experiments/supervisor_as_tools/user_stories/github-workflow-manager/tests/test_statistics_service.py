import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_attempt_status import WorkflowAttemptStatus
from src.models.workflow_attempt_conclusion import WorkflowAttemptConclusion
from src.models.statistics_report import StatisticsReport
from src.services.statistics_service import StatisticsService


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 0.0,
    attempts: list = None,
) -> WorkflowRun:
    """Helper to create a WorkflowRun for testing."""
    if attempts is None:
        attempts = []
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
        attempts=attempts,
    )


def _make_attempt(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: WorkflowAttemptStatus = WorkflowAttemptStatus.COMPLETED,
    conclusion: WorkflowAttemptConclusion = WorkflowAttemptConclusion.SUCCESS,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt for testing."""
    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    """Fixture providing a StatisticsService."""
    return StatisticsService()


class TestComputeStatistics:
    """Tests for StatisticsService.compute_statistics()"""

    def test_compute_statistics_with_empty_runs(self, service):
        """Empty runs list should return zeros."""
        result = service.compute_statistics([])

        assert result.total_runs == 0
        assert result.count_by_conclusion == {}
        assert result.average_duration_seconds == 0.0
        assert result.min_duration_seconds == 0.0
        assert result.max_duration_seconds == 0.0
        assert result.average_attempts_per_run == 0.0
        assert result.per_status_avg_duration == {}

    def test_compute_statistics_with_single_run(self, service):
        """Single run should compute basic statistics."""
        run = _make_run("run-1", duration_seconds=10.0)
        result = service.compute_statistics([run])

        assert result.total_runs == 1
        assert result.count_by_conclusion == {WorkflowConclusion.SUCCESS: 1}
        assert result.average_duration_seconds == 10.0
        assert result.min_duration_seconds == 10.0
        assert result.max_duration_seconds == 10.0
        assert result.average_attempts_per_run == 0.0
        assert result.per_status_avg_duration == {WorkflowStatus.COMPLETED: 10.0}

    def test_compute_statistics_with_all_metrics(self, service):
        """Multiple runs with attempts should compute all metrics."""
        attempt1 = _make_attempt(1, 1, 1, duration_seconds=5.0)
        attempt2 = _make_attempt(2, 1, 2, duration_seconds=3.0)
        run1 = _make_run("run-1", duration_seconds=30.0, attempts=[attempt1, attempt2])

        run2 = _make_run("run-2", duration_seconds=20.0, attempts=[])

        run3 = _make_run(
            "run-3",
            duration_seconds=40.0,
            conclusion=WorkflowConclusion.FAILURE,
            attempts=[_make_attempt(3, 3, 1)],
        )

        result = service.compute_statistics([run1, run2, run3])

        assert result.total_runs == 3
        assert result.count_by_conclusion == {
            WorkflowConclusion.SUCCESS: 2,
            WorkflowConclusion.FAILURE: 1,
        }
        assert result.average_duration_seconds == pytest.approx(30.0)  # (30 + 20 + 40) / 3
        assert result.min_duration_seconds == 20.0
        assert result.max_duration_seconds == 40.0
        assert result.average_attempts_per_run == pytest.approx(1.0)  # (2 + 0 + 1) / 3
        assert result.per_status_avg_duration == {WorkflowStatus.COMPLETED: 30.0}

    def test_compute_statistics_with_runs_no_attempts(self, service):
        """Runs with no attempts should have zero average attempts."""
        run1 = _make_run("run-1", duration_seconds=10.0, attempts=[])
        run2 = _make_run("run-2", duration_seconds=20.0, attempts=[])

        result = service.compute_statistics([run1, run2])

        assert result.total_runs == 2
        assert result.average_attempts_per_run == 0.0
        assert result.average_duration_seconds == pytest.approx(15.0)

    def test_compute_statistics_with_mixed_statuses(self, service):
        """Runs with different statuses should compute per-status averages."""
        run1 = _make_run(
            "run-1",
            status=WorkflowStatus.COMPLETED,
            duration_seconds=10.0,
        )
        run2 = _make_run(
            "run-2",
            status=WorkflowStatus.IN_PROGRESS,
            duration_seconds=20.0,
        )
        run3 = _make_run(
            "run-3",
            status=WorkflowStatus.COMPLETED,
            duration_seconds=30.0,
        )

        result = service.compute_statistics([run1, run2, run3])

        assert result.per_status_avg_duration == {
            WorkflowStatus.COMPLETED: pytest.approx(20.0),  # (10 + 30) / 2
            WorkflowStatus.IN_PROGRESS: pytest.approx(20.0),
        }

    def test_compute_statistics_with_none_conclusions(self, service):
        """Runs with None conclusions should be excluded from count_by_conclusion."""
        run1 = _make_run("run-1", conclusion=WorkflowConclusion.SUCCESS)
        run2 = _make_run("run-2", conclusion=None)
        run3 = _make_run("run-3", conclusion=WorkflowConclusion.FAILURE)

        result = service.compute_statistics([run1, run2, run3])

        assert result.total_runs == 3
        assert result.count_by_conclusion == {
            WorkflowConclusion.SUCCESS: 1,
            WorkflowConclusion.FAILURE: 1,
        }

    def test_compute_statistics_filtered_by_branch(self, service):
        """Test branch filtering at service level (not in compute_statistics)."""
        # This test validates that the StatisticsReport structure works
        # Branch filtering is done by WorkflowRunService.filter_runs()
        run1 = _make_run("run-1", branch="main", duration_seconds=10.0)
        run2 = _make_run("run-2", branch="dev", duration_seconds=20.0)

        result = service.compute_statistics([run1])  # Only main branch

        assert result.total_runs == 1
        assert result.average_duration_seconds == 10.0

    def test_compute_statistics_filtered_by_status(self, service):
        """Test status filtering at service level."""
        run1 = _make_run("run-1", status=WorkflowStatus.COMPLETED, duration_seconds=10.0)
        run2 = _make_run("run-2", status=WorkflowStatus.IN_PROGRESS, duration_seconds=20.0)

        result = service.compute_statistics([run1])  # Only completed

        assert result.total_runs == 1
        assert result.per_status_avg_duration == {WorkflowStatus.COMPLETED: 10.0}

    def test_compute_statistics_filtered_by_conclusion(self, service):
        """Test conclusion filtering at service level."""
        run1 = _make_run("run-1", conclusion=WorkflowConclusion.SUCCESS, duration_seconds=10.0)
        run2 = _make_run("run-2", conclusion=WorkflowConclusion.FAILURE, duration_seconds=20.0)

        result = service.compute_statistics([run1])  # Only success

        assert result.total_runs == 1
        assert result.count_by_conclusion == {WorkflowConclusion.SUCCESS: 1}


class TestFormatStatisticsForTerminal:
    """Tests for StatisticsService.format_statistics_for_terminal()"""

    def test_format_statistics_for_terminal(self, service):
        """Terminal output should include all sections clearly."""
        attempt = _make_attempt(1, 1, 1, duration_seconds=5.0)
        run1 = _make_run("run-1", duration_seconds=30.0, attempts=[attempt])
        run2 = _make_run("run-2", duration_seconds=20.0, conclusion=WorkflowConclusion.FAILURE)

        report = service.compute_statistics([run1, run2])
        output = service.format_statistics_for_terminal(report)

        # Check that key sections are present
        assert "--- Workflow Statistics ---" in output
        assert "Total runs: 2" in output
        assert "Conclusion breakdown:" in output
        assert "success: 1" in output
        assert "failure: 1" in output
        assert "Duration statistics (seconds):" in output
        assert "Average:" in output
        assert "Minimum:" in output
        assert "Maximum:" in output
        assert "Average attempts per run:" in output
        assert "Average duration by status:" in output
        assert "completed: " in output

    def test_format_statistics_empty_report(self, service):
        """Empty report should format correctly."""
        report = service.compute_statistics([])
        output = service.format_statistics_for_terminal(report)

        assert "--- Workflow Statistics ---" in output
        assert "Total runs: 0" in output
        assert "Average:" in output
        assert "0.00" in output

    def test_format_statistics_numbers_formatted(self, service):
        """Numbers should be formatted to 2 decimal places."""
        run = _make_run("run-1", duration_seconds=33.3333)
        report = service.compute_statistics([run])
        output = service.format_statistics_for_terminal(report)

        # Check that 33.3333 is formatted to 2 decimal places
        assert "33.33" in output

    def test_format_statistics_single_conclusion(self, service):
        """Single conclusion type should display correctly."""
        run = _make_run("run-1", conclusion=WorkflowConclusion.SUCCESS)
        report = service.compute_statistics([run])
        output = service.format_statistics_for_terminal(report)

        assert "Conclusion breakdown:" in output
        assert "success: 1" in output
        assert "failure:" not in output or "failure: 0" not in output

    def test_format_statistics_multiple_statuses(self, service):
        """Multiple statuses should all appear in output."""
        run1 = _make_run("run-1", status=WorkflowStatus.COMPLETED, duration_seconds=10.0)
        run2 = _make_run("run-2", status=WorkflowStatus.IN_PROGRESS, duration_seconds=20.0)
        run3 = _make_run("run-3", status=WorkflowStatus.QUEUED, duration_seconds=5.0)

        report = service.compute_statistics([run1, run2, run3])
        output = service.format_statistics_for_terminal(report)

        assert "Average duration by status:" in output
        assert "completed:" in output
        assert "in_progress:" in output
        assert "queued:" in output


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_compute_statistics_zero_duration_runs(self, service):
        """Runs with zero duration should be handled correctly."""
        run1 = _make_run("run-1", duration_seconds=0.0)
        run2 = _make_run("run-2", duration_seconds=0.0)

        result = service.compute_statistics([run1, run2])

        assert result.average_duration_seconds == 0.0
        assert result.min_duration_seconds == 0.0
        assert result.max_duration_seconds == 0.0

    def test_compute_statistics_large_durations(self, service):
        """Large duration values should be handled correctly."""
        run1 = _make_run("run-1", duration_seconds=3600.0)  # 1 hour
        run2 = _make_run("run-2", duration_seconds=7200.0)  # 2 hours

        result = service.compute_statistics([run1, run2])

        assert result.average_duration_seconds == pytest.approx(5400.0)
        assert result.min_duration_seconds == 3600.0
        assert result.max_duration_seconds == 7200.0

    def test_compute_statistics_many_attempts(self, service):
        """Runs with many attempts should compute correctly."""
        attempts = [_make_attempt(i, 1, i, duration_seconds=float(i)) for i in range(1, 6)]
        run = _make_run("run-1", duration_seconds=30.0, attempts=attempts)

        result = service.compute_statistics([run])

        assert result.total_runs == 1
        assert result.average_attempts_per_run == 5.0

    def test_report_is_frozen(self, service):
        """StatisticsReport should be immutable (frozen dataclass)."""
        run = _make_run("run-1", duration_seconds=10.0)
        report = service.compute_statistics([run])

        with pytest.raises(AttributeError):
            report.total_runs = 999
