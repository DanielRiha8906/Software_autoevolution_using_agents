import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService


def _make_run(run_id: str = "run-1", branch: str = "main", duration_seconds: float = 0.0) -> WorkflowRun:
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
        duration_seconds=duration_seconds,
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


def test_add_and_list_with_duration(service):
    run = _make_run(duration_seconds=45.5)
    service.add_workflow_run(run)
    assert service.list_runs() == [run]
    assert service.list_runs()[0].duration_seconds == 45.5


def test_workflow_run_validation_negative_duration():
    with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
        WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=-5.0,
        )


# Tests for filter_runs() method

def test_filter_runs_duration_min(service):
    r1 = _make_run("r1", duration_seconds=10.0)
    r2 = _make_run("r2", duration_seconds=20.0)
    r3 = _make_run("r3", duration_seconds=30.0)
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    assert service.filter_runs(duration_min=15.0) == [r2, r3]
    assert service.filter_runs(duration_min=10.0) == [r1, r2, r3]
    assert service.filter_runs(duration_min=40.0) == []


def test_filter_runs_duration_max(service):
    r1 = _make_run("r1", duration_seconds=10.0)
    r2 = _make_run("r2", duration_seconds=20.0)
    r3 = _make_run("r3", duration_seconds=30.0)
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    assert service.filter_runs(duration_max=25.0) == [r1, r2]
    assert service.filter_runs(duration_max=30.0) == [r1, r2, r3]
    assert service.filter_runs(duration_max=5.0) == []


def test_filter_runs_duration_range(service):
    r1 = _make_run("r1", duration_seconds=10.0)
    r2 = _make_run("r2", duration_seconds=20.0)
    r3 = _make_run("r3", duration_seconds=30.0)
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    assert service.filter_runs(duration_min=15.0, duration_max=25.0) == [r2]
    assert service.filter_runs(duration_min=10.0, duration_max=30.0) == [r1, r2, r3]


def test_filter_runs_created_after(service):
    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    # created_after is exclusive
    assert service.filter_runs(created_after=base_time) == [r2]


def test_filter_runs_created_before(service):
    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    # created_before is exclusive
    assert service.filter_runs(created_before=base_time) == [r1]


def test_filter_runs_updated_after(service):
    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, 10, 30, 0, tzinfo=timezone.utc),
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc),
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r3 = WorkflowRun(
        id="r3",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    # updated_after is exclusive and only applies if updated_at is not None
    assert service.filter_runs(updated_after=base_time) == [r2]


def test_filter_runs_updated_before(service):
    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, 10, 30, 0, tzinfo=timezone.utc),
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc),
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    r3 = WorkflowRun(
        id="r3",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    # updated_before is exclusive and only applies if updated_at is not None
    assert service.filter_runs(updated_before=base_time) == [r1]


def test_filter_runs_has_attempts_true(service):
    from src.models.workflow_run_attempt import WorkflowRunAttempt
    from src.models.workflow_attempt_status import WorkflowAttemptStatus

    r1 = _make_run("r1")
    r2 = _make_run("r2")
    r3 = _make_run("r3")

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    # Add attempts to r1 and r2
    attempt1 = WorkflowRunAttempt(
        id=1,
        run_id=int("1"),
        attempt_number=1,
        status=WorkflowAttemptStatus.IN_PROGRESS,
        conclusion=None,
        created_at=datetime.now(timezone.utc),
        duration_seconds=None,
    )
    attempt2 = WorkflowRunAttempt(
        id=2,
        run_id=int("2"),
        attempt_number=1,
        status=WorkflowAttemptStatus.COMPLETED,
        conclusion=None,
        created_at=datetime.now(timezone.utc),
        duration_seconds=None,
    )
    r1.attempts.append(attempt1)
    r2.attempts.append(attempt2)

    result = service.filter_runs(has_attempts=True)
    assert len(result) == 2
    assert r1 in result
    assert r2 in result
    assert r3 not in result


def test_filter_runs_has_attempts_false(service):
    from src.models.workflow_run_attempt import WorkflowRunAttempt
    from src.models.workflow_attempt_status import WorkflowAttemptStatus

    r1 = _make_run("r1")
    r2 = _make_run("r2")
    r3 = _make_run("r3")

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    # Add attempt only to r1
    attempt1 = WorkflowRunAttempt(
        id=1,
        run_id=int("1"),
        attempt_number=1,
        status=WorkflowAttemptStatus.IN_PROGRESS,
        conclusion=None,
        created_at=datetime.now(timezone.utc),
        duration_seconds=None,
    )
    r1.attempts.append(attempt1)

    result = service.filter_runs(has_attempts=False)
    assert len(result) == 2
    assert r2 in result
    assert r3 in result
    assert r1 not in result


def test_filter_runs_multi_filter_branch_status_duration(service):
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=10.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.IN_PROGRESS,
        conclusion=None,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=2,
        commit_sha="abc124",
        duration_seconds=20.0,
    )
    r3 = WorkflowRun(
        id="r3",
        workflow_name="CI",
        branch="dev",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=3,
        commit_sha="abc125",
        duration_seconds=15.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    result = service.filter_runs(
        branch="main",
        status=WorkflowStatus.COMPLETED,
        duration_min=5.0,
    )
    assert result == [r1]


def test_filter_runs_date_range_has_attempts(service):
    from src.models.workflow_run_attempt import WorkflowRunAttempt
    from src.models.workflow_attempt_status import WorkflowAttemptStatus

    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=10.0,
    )
    r2 = WorkflowRun(
        id="r2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        run_number=2,
        commit_sha="abc124",
        duration_seconds=20.0,
    )
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    # Add attempt only to r2
    attempt = WorkflowRunAttempt(
        id=1,
        run_id=int("2"),
        attempt_number=1,
        status=WorkflowAttemptStatus.COMPLETED,
        conclusion=None,
        created_at=datetime.now(timezone.utc),
        duration_seconds=None,
    )
    r2.attempts.append(attempt)

    result = service.filter_runs(
        created_after=base_time,
        has_attempts=True,
    )
    assert result == [r2]


def test_filter_runs_all_none_returns_all(service):
    r1 = _make_run("r1")
    r2 = _make_run("r2")
    r3 = _make_run("r3")
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    result = service.filter_runs()
    assert result == [r1, r2, r3]


def test_filter_runs_no_matches(service):
    r1 = _make_run("r1", branch="main")
    r2 = _make_run("r2", branch="dev")
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    result = service.filter_runs(branch="nonexistent")
    assert result == []


def test_filter_runs_boundary_inclusive(service):
    r1 = _make_run("r1", duration_seconds=10.0)
    r2 = _make_run("r2", duration_seconds=20.0)
    r3 = _make_run("r3", duration_seconds=30.0)
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    # Test that boundaries are inclusive
    assert service.filter_runs(duration_min=10.0, duration_max=20.0) == [r1, r2]


def test_filter_runs_boundary_exclusive_dates(service):
    base_time = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    r1 = WorkflowRun(
        id="r1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=base_time,
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
    service.add_workflow_run(r1)
    # created_after and created_before are exclusive
    assert service.filter_runs(created_after=base_time) == []
    assert service.filter_runs(created_before=base_time) == []


# CLI integration tests for ISO8601 parsing

def test_parse_iso8601_with_z_suffix():
    from src.cli.workflow_cli import _parse_iso8601

    result = _parse_iso8601("2024-06-01T12:00:00Z")
    assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_iso8601_with_plus_format():
    from src.cli.workflow_cli import _parse_iso8601

    result = _parse_iso8601("2024-06-01T12:00:00+00:00")
    assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_iso8601_invalid_format():
    from src.cli.workflow_cli import _parse_iso8601

    with pytest.raises(ValueError, match="Invalid ISO 8601 timestamp"):
        _parse_iso8601("not-a-date")
