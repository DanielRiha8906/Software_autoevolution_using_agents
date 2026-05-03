"""Tests for WorkflowStatisticsService computation methods."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock

from src.services.workflow_statistics_service import WorkflowStatisticsService
from src.models.workflow_run import WorkflowRun
from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


class TestWorkflowStatisticsServiceComputeReport:
    """Test compute_report() method and related helper methods."""

    @pytest.fixture
    def mock_run_service(self):
        """Create a mock WorkflowRunService."""
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        """Create a mock WorkflowAttemptService."""
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        """Create a WorkflowStatisticsService with mocked dependencies."""
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_report_calls_list_runs(self, statistics_service, mock_run_service):
        """Test that compute_report() calls list_runs() on the service."""
        mock_run_service.list_runs.return_value = []
        mock_run_service.list_runs.return_value = []

        statistics_service.compute_report()

        mock_run_service.list_runs.assert_called_once()

    def test_compute_report_with_valid_data(self, statistics_service, mock_run_service, mock_attempt_service):
        """Test compute_report() with valid workflow run data."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=60.0,
            ),
        ]

        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        report = statistics_service.compute_report()

        assert report.total_runs == 2
        assert report.average_duration_seconds == 55.0

    def test_compute_report_with_attempts(self, statistics_service, mock_run_service, mock_attempt_service):
        """Test compute_report() includes attempt statistics."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
        ]

        attempts = [
            WorkflowRunAttempt(
                id="attempt1",
                run_id="run1",
                attempt_number=1,
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                started_at=now,
                completed_at=now,
                duration_seconds=50.0,
            ),
        ]

        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = attempts

        report = statistics_service.compute_report()

        assert report.total_attempts == 1
        assert report.average_attempts_per_run == 1.0

    def test_compute_report_returns_dataclass(self, statistics_service, mock_run_service, mock_attempt_service):
        """Test that compute_report() returns a WorkflowStatisticsReport dataclass."""
        from src.models.workflow_statistics_report import WorkflowStatisticsReport

        mock_run_service.list_runs.return_value = []
        mock_attempt_service.filter_by_run_id.return_value = []

        report = statistics_service.compute_report()

        assert isinstance(report, WorkflowStatisticsReport)

    def test_compute_report_includes_generated_at(self, statistics_service, mock_run_service, mock_attempt_service):
        """Test that compute_report() includes a generated_at timestamp."""
        mock_run_service.list_runs.return_value = []
        mock_attempt_service.filter_by_run_id.return_value = []

        before = datetime.now()
        report = statistics_service.compute_report()
        after = datetime.now()

        assert report.generated_at is not None
        assert before <= report.generated_at <= after


class TestComputeReportForRuns:
    """Test compute_report_for_runs() method with explicit run lists."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_report_for_runs_with_valid_data(self, statistics_service, mock_attempt_service):
        """Test compute_report_for_runs() with valid run data."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=100.0,
            ),
        ]

        mock_attempt_service.filter_by_run_id.return_value = []

        report = statistics_service.compute_report_for_runs(runs)

        assert report.total_runs == 1
        assert report.average_duration_seconds == 100.0

    def test_compute_report_for_runs_with_zero_runs(self, statistics_service, mock_attempt_service):
        """Test compute_report_for_runs() with empty list (edge case)."""
        mock_attempt_service.filter_by_run_id.return_value = []

        report = statistics_service.compute_report_for_runs([])

        assert report.total_runs == 0
        assert report.average_duration_seconds == 0.0
        assert report.average_attempts_per_run == 0.0

    def test_compute_report_for_runs_with_mixed_conclusions(self, statistics_service, mock_attempt_service):
        """Test compute_report_for_runs() with runs having different conclusions."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=70.0,
            ),
            WorkflowRun(
                id="run3",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.CANCELLED,
                created_at=now,
                updated_at=now,
                run_number=3,
                commit_sha="ghi789",
                duration_seconds=30.0,
            ),
        ]

        mock_attempt_service.filter_by_run_id.return_value = []

        report = statistics_service.compute_report_for_runs(runs)

        assert report.total_runs == 3
        assert "success" in report.conclusion_counts
        assert "failure" in report.conclusion_counts
        assert "cancelled" in report.conclusion_counts


class TestComputeConclusionCounts:
    """Test _compute_conclusion_counts() helper method."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_conclusion_counts_with_single_conclusion(self, statistics_service):
        """Test counting runs with a single conclusion type."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=60.0,
            ),
        ]

        counts = statistics_service._compute_conclusion_counts(runs)

        assert counts["success"] == 2

    def test_compute_conclusion_counts_with_multiple_conclusions(self, statistics_service):
        """Test counting runs with multiple conclusion types."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=60.0,
            ),
            WorkflowRun(
                id="run3",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=now,
                updated_at=now,
                run_number=3,
                commit_sha="ghi789",
                duration_seconds=70.0,
            ),
        ]

        counts = statistics_service._compute_conclusion_counts(runs)

        assert counts["success"] == 1
        assert counts["failure"] == 2

    def test_compute_conclusion_counts_with_none_conclusion(self, statistics_service):
        """Test counting runs with None conclusion (incomplete runs)."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=now,
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=0.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=now,
                updated_at=None,
                run_number=2,
                commit_sha="def456",
                duration_seconds=0.0,
            ),
        ]

        counts = statistics_service._compute_conclusion_counts(runs)

        assert None in counts
        assert counts[None] == 2

    def test_compute_conclusion_counts_with_mixed_conclusions_and_none(self, statistics_service):
        """Test counting with both terminal and non-terminal runs."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=now,
                updated_at=None,
                run_number=2,
                commit_sha="def456",
                duration_seconds=0.0,
            ),
        ]

        counts = statistics_service._compute_conclusion_counts(runs)

        assert counts["success"] == 1
        assert counts[None] == 1

    def test_compute_conclusion_counts_empty_list(self, statistics_service):
        """Test counting with empty run list."""
        counts = statistics_service._compute_conclusion_counts([])

        assert counts == {}


class TestComputeAverageDuration:
    """Test _compute_average_duration() helper method."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_average_duration_with_single_run(self, statistics_service):
        """Test average duration with a single run."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=100.0,
            ),
        ]

        avg = statistics_service._compute_average_duration(runs)

        assert avg == 100.0

    def test_compute_average_duration_with_multiple_runs(self, statistics_service):
        """Test average duration with multiple runs."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=60.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=40.0,
            ),
        ]

        avg = statistics_service._compute_average_duration(runs)

        assert avg == 50.0

    def test_compute_average_duration_with_empty_list(self, statistics_service):
        """Test average duration with empty list returns 0.0."""
        avg = statistics_service._compute_average_duration([])

        assert avg == 0.0

    def test_compute_average_duration_with_zero_durations(self, statistics_service):
        """Test average duration when all runs have 0 duration."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=0.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=0.0,
            ),
        ]

        avg = statistics_service._compute_average_duration(runs)

        assert avg == 0.0


class TestComputeMinMaxDuration:
    """Test _compute_min_max_duration() helper method."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_min_max_duration_with_single_run(self, statistics_service):
        """Test min/max duration with a single run."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
        ]

        min_dur, max_dur = statistics_service._compute_min_max_duration(runs)

        assert min_dur == 50.0
        assert max_dur == 50.0

    def test_compute_min_max_duration_with_multiple_runs(self, statistics_service):
        """Test min/max duration with multiple runs."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=30.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=100.0,
            ),
            WorkflowRun(
                id="run3",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=3,
                commit_sha="ghi789",
                duration_seconds=50.0,
            ),
        ]

        min_dur, max_dur = statistics_service._compute_min_max_duration(runs)

        assert min_dur == 30.0
        assert max_dur == 100.0

    def test_compute_min_max_duration_with_empty_list(self, statistics_service):
        """Test min/max duration with empty list returns (None, None)."""
        min_dur, max_dur = statistics_service._compute_min_max_duration([])

        assert min_dur is None
        assert max_dur is None

    def test_compute_min_max_duration_with_zero_durations(self, statistics_service):
        """Test min/max duration when all runs have 0 duration."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=0.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=0.0,
            ),
        ]

        min_dur, max_dur = statistics_service._compute_min_max_duration(runs)

        assert min_dur == 0.0
        assert max_dur == 0.0


class TestComputeDurationByConclusion:
    """Test _compute_duration_by_conclusion() helper method."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_duration_by_conclusion_single_conclusion(self, statistics_service):
        """Test duration by conclusion with single conclusion type."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=60.0,
            ),
        ]

        by_conclusion = statistics_service._compute_duration_by_conclusion(runs)

        assert by_conclusion["success"] == 55.0

    def test_compute_duration_by_conclusion_multiple_conclusions(self, statistics_service):
        """Test duration by conclusion with multiple conclusion types."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=80.0,
            ),
        ]

        by_conclusion = statistics_service._compute_duration_by_conclusion(runs)

        assert by_conclusion["success"] == 50.0
        assert by_conclusion["failure"] == 80.0

    def test_compute_duration_by_conclusion_with_none(self, statistics_service):
        """Test duration by conclusion with None conclusions."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.IN_PROGRESS,
                conclusion=None,
                created_at=now,
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=30.0,
            ),
        ]

        by_conclusion = statistics_service._compute_duration_by_conclusion(runs)

        assert by_conclusion[None] == 30.0

    def test_compute_duration_by_conclusion_empty_list(self, statistics_service):
        """Test duration by conclusion with empty list."""
        by_conclusion = statistics_service._compute_duration_by_conclusion([])

        assert by_conclusion == {}


class TestComputeAttemptStatistics:
    """Test _compute_attempt_statistics() helper method."""

    @pytest.fixture
    def mock_run_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_attempt_service(self):
        return MagicMock()

    @pytest.fixture
    def statistics_service(self, mock_run_service, mock_attempt_service):
        return WorkflowStatisticsService(mock_run_service, mock_attempt_service)

    def test_compute_attempt_statistics_with_attempts(self, statistics_service, mock_attempt_service):
        """Test attempt statistics when runs have attempts."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
        ]

        attempts = [
            WorkflowRunAttempt(
                id="attempt1",
                run_id="run1",
                attempt_number=1,
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                started_at=now,
                completed_at=now,
                duration_seconds=50.0,
            ),
        ]

        mock_attempt_service.filter_by_run_id.return_value = attempts

        total, with_attempts, without_attempts = statistics_service._compute_attempt_statistics(runs)

        assert total == 1
        assert with_attempts == 1
        assert without_attempts == 0

    def test_compute_attempt_statistics_without_attempts(self, statistics_service, mock_attempt_service):
        """Test attempt statistics when runs have no attempts."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
        ]

        mock_attempt_service.filter_by_run_id.return_value = []

        total, with_attempts, without_attempts = statistics_service._compute_attempt_statistics(runs)

        assert total == 0
        assert with_attempts == 0
        assert without_attempts == 1

    def test_compute_attempt_statistics_mixed(self, statistics_service, mock_attempt_service):
        """Test attempt statistics with mixed runs (some with, some without attempts)."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=50.0,
            ),
            WorkflowRun(
                id="run2",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=2,
                commit_sha="def456",
                duration_seconds=60.0,
            ),
        ]

        def filter_by_run_id_side_effect(run_id):
            if run_id == "run1":
                return [
                    WorkflowRunAttempt(
                        id="attempt1",
                        run_id="run1",
                        attempt_number=1,
                        status=WorkflowStatus.COMPLETED,
                        conclusion=WorkflowConclusion.SUCCESS,
                        started_at=now,
                        completed_at=now,
                        duration_seconds=50.0,
                    ),
                ]
            else:
                return []

        mock_attempt_service.filter_by_run_id.side_effect = filter_by_run_id_side_effect

        total, with_attempts, without_attempts = statistics_service._compute_attempt_statistics(runs)

        assert total == 1
        assert with_attempts == 1
        assert without_attempts == 1

    def test_compute_attempt_statistics_multiple_attempts_per_run(self, statistics_service, mock_attempt_service):
        """Test attempt statistics when a single run has multiple attempts."""
        now = datetime.now()
        runs = [
            WorkflowRun(
                id="run1",
                workflow_name="test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=now,
                updated_at=now,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=100.0,
            ),
        ]

        attempts = [
            WorkflowRunAttempt(
                id="attempt1",
                run_id="run1",
                attempt_number=1,
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                started_at=now,
                completed_at=now,
                duration_seconds=50.0,
            ),
            WorkflowRunAttempt(
                id="attempt2",
                run_id="run1",
                attempt_number=2,
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                started_at=now,
                completed_at=now,
                duration_seconds=50.0,
            ),
        ]

        mock_attempt_service.filter_by_run_id.return_value = attempts

        total, with_attempts, without_attempts = statistics_service._compute_attempt_statistics(runs)

        assert total == 2
        assert with_attempts == 1
        assert without_attempts == 0

    def test_compute_attempt_statistics_empty_runs(self, statistics_service):
        """Test attempt statistics with empty run list."""
        total, with_attempts, without_attempts = statistics_service._compute_attempt_statistics([])

        assert total == 0
        assert with_attempts == 0
        assert without_attempts == 0
