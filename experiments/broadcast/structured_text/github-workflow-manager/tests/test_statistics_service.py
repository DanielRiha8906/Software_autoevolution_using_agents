import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.services.statistics_service import StatisticsService, WorkflowStatisticsReport


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 100.0,
) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


def _make_attempt(
    run_id: int = 1,
    attempt_number: int = 1,
    duration_seconds: float = 50.0,
) -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=1,
        run_id=run_id,
        attempt_number=attempt_number,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def workflow_run_service():
    storage = MagicMock()
    storage.load.return_value = []
    return WorkflowRunService(storage)


@pytest.fixture
def attempt_service():
    storage = MagicMock()
    storage.load.return_value = []
    return AttemptService(storage)


@pytest.fixture
def stats_service(workflow_run_service, attempt_service):
    return StatisticsService(workflow_run_service, attempt_service)


def test_compute_statistics_empty(stats_service):
    """Test statistics with no runs."""
    report = stats_service.compute_statistics()
    assert report.total_runs == 0
    assert report.conclusions_count == {}
    assert report.avg_duration_seconds == 0.0
    assert report.min_duration_seconds is None
    assert report.max_duration_seconds is None
    assert report.avg_attempts_per_run == 0.0


def test_compute_statistics_single_run(workflow_run_service, attempt_service):
    """Test statistics with one run."""
    run = _make_run(duration_seconds=100.0)
    workflow_run_service.add_workflow_run(run)

    stats_service = StatisticsService(workflow_run_service, attempt_service)
    report = stats_service.compute_statistics()

    assert report.total_runs == 1
    assert report.conclusions_count == {"success": 1}
    assert report.avg_duration_seconds == 100.0
    assert report.min_duration_seconds == 100.0
    assert report.max_duration_seconds == 100.0
    assert report.avg_attempts_per_run == 0.0


def test_compute_statistics_multiple_runs(workflow_run_service, attempt_service):
    """Test statistics with multiple runs."""
    run1 = _make_run(run_id="run-1", duration_seconds=100.0)
    run2 = _make_run(
        run_id="run-2",
        duration_seconds=200.0,
        conclusion=WorkflowConclusion.FAILURE,
    )
    run3 = _make_run(run_id="run-3", duration_seconds=150.0)

    workflow_run_service.add_workflow_run(run1)
    workflow_run_service.add_workflow_run(run2)
    workflow_run_service.add_workflow_run(run3)

    stats_service = StatisticsService(workflow_run_service, attempt_service)
    report = stats_service.compute_statistics()

    assert report.total_runs == 3
    assert report.conclusions_count == {"success": 2, "failure": 1}
    assert report.avg_duration_seconds == pytest.approx(150.0)
    assert report.min_duration_seconds == 100.0
    assert report.max_duration_seconds == 200.0


def test_compute_statistics_with_attempts(workflow_run_service, attempt_service):
    """Test statistics including attempts."""
    run1 = _make_run(run_id="1")
    run2 = _make_run(run_id="2")
    workflow_run_service.add_workflow_run(run1)
    workflow_run_service.add_workflow_run(run2)

    attempt1 = _make_attempt(run_id=1, attempt_number=1)
    attempt2 = _make_attempt(run_id=1, attempt_number=2)
    attempt3 = _make_attempt(run_id=2, attempt_number=1)

    attempt_service.add_workflow_attempt(attempt1)
    attempt_service.add_workflow_attempt(attempt2)
    attempt_service.add_workflow_attempt(attempt3)

    stats_service = StatisticsService(workflow_run_service, attempt_service)
    report = stats_service.compute_statistics()

    assert report.total_runs == 2
    assert report.avg_attempts_per_run == 1.5


def test_workflow_statistics_report_to_dict():
    """Test report conversion to dictionary."""
    report = WorkflowStatisticsReport(
        total_runs=5,
        conclusions_count={"success": 3, "failure": 2},
        avg_duration_seconds=120.5,
        min_duration_seconds=50.0,
        max_duration_seconds=200.0,
        avg_attempts_per_run=1.5,
    )

    report_dict = report.to_dict()

    assert report_dict["total_runs"] == 5
    assert report_dict["conclusions_count"] == {"success": 3, "failure": 2}
    assert report_dict["avg_duration_seconds"] == 120.5
    assert report_dict["min_duration_seconds"] == 50.0
    assert report_dict["max_duration_seconds"] == 200.0
    assert report_dict["avg_attempts_per_run"] == 1.5


def test_compute_statistics_all_conclusions(workflow_run_service, attempt_service):
    """Test statistics counts all conclusion types."""
    conclusions = [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
    ]

    for i, conclusion in enumerate(conclusions):
        run = _make_run(run_id=f"run-{i}", conclusion=conclusion)
        workflow_run_service.add_workflow_run(run)

    stats_service = StatisticsService(workflow_run_service, attempt_service)
    report = stats_service.compute_statistics()

    assert len(report.conclusions_count) == 4
    assert all(count == 1 for count in report.conclusions_count.values())
