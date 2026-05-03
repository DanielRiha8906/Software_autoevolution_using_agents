import dataclasses
import pytest
from datetime import datetime, timezone, timedelta
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.services.statistics_service import WorkflowStatisticsService
from src.storage.workflow_json_storage import WorkflowJsonStorage


CEST = timezone(timedelta(hours=2))


def _run(run_id, conclusion, duration):
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=None,
        commit_sha=None,
        duration_seconds=duration,
    )


def _attempt(run_id, attempt_number):
    return WorkflowRunAttempt(
        id=attempt_number,
        run_id=run_id,
        attempt_number=attempt_number,
        status="completed",
        conclusion="success",
        created_at=datetime.now(CEST),
    )


@pytest.fixture
def stats_svc(tmp_path):
    storage = WorkflowJsonStorage(str(tmp_path / "runs.json"))
    run_svc = WorkflowRunService(storage, AttemptService())
    attempt_svc = run_svc.attempt_service

    run_svc.add_workflow_run(_run("r1", WorkflowConclusion.SUCCESS, 10.0))
    run_svc.add_workflow_run(_run("r2", WorkflowConclusion.FAILURE, 30.0))
    run_svc.add_workflow_run(_run("r3", WorkflowConclusion.SUCCESS, 20.0))

    # attempts for r2 only
    attempt_svc.create(_attempt("r2", 1))
    attempt_svc.create(_attempt("r2", 2))

    return WorkflowStatisticsService(run_svc)


def test_statistics_service_exists(stats_svc):
    assert stats_svc is not None


def test_report_is_dataclass(stats_svc):
    report = stats_svc.compute()
    assert dataclasses.is_dataclass(report)


def test_count_by_conclusion(stats_svc):
    report = stats_svc.compute()
    assert report.count_by_conclusion[WorkflowConclusion.SUCCESS] == 2
    assert report.count_by_conclusion[WorkflowConclusion.FAILURE] == 1


def test_average_duration(stats_svc):
    report = stats_svc.compute()
    assert report.avg_duration_seconds == pytest.approx(20.0)


def test_min_max_duration(stats_svc):
    report = stats_svc.compute()
    assert report.min_duration_seconds == pytest.approx(10.0)
    assert report.max_duration_seconds == pytest.approx(30.0)


def test_average_attempts_per_run(stats_svc):
    report = stats_svc.compute()
    assert report.avg_attempts_per_run == pytest.approx(2 / 3, rel=1e-3)


def test_empty_data_returns_zeroed_report(tmp_path):
    storage = WorkflowJsonStorage(str(tmp_path / "runs.json"))
    run_svc = WorkflowRunService(storage, AttemptService())
    report = WorkflowStatisticsService(run_svc).compute()

    assert report.avg_duration_seconds == 0
    assert report.min_duration_seconds == 0
    assert report.max_duration_seconds == 0
    assert report.avg_attempts_per_run == 0
