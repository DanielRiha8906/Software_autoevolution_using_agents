import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_service import WorkflowRunService


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    duration_seconds: float = 100.0,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
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


@pytest.fixture
def attempt_service():
    service = MagicMock()
    service.list_attempts.return_value = []
    return service


class TestDurationFiltering:
    def test_filter_by_min_duration(self, service):
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=150.0)
        r3 = _make_run("r3", duration_seconds=200.0)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_duration_range(min_seconds=100.0)
        assert len(result) == 2
        assert r2 in result
        assert r3 in result
        assert r1 not in result

    def test_filter_by_max_duration(self, service):
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=150.0)
        r3 = _make_run("r3", duration_seconds=200.0)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_duration_range(max_seconds=100.0)
        assert len(result) == 1
        assert r1 in result
        assert r2 not in result
        assert r3 not in result

    def test_filter_by_duration_range(self, service):
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=150.0)
        r3 = _make_run("r3", duration_seconds=200.0)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_duration_range(min_seconds=100.0, max_seconds=180.0)
        assert len(result) == 1
        assert r2 in result

    def test_filter_by_duration_empty_range(self, service):
        r1 = _make_run("r1", duration_seconds=50.0)
        service.add_workflow_run(r1)

        result = service.filter_by_duration_range(min_seconds=100.0, max_seconds=200.0)
        assert len(result) == 0


class TestTimestampFiltering:
    def test_filter_by_created_before(self, service):
        dt1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)

        r1 = _make_run("r1", created_at=dt1)
        r2 = _make_run("r2", created_at=dt2)
        r3 = _make_run("r3", created_at=dt3)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        cutoff = datetime(2026, 5, 2, 0, 0, 0, tzinfo=timezone.utc)
        result = service.filter_by_created_before(cutoff)
        assert len(result) == 1
        assert r1 in result

    def test_filter_by_created_after(self, service):
        dt1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)

        r1 = _make_run("r1", created_at=dt1)
        r2 = _make_run("r2", created_at=dt2)
        r3 = _make_run("r3", created_at=dt3)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        cutoff = datetime(2026, 5, 2, 0, 0, 0, tzinfo=timezone.utc)
        result = service.filter_by_created_after(cutoff)
        assert len(result) == 2
        assert r2 in result
        assert r3 in result

    def test_filter_by_updated_before(self, service):
        dt1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)

        r1 = _make_run("r1", updated_at=dt1)
        r2 = _make_run("r2", updated_at=dt2)
        r3 = _make_run("r3", updated_at=None)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        cutoff = datetime(2026, 5, 2, 0, 0, 0, tzinfo=timezone.utc)
        result = service.filter_by_updated_before(cutoff)
        assert len(result) == 1
        assert r1 in result

    def test_filter_by_updated_after(self, service):
        dt1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)

        r1 = _make_run("r1", updated_at=dt1)
        r2 = _make_run("r2", updated_at=dt2)
        r3 = _make_run("r3", updated_at=None)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        cutoff = datetime(2026, 5, 2, 0, 0, 0, tzinfo=timezone.utc)
        result = service.filter_by_updated_after(cutoff)
        assert len(result) == 1
        assert r2 in result


class TestAttemptFiltering:
    def test_filter_with_attempts(self, service, attempt_service):
        r1 = _make_run("run-1")
        r2 = _make_run("run-2")
        r3 = _make_run("run-3")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        # Only runs 1 and 2 have attempts
        attempt = MagicMock(spec=WorkflowRunAttempt)
        attempt.run_id = "run-1"
        attempt2 = MagicMock(spec=WorkflowRunAttempt)
        attempt2.run_id = "run-2"
        attempt_service.list_attempts.return_value = [attempt, attempt2]

        result = service.filter_with_attempts(attempt_service)
        assert len(result) == 2
        assert r1 in result
        assert r2 in result
        assert r3 not in result

    def test_filter_without_attempts(self, service, attempt_service):
        r1 = _make_run("run-1")
        r2 = _make_run("run-2")
        r3 = _make_run("run-3")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        # Only run 1 has an attempt
        attempt = MagicMock(spec=WorkflowRunAttempt)
        attempt.run_id = "run-1"
        attempt_service.list_attempts.return_value = [attempt]

        result = service.filter_without_attempts(attempt_service)
        assert len(result) == 2
        assert r2 in result
        assert r3 in result
        assert r1 not in result


class TestCompositeFiltering:
    def test_filter_runs_with_multiple_criteria(self, service, attempt_service):
        dt1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)

        r1 = _make_run("r1", "main", duration_seconds=50.0, created_at=dt1)
        r2 = _make_run("r2", "main", duration_seconds=150.0, created_at=dt2)
        r3 = _make_run("r3", "dev", duration_seconds=200.0, created_at=dt3)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        # Filter: branch=main AND duration >= 100 AND created after dt1
        result = service.filter_runs(
            attempt_service=attempt_service,
            branch="main",
            min_duration=100.0,
            created_after=datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        assert len(result) == 1
        assert r2 in result

    def test_filter_runs_no_matches(self, service, attempt_service):
        r1 = _make_run("r1", "main", duration_seconds=50.0)
        service.add_workflow_run(r1)

        result = service.filter_runs(
            attempt_service=attempt_service,
            min_duration=200.0,
        )
        assert len(result) == 0

    def test_filter_runs_with_attempts_flag(self, service, attempt_service):
        r1 = _make_run("run-1")
        r2 = _make_run("run-2")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        attempt = MagicMock(spec=WorkflowRunAttempt)
        attempt.run_id = "run-1"
        attempt_service.list_attempts.return_value = [attempt]

        result = service.filter_runs(
            attempt_service=attempt_service,
            has_attempts=True,
        )
        assert len(result) == 1
        assert r1 in result

    def test_filter_runs_without_attempts_flag(self, service, attempt_service):
        r1 = _make_run("run-1")
        r2 = _make_run("run-2")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        attempt = MagicMock(spec=WorkflowRunAttempt)
        attempt.run_id = "run-1"
        attempt_service.list_attempts.return_value = [attempt]

        result = service.filter_runs(
            attempt_service=attempt_service,
            has_attempts=False,
        )
        assert len(result) == 1
        assert r2 in result

    def test_filter_runs_requires_attempt_service_when_filtering_by_attempts(self, service):
        r1 = _make_run("r1")
        service.add_workflow_run(r1)

        with pytest.raises(ValueError, match="attempt_service is required"):
            service.filter_runs(has_attempts=True)

    def test_filter_runs_ignores_none_parameters(self, service, attempt_service):
        r1 = _make_run("r1")
        r2 = _make_run("r2")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        # All None parameters should return all runs
        result = service.filter_runs(
            attempt_service=attempt_service,
            branch=None,
            status=None,
            conclusion=None,
            min_duration=None,
            max_duration=None,
            created_before=None,
            created_after=None,
            updated_before=None,
            updated_after=None,
            has_attempts=None,
        )
        assert len(result) == 2
