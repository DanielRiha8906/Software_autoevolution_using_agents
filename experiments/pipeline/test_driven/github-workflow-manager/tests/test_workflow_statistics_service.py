import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from dataclasses import is_dataclass

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_statistics_report import WorkflowStatisticsReport
from src.services.workflow_statistics_service import WorkflowStatisticsService
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService


CEST = timezone(timedelta(hours=2))


def _make_run(
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 100.0,
) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


def _make_attempt(run_id: int = 1, attempt_number: int = 1) -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=attempt_number,
        run_id=run_id,
        attempt_number=attempt_number,
        status="completed",
        conclusion="success",
        created_at=datetime.now(CEST),
    )


@pytest.fixture
def workflow_run_service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


@pytest.fixture
def statistics_service(workflow_run_service):
    return WorkflowStatisticsService(workflow_run_service)


def test_statistics_service_exists(statistics_service):
    """Test that WorkflowStatisticsService can be instantiated."""
    assert statistics_service is not None


def test_report_is_dataclass():
    """Test that WorkflowStatisticsReport is a dataclass."""
    assert is_dataclass(WorkflowStatisticsReport)


def test_count_by_conclusion(workflow_run_service, statistics_service):
    """Test that count_by_conclusion correctly counts terminal runs by conclusion."""
    # Add multiple runs with different conclusions
    workflow_run_service.add_workflow_run(_make_run("run-1", conclusion=WorkflowConclusion.SUCCESS))
    workflow_run_service.add_workflow_run(_make_run("run-2", conclusion=WorkflowConclusion.SUCCESS))
    workflow_run_service.add_workflow_run(_make_run("run-3", conclusion=WorkflowConclusion.FAILURE))
    workflow_run_service.add_workflow_run(_make_run("run-4", conclusion=WorkflowConclusion.CANCELLED))

    report = statistics_service.compute()

    assert report.count_by_conclusion == {
        WorkflowConclusion.SUCCESS.value: 2,
        WorkflowConclusion.FAILURE.value: 1,
        WorkflowConclusion.CANCELLED.value: 1,
    }


def test_count_by_conclusion_ignores_non_terminal_runs(workflow_run_service, statistics_service):
    """Test that count_by_conclusion only counts COMPLETED runs."""
    # Add a mix of terminal and non-terminal runs
    workflow_run_service.add_workflow_run(
        _make_run("run-1", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    )
    workflow_run_service.add_workflow_run(
        _make_run("run-2", status=WorkflowStatus.IN_PROGRESS, conclusion=None)
    )
    workflow_run_service.add_workflow_run(
        _make_run("run-3", status=WorkflowStatus.QUEUED, conclusion=None)
    )

    report = statistics_service.compute()

    # Should only count the COMPLETED run
    assert report.count_by_conclusion == {WorkflowConclusion.SUCCESS.value: 1}


def test_count_by_conclusion_ignores_null_conclusions(workflow_run_service, statistics_service):
    """Test that count_by_conclusion ignores COMPLETED runs with null conclusions."""
    workflow_run_service.add_workflow_run(
        _make_run("run-1", status=WorkflowStatus.COMPLETED, conclusion=None)
    )
    workflow_run_service.add_workflow_run(
        _make_run("run-2", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    )

    report = statistics_service.compute()

    # Should only count run-2, run-1 is skipped due to null conclusion
    assert report.count_by_conclusion == {WorkflowConclusion.SUCCESS.value: 1}


def test_average_duration(workflow_run_service, statistics_service):
    """Test that avg_duration_seconds calculates the correct average."""
    workflow_run_service.add_workflow_run(_make_run("run-1", duration_seconds=100.0))
    workflow_run_service.add_workflow_run(_make_run("run-2", duration_seconds=200.0))
    workflow_run_service.add_workflow_run(_make_run("run-3", duration_seconds=300.0))

    report = statistics_service.compute()

    assert report.avg_duration_seconds == 200.0


def test_average_duration_with_single_run(workflow_run_service, statistics_service):
    """Test avg_duration_seconds with a single run."""
    workflow_run_service.add_workflow_run(_make_run("run-1", duration_seconds=150.0))

    report = statistics_service.compute()

    assert report.avg_duration_seconds == 150.0


def test_average_duration_empty_data(workflow_run_service, statistics_service):
    """Test that avg_duration_seconds returns 0.0 for empty data."""
    report = statistics_service.compute()

    assert report.avg_duration_seconds == 0.0


def test_min_max_duration(workflow_run_service, statistics_service):
    """Test that min_duration_seconds and max_duration_seconds are calculated correctly."""
    workflow_run_service.add_workflow_run(_make_run("run-1", duration_seconds=50.0))
    workflow_run_service.add_workflow_run(_make_run("run-2", duration_seconds=150.0))
    workflow_run_service.add_workflow_run(_make_run("run-3", duration_seconds=300.0))

    report = statistics_service.compute()

    assert report.min_duration_seconds == 50.0
    assert report.max_duration_seconds == 300.0


def test_min_max_duration_single_run(workflow_run_service, statistics_service):
    """Test min/max with a single run."""
    workflow_run_service.add_workflow_run(_make_run("run-1", duration_seconds=100.0))

    report = statistics_service.compute()

    assert report.min_duration_seconds == 100.0
    assert report.max_duration_seconds == 100.0


def test_min_max_duration_empty_data(workflow_run_service, statistics_service):
    """Test that min/max duration return 0.0 for empty data."""
    report = statistics_service.compute()

    assert report.min_duration_seconds == 0.0
    assert report.max_duration_seconds == 0.0


def test_average_attempts_per_run(workflow_run_service, statistics_service):
    """Test that avg_attempts_per_run calculates correctly with AttemptService."""
    # Add runs with numeric IDs for attempt tracking
    workflow_run_service.add_workflow_run(_make_run("1", duration_seconds=100.0))
    workflow_run_service.add_workflow_run(_make_run("2", duration_seconds=100.0))
    workflow_run_service.add_workflow_run(_make_run("3", duration_seconds=100.0))

    # Create attempt service with attempts
    attempt_service = AttemptService()
    attempt_service.create(_make_attempt(run_id=1, attempt_number=1))
    attempt_service.create(_make_attempt(run_id=1, attempt_number=2))
    attempt_service.create(_make_attempt(run_id=2, attempt_number=1))
    # run_id=3 has 0 attempts

    report = statistics_service.compute(attempt_service)

    # (2 + 1 + 0) / 3 = 1.0
    assert report.avg_attempts_per_run == 1.0


def test_average_attempts_per_run_includes_zero_attempt_runs(
    workflow_run_service, statistics_service
):
    """Test that avg_attempts_per_run includes runs with 0 attempts in denominator."""
    workflow_run_service.add_workflow_run(_make_run("1", duration_seconds=100.0))
    workflow_run_service.add_workflow_run(_make_run("2", duration_seconds=100.0))

    attempt_service = AttemptService()
    attempt_service.create(_make_attempt(run_id=1, attempt_number=1))
    attempt_service.create(_make_attempt(run_id=1, attempt_number=2))
    # run_id=2 has 0 attempts

    report = statistics_service.compute(attempt_service)

    # (2 + 0) / 2 = 1.0
    assert report.avg_attempts_per_run == 1.0


def test_average_attempts_per_run_without_service(workflow_run_service, statistics_service):
    """Test that avg_attempts_per_run is 0.0 when attempt_service is None."""
    workflow_run_service.add_workflow_run(_make_run("1", duration_seconds=100.0))
    workflow_run_service.add_workflow_run(_make_run("2", duration_seconds=100.0))

    report = statistics_service.compute(attempt_service=None)

    # When no attempt service provided, should be 0.0
    assert report.avg_attempts_per_run == 0.0


def test_average_attempts_per_run_empty_data(workflow_run_service, statistics_service):
    """Test that avg_attempts_per_run is 0.0 for empty data."""
    attempt_service = AttemptService()

    report = statistics_service.compute(attempt_service)

    assert report.avg_attempts_per_run == 0.0


def test_empty_data_returns_zeroed_report(workflow_run_service, statistics_service):
    """Test that empty data returns a zeroed report."""
    report = statistics_service.compute()

    assert report.count_by_conclusion == {}
    assert report.avg_duration_seconds == 0.0
    assert report.min_duration_seconds == 0.0
    assert report.max_duration_seconds == 0.0
    assert report.avg_attempts_per_run == 0.0


def test_comprehensive_statistics_report(workflow_run_service, statistics_service):
    """Test a comprehensive report with mixed data."""
    # Add runs with various properties
    workflow_run_service.add_workflow_run(
        _make_run("1", conclusion=WorkflowConclusion.SUCCESS, duration_seconds=100.0)
    )
    workflow_run_service.add_workflow_run(
        _make_run("2", conclusion=WorkflowConclusion.SUCCESS, duration_seconds=200.0)
    )
    workflow_run_service.add_workflow_run(
        _make_run("3", conclusion=WorkflowConclusion.FAILURE, duration_seconds=150.0)
    )

    # Add attempts for runs
    attempt_service = AttemptService()
    attempt_service.create(_make_attempt(run_id=1, attempt_number=1))
    attempt_service.create(_make_attempt(run_id=2, attempt_number=1))
    attempt_service.create(_make_attempt(run_id=2, attempt_number=2))

    report = statistics_service.compute(attempt_service)

    assert report.count_by_conclusion[WorkflowConclusion.SUCCESS.value] == 2
    assert report.count_by_conclusion[WorkflowConclusion.FAILURE.value] == 1
    assert report.avg_duration_seconds == 150.0
    assert report.min_duration_seconds == 100.0
    assert report.max_duration_seconds == 200.0
    assert report.avg_attempts_per_run == (1 + 2 + 0) / 3  # 1.0
