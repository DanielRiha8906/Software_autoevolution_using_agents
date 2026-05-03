"""
Comprehensive unit tests for StatisticsService.calculate_statistics().

Tests cover:
- Empty dataset behavior
- Single run scenarios
- Multiple run scenarios
- All conclusion types
- Duration calculations (average, min, max)
- Attempts per run calculation
- Per-status duration breakdown
- Frozen dataclass immutability
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.statistics_report import StatisticsReport
from src.services.statistics_service import StatisticsService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


@pytest.fixture
def base_datetime():
    """Shared base datetime for consistent test data."""
    return datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_attempt_service():
    """Mock WorkflowRunAttemptService for testing."""
    return Mock(spec=WorkflowRunAttemptService)


@pytest.fixture
def stats_service():
    """StatisticsService instance."""
    return StatisticsService()


class TestEmptyDataset:
    """Test behavior with empty dataset."""

    def test_empty_runs_returns_valid_report(self, stats_service):
        """Empty run list should return valid report with sensible defaults."""
        report = stats_service.calculate_statistics([])

        assert isinstance(report, StatisticsReport)
        assert report.count_by_conclusion == {}
        assert report.average_duration_seconds == 0.0
        assert report.average_attempts_per_run == 0.0
        assert report.min_duration_seconds is None
        assert report.max_duration_seconds is None
        assert all(duration == 0.0 for duration in report.duration_by_status.values())

    def test_empty_runs_no_attempt_service(self, stats_service):
        """Empty runs without attempt service should return valid report."""
        report = stats_service.calculate_statistics([], None)

        assert report.average_attempts_per_run == 0.0
        assert report.count_by_conclusion == {}

    def test_empty_runs_with_attempt_service(self, stats_service, mock_attempt_service):
        """Empty runs with attempt service should return valid report without calling service."""
        mock_attempt_service.list_attempts.return_value = []
        report = stats_service.calculate_statistics([], mock_attempt_service)

        assert report.average_attempts_per_run == 0.0
        # Service is not called for empty runs (early return)
        # This is an optimization - no need to get attempts if there are no runs

    def test_duration_by_status_all_zeros_for_empty_runs(self, stats_service):
        """All status averages should be 0.0 for empty runs."""
        report = stats_service.calculate_statistics([])

        for status in WorkflowStatus:
            assert report.duration_by_status[status.value] == 0.0


class TestSingleRun:
    """Test behavior with a single run."""

    def test_single_successful_run(self, stats_service, base_datetime):
        """Single successful run should compute correct statistics."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        report = stats_service.calculate_statistics([run])

        assert report.count_by_conclusion == {"success": 1}
        assert report.average_duration_seconds == 100.0
        assert report.min_duration_seconds == 100.0
        assert report.max_duration_seconds == 100.0

    def test_single_run_with_zero_duration(self, stats_service, base_datetime):
        """Single run with zero duration."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=0.0,
        )

        report = stats_service.calculate_statistics([run])

        assert report.average_duration_seconds == 0.0
        assert report.min_duration_seconds == 0.0
        assert report.max_duration_seconds == 0.0

    def test_single_run_no_conclusion(self, stats_service, base_datetime):
        """Single run without conclusion should not appear in count_by_conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=50.0,
        )

        report = stats_service.calculate_statistics([run])

        assert report.count_by_conclusion == {}


class TestMultipleRuns:
    """Test behavior with multiple runs."""

    def test_multiple_runs_same_conclusion(self, stats_service, base_datetime):
        """Multiple runs with same conclusion."""
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=100.0 + i * 10,
            )
            for i in range(3)
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.count_by_conclusion == {"success": 3}
        assert report.average_duration_seconds == 110.0  # (100+110+120)/3

    def test_multiple_runs_mixed_conclusions(self, stats_service, base_datetime):
        """Multiple runs with different conclusions."""
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SUCCESS,
        ]

        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=50.0,
            )
            for i, conclusion in enumerate(conclusions)
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.count_by_conclusion == {
            "success": 2,
            "failure": 1,
            "cancelled": 1,
        }

    def test_average_duration_multiple_runs(self, stats_service, base_datetime):
        """Average duration calculation across multiple runs."""
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=float(duration),
            )
            for i, duration in enumerate([10.0, 20.0, 30.0, 40.0])
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.average_duration_seconds == 25.0  # (10+20+30+40)/4


class TestMinMaxDuration:
    """Test min and max duration calculations."""

    def test_min_max_single_run(self, stats_service, base_datetime):
        """Min and max should be equal for single run."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=75.5,
        )

        report = stats_service.calculate_statistics([run])

        assert report.min_duration_seconds == 75.5
        assert report.max_duration_seconds == 75.5

    def test_min_max_multiple_runs(self, stats_service, base_datetime):
        """Min and max across multiple runs."""
        durations = [5.0, 100.0, 25.5, 50.0, 10.0]
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=duration,
            )
            for i, duration in enumerate(durations)
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.min_duration_seconds == 5.0
        assert report.max_duration_seconds == 100.0

    def test_min_max_empty_runs(self, stats_service):
        """Min and max should be None for empty runs."""
        report = stats_service.calculate_statistics([])

        assert report.min_duration_seconds is None
        assert report.max_duration_seconds is None


class TestAverageDurationByStatus:
    """Test per-status average duration calculation (bonus feature)."""

    def test_all_statuses_present(self, stats_service, base_datetime):
        """All statuses should be present in output, even with zero runs."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        report = stats_service.calculate_statistics([run])

        # All statuses should be keys in the report
        for status in WorkflowStatus:
            assert status.value in report.duration_by_status

    def test_duration_by_status_single_status(self, stats_service, base_datetime):
        """Average duration for runs with a specific status."""
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=float(duration),
            )
            for i, duration in enumerate([50.0, 100.0])
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.duration_by_status["completed"] == 75.0  # (50+100)/2

    def test_duration_by_status_multiple_statuses(self, stats_service, base_datetime):
        """Average duration grouped by different statuses."""
        runs = [
            # Completed runs
            WorkflowRun(
                id="run-1",
                workflow_name="test-workflow",
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
                id="run-2",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=2,
                commit_sha="sha2",
                duration_seconds=200.0,
            ),
            # In-progress runs
            WorkflowRun(
                id="run-3",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=3,
                commit_sha="sha3",
                duration_seconds=50.0,
            ),
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.duration_by_status["completed"] == 150.0  # (100+200)/2
        assert report.duration_by_status["in_progress"] == 50.0

    def test_duration_by_status_empty_status(self, stats_service, base_datetime):
        """Status with no runs should have 0.0 average."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        report = stats_service.calculate_statistics([run])

        assert report.duration_by_status["in_progress"] == 0.0
        assert report.duration_by_status["queued"] == 0.0
        assert report.duration_by_status["waiting"] == 0.0


class TestAverageAttemptsPerRun:
    """Test average attempts per run calculation."""

    def test_no_attempt_service_returns_zero(self, stats_service, base_datetime):
        """Without attempt service, average_attempts_per_run should be 0.0."""
        run = WorkflowRun(
            id="1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        report = stats_service.calculate_statistics([run], None)

        assert report.average_attempts_per_run == 0.0

    def test_single_run_single_attempt(self, stats_service, base_datetime, mock_attempt_service):
        """Single run with single attempt."""
        run = WorkflowRun(
            id="1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=base_datetime,
            duration_seconds=100.0,
        )

        mock_attempt_service.list_attempts.return_value = [attempt]

        report = stats_service.calculate_statistics([run], mock_attempt_service)

        assert report.average_attempts_per_run == 1.0  # 1 attempt / 1 run

    def test_multiple_runs_multiple_attempts(self, stats_service, base_datetime, mock_attempt_service):
        """Multiple runs with multiple attempts total."""
        runs = [
            WorkflowRun(
                id=f"{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=100.0,
            )
            for i in range(1, 6)  # 5 runs
        ]

        attempts = [
            WorkflowRunAttempt(
                id=j,
                run_id=1,
                attempt_number=j,
                status="completed",
                conclusion="success",
                created_at=base_datetime,
                duration_seconds=50.0,
            )
            for j in range(1, 4)  # 3 attempts for run 1
        ] + [
            WorkflowRunAttempt(
                id=4,
                run_id=2,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=base_datetime,
                duration_seconds=50.0,
            ),
            WorkflowRunAttempt(
                id=5,
                run_id=3,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=base_datetime,
                duration_seconds=50.0,
            ),
        ]  # 5 attempts total

        mock_attempt_service.list_attempts.return_value = attempts

        report = stats_service.calculate_statistics(runs, mock_attempt_service)

        assert report.average_attempts_per_run == 1.0  # 5 attempts / 5 runs

    def test_runs_without_attempts(self, stats_service, base_datetime, mock_attempt_service):
        """Runs without attempts included in denominator."""
        runs = [
            WorkflowRun(
                id=f"{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=100.0,
            )
            for i in range(1, 6)  # 5 runs
        ]

        attempts = [
            WorkflowRunAttempt(
                id=j,
                run_id=1,
                attempt_number=j,
                status="completed",
                conclusion="success",
                created_at=base_datetime,
                duration_seconds=50.0,
            )
            for j in range(1, 4)  # 3 attempts for run 1 only
        ]

        mock_attempt_service.list_attempts.return_value = attempts

        report = stats_service.calculate_statistics(runs, mock_attempt_service)

        # 3 attempts total / 5 runs = 0.6
        assert report.average_attempts_per_run == 0.6


class TestFrozenDataclass:
    """Test StatisticsReport immutability."""

    def test_report_is_frozen(self, stats_service, base_datetime):
        """StatisticsReport should be immutable (frozen=True)."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=100.0,
        )

        report = stats_service.calculate_statistics([run])

        # Attempt to modify should raise FrozenInstanceError
        with pytest.raises((AttributeError, TypeError)):
            report.average_duration_seconds = 200.0


class TestAllConclusionTypes:
    """Test counting all conclusion types."""

    def test_count_all_conclusion_types(self, stats_service, base_datetime):
        """Count runs for each conclusion type."""
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]

        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=50.0,
            )
            for i, conclusion in enumerate(conclusions)
        ]

        report = stats_service.calculate_statistics(runs)

        expected = {c.value: 1 for c in conclusions}
        assert report.count_by_conclusion == expected


class TestFullScenario:
    """Test with complex mixed data."""

    def test_full_scenario_mixed_data(self, stats_service, base_datetime, mock_attempt_service):
        """Complex scenario with mixed statuses, conclusions, durations, and attempts."""
        runs = [
            # Successful completed runs
            WorkflowRun(
                id="run-1",
                workflow_name="build",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=1,
                commit_sha="sha1",
                duration_seconds=120.0,
            ),
            WorkflowRun(
                id="run-2",
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
            # Failed completed run
            WorkflowRun(
                id="run-3",
                workflow_name="build",
                branch="develop",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=3,
                commit_sha="sha3",
                duration_seconds=90.0,
            ),
            # In-progress run (no conclusion yet)
            WorkflowRun(
                id="run-4",
                workflow_name="build",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=4,
                commit_sha="sha4",
                duration_seconds=30.0,
            ),
            # Cancelled run
            WorkflowRun(
                id="run-5",
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

        attempts = [
            WorkflowRunAttempt(id=1, run_id=1, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=120.0),
            WorkflowRunAttempt(id=2, run_id=2, attempt_number=1, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=100.0),
            WorkflowRunAttempt(id=3, run_id=2, attempt_number=2, status="completed", conclusion="success", created_at=base_datetime, duration_seconds=50.0),
            WorkflowRunAttempt(id=4, run_id=3, attempt_number=1, status="completed", conclusion="failure", created_at=base_datetime, duration_seconds=90.0),
        ]

        mock_attempt_service.list_attempts.return_value = attempts

        report = stats_service.calculate_statistics(runs, mock_attempt_service)

        # Verify all calculations
        assert report.count_by_conclusion == {"success": 2, "failure": 1, "cancelled": 1}
        assert report.average_duration_seconds == 90.0  # (120+150+90+30+60)/5
        assert report.min_duration_seconds == 30.0
        assert report.max_duration_seconds == 150.0
        assert report.average_attempts_per_run == 0.8  # 4 attempts / 5 runs
        assert report.duration_by_status["completed"] == 105.0  # (120+150+90+60)/4
        assert report.duration_by_status["in_progress"] == 30.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_duration(self, stats_service, base_datetime):
        """Handle very large duration values."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="test-workflow",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=base_datetime,
            updated_at=base_datetime,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=999999.99,
        )

        report = stats_service.calculate_statistics([run])

        assert report.average_duration_seconds == 999999.99
        assert report.min_duration_seconds == 999999.99
        assert report.max_duration_seconds == 999999.99

    def test_many_runs_with_same_duration(self, stats_service, base_datetime):
        """Many runs with identical durations."""
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=42.0,
            )
            for i in range(100)
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.average_duration_seconds == 42.0
        assert report.min_duration_seconds == 42.0
        assert report.max_duration_seconds == 42.0

    def test_single_conclusion_multiple_duplicates(self, stats_service, base_datetime):
        """Count duplicates of single conclusion type correctly."""
        runs = [
            WorkflowRun(
                id=f"run-{i}",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=i,
                commit_sha=f"sha{i}",
                duration_seconds=50.0,
            )
            for i in range(10)
        ]

        report = stats_service.calculate_statistics(runs)

        assert report.count_by_conclusion == {"success": 10}
        assert len(report.count_by_conclusion) == 1

    def test_mix_with_and_without_conclusion(self, stats_service, base_datetime):
        """Mix of runs with and without conclusions."""
        runs = [
            WorkflowRun(
                id="run-1",
                workflow_name="test-workflow",
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
                id="run-2",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=2,
                commit_sha="sha2",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run-3",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=3,
                commit_sha="sha3",
                duration_seconds=30.0,
            ),
        ]

        report = stats_service.calculate_statistics(runs)

        # Only completed run should be counted in conclusions
        assert report.count_by_conclusion == {"success": 1}
        # All runs included in duration average
        assert report.average_duration_seconds == 60.0  # (100+50+30)/3

    def test_attempt_service_called_correctly(self, stats_service, base_datetime, mock_attempt_service):
        """Verify attempt service is called with correct parameters."""
        runs = [
            WorkflowRun(
                id="run-1",
                workflow_name="test-workflow",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=base_datetime,
                updated_at=base_datetime,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=100.0,
            )
        ]

        mock_attempt_service.list_attempts.return_value = []

        stats_service.calculate_statistics(runs, mock_attempt_service)

        # Verify the service was called with sorted=False
        mock_attempt_service.list_attempts.assert_called_once_with(sorted=False)
