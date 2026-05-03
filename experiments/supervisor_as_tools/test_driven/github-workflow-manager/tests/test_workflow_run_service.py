import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage


def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


def test_add_and_list(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.list_runs() == [run]


def test_add_duplicate_raises(service):
    run = _make_run()
    service.add_workflow_run(run)
    with pytest.raises(ValueError):
        service.add_workflow_run(run)


def test_get_run_detail(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.get_run_detail("run-1") is run
    assert service.get_run_detail("unknown") is None


def test_filter_by_branch(service):
    r1 = _make_run("r1", "main")
    r2 = _make_run("r2", "dev")
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    assert service.filter_by_branch("main") == [r1]
    assert service.filter_by_branch("dev") == [r2]


def test_filter_by_status(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.filter_by_status(WorkflowStatus.COMPLETED) == [run]
    assert service.filter_by_status(WorkflowStatus.QUEUED) == []


def test_filter_by_conclusion(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.filter_by_conclusion(WorkflowConclusion.SUCCESS) == [run]
    assert service.filter_by_conclusion(WorkflowConclusion.FAILURE) == []


# Task 05 - Query method tests

EARLY = datetime(2020, 1, 1, tzinfo=timezone.utc)
LATE = datetime(2030, 1, 1, tzinfo=timezone.utc)
CEST = timezone(timedelta(hours=2))


def _run(run_id, duration=10.0, created_at=None):
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=created_at or datetime.now(timezone.utc),
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
def svc(tmp_path):
    storage = WorkflowJsonStorage(str(tmp_path / "runs.json"))
    attempt_svc = AttemptService()
    service = WorkflowRunService(storage, attempt_svc)

    service.add_workflow_run(_run("r1", duration=5.0, created_at=EARLY))
    service.add_workflow_run(_run("r2", duration=50.0, created_at=LATE))

    # only r2 has attempts
    attempt_svc.create(_attempt("r2", 1))

    return service


def test_filter_by_duration_range(svc):
    results = svc.query(min_duration=10.0, max_duration=100.0)
    assert all(10.0 <= r.duration_seconds <= 100.0 for r in results)


def test_filter_by_created_before(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
    results = svc.query(created_before=cutoff)
    assert all(r.created_at < cutoff for r in results)


def test_filter_by_created_after(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
    results = svc.query(created_after=cutoff)
    assert all(r.created_at > cutoff for r in results)


def test_filter_runs_with_attempts(svc):
    results = svc.query(has_attempts=True)
    assert all(r.id == "r2" for r in results)


def test_filter_runs_without_attempts(svc):
    results = svc.query(has_attempts=False)
    assert all(r.id == "r1" for r in results)


def test_combined_filters(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
    results = svc.query(min_duration=1.0, created_before=cutoff, has_attempts=False)

    assert all(
        r.duration_seconds >= 1.0 and
        r.created_at < cutoff and
        r.id == "r1"
        for r in results
    )


def test_query_returns_list(svc):
    assert isinstance(svc.query(), list)


def test_no_match_returns_empty_list(svc):
    results = svc.query(min_duration=9999)
    assert results == []
