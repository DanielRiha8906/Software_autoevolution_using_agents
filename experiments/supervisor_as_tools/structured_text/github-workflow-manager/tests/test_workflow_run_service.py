import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService


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


# Duration Range Tests
def test_filter_by_duration_range(service):
    r1 = _make_run("r1")
    r1.duration_seconds = 10.0
    r2 = _make_run("r2")
    r2.duration_seconds = 20.0
    r3 = _make_run("r3")
    r3.duration_seconds = 30.0

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    result = service.filter_by_duration_range(15.0, 25.0)
    assert result == [r2]


def test_filter_by_duration_min_only(service):
    r1 = _make_run("r1")
    r1.duration_seconds = 5.0
    r2 = _make_run("r2")
    r2.duration_seconds = 15.0

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    result = service.filter_by_duration_range(min_duration_seconds=10.0)
    assert result == [r2]


def test_filter_by_duration_max_only(service):
    r1 = _make_run("r1")
    r1.duration_seconds = 5.0
    r2 = _make_run("r2")
    r2.duration_seconds = 15.0

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    result = service.filter_by_duration_range(max_duration_seconds=10.0)
    assert result == [r1]


def test_filter_by_duration_empty_result(service):
    r1 = _make_run("r1")
    r1.duration_seconds = 5.0
    service.add_workflow_run(r1)

    result = service.filter_by_duration_range(10.0, 20.0)
    assert result == []


def test_filter_by_duration_negative_min_raises(service):
    with pytest.raises(ValueError, match="min_duration_seconds must be non-negative"):
        service.filter_by_duration_range(-1.0, 10.0)


def test_filter_by_duration_negative_max_raises(service):
    with pytest.raises(ValueError, match="max_duration_seconds must be non-negative"):
        service.filter_by_duration_range(0.0, -1.0)


def test_filter_by_duration_min_gt_max_raises(service):
    with pytest.raises(ValueError, match="min_duration_seconds .* must be <="):
        service.filter_by_duration_range(20.0, 10.0)


# Created Datetime Tests
def test_filter_by_created_after(service):
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before
    r2 = _make_run("r2")
    r2.created_at = after

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    result = service.filter_by_created_after(now)
    assert result == [r2]


def test_filter_by_created_before(service):
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before
    r2 = _make_run("r2")
    r2.created_at = after

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    result = service.filter_by_created_before(now)
    assert result == [r1]


# Updated Datetime Tests
def test_filter_by_updated_after(service):
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.updated_at = before
    r2 = _make_run("r2")
    r2.updated_at = after
    r3 = _make_run("r3")
    r3.updated_at = None

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    result = service.filter_by_updated_after(now)
    assert result == [r2]


def test_filter_by_updated_before(service):
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.updated_at = before
    r2 = _make_run("r2")
    r2.updated_at = after
    r3 = _make_run("r3")
    r3.updated_at = None

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    result = service.filter_by_updated_before(now)
    assert result == [r1]


# Has Attempts Tests
def test_filter_by_has_attempts_true(service):
    r1 = _make_run("1")
    r2 = _make_run("2")

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    attempt_service = MagicMock(spec=AttemptService)
    attempt_service.get_attempts_by_run_id.side_effect = lambda run_id: [
        MagicMock()
    ] if run_id == 1 else []

    result = service.filter_by_has_attempts(attempt_service, has_attempts=True)
    assert result == [r1]


def test_filter_by_has_attempts_false(service):
    r1 = _make_run("1")
    r2 = _make_run("2")

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    attempt_service = MagicMock(spec=AttemptService)
    attempt_service.get_attempts_by_run_id.side_effect = lambda run_id: [
        MagicMock()
    ] if run_id == 1 else []

    result = service.filter_by_has_attempts(attempt_service, has_attempts=False)
    assert result == [r2]


# Compound Filter Tests
def test_filter_compound_duration_and_status(service):
    r1 = _make_run("r1")
    r1.duration_seconds = 10.0
    r1.status = WorkflowStatus.COMPLETED

    r2 = _make_run("r2")
    r2.duration_seconds = 20.0
    r2.status = WorkflowStatus.COMPLETED

    r3 = _make_run("r3")
    r3.duration_seconds = 5.0
    r3.status = WorkflowStatus.QUEUED

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    result = service.filter_runs(
        status=WorkflowStatus.COMPLETED,
        min_duration_seconds=15.0,
    )
    assert result == [r2]


# Timezone Tests
def test_filter_timestamps_with_tz_aware_utc(service):
    now_utc = datetime.now(timezone.utc)
    before = now_utc - timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before
    service.add_workflow_run(r1)

    # Query with UTC timezone-aware datetime
    result = service.filter_by_created_after(now_utc)
    assert result == []

    result = service.filter_by_created_before(now_utc)
    assert result == [r1]


def test_filter_timestamps_with_naive_datetime(service):
    now_utc = datetime.now(timezone.utc)
    before_utc = now_utc - timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before_utc
    service.add_workflow_run(r1)

    # Query with naive datetime (should assume UTC)
    now_naive = now_utc.replace(tzinfo=None)
    result = service.filter_by_created_before(now_naive)
    assert result == [r1]


def test_filter_runs_with_has_attempts_without_service_raises(service):
    with pytest.raises(ValueError, match="attempt_service must be provided"):
        service.filter_runs(has_attempts=True)
