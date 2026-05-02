import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
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
        duration_seconds=0.0,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    run_service = WorkflowRunService(storage)
    attempt_service = AttemptService(run_service)
    return attempt_service, run_service


class TestAttemptServiceCreateAttemptSuccess:
    """Test successful creation of workflow attempts."""

    def test_create_single_attempt(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            duration_seconds=42.5,
        )

        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.duration_seconds == 42.5
        assert attempt.id == 1

    def test_create_multiple_attempts_for_same_run(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt1 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempt2 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        assert attempt1.attempt_number == 1
        assert attempt2.attempt_number == 2
        assert attempt1.id == 1
        assert attempt2.id == 2

    def test_create_attempt_without_duration(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert attempt.duration_seconds is None
        assert attempt.conclusion is None

    def test_create_attempt_with_zero_duration(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            duration_seconds=0.0,
        )

        assert attempt.duration_seconds == 0.0

    def test_create_attempt_persists_to_storage(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        retrieved_run = run_service.get_run_detail("run-1")
        assert len(retrieved_run.attempts) == 1
        assert retrieved_run.attempts[0].attempt_number == 1


class TestAttemptServiceCreateAttemptValidation:
    """Test validation rules for creating attempts."""

    def test_create_attempt_run_not_found_raises_error(self, service):
        attempt_service, _ = service

        with pytest.raises(ValueError, match="Run with id 'unknown-run' not found"):
            attempt_service.create_attempt(
                run_id="unknown-run",
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )

    def test_create_duplicate_attempt_number_raises_error(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(
            ValueError,
            match="Attempt with attempt_number 1 already exists for run 'run-1'",
        ):
            attempt_service.create_attempt(
                run_id="run-1",
                attempt_number=1,
                status="completed",
                conclusion="failure",
                created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            )

    def test_create_attempt_with_invalid_attempt_number_zero_raises_error(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            attempt_service.create_attempt(
                run_id="run-1",
                attempt_number=0,
                status="completed",
                conclusion="success",
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )

    def test_create_attempt_with_invalid_attempt_number_negative_raises_error(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            attempt_service.create_attempt(
                run_id="run-1",
                attempt_number=-1,
                status="completed",
                conclusion="success",
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )

    def test_create_attempt_auto_generates_id_starting_at_one(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert attempt.id == 1

    def test_create_attempt_auto_generates_id_incrementally(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt1 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempt2 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        attempt3 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=3,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        )

        assert attempt1.id == 1
        assert attempt2.id == 2
        assert attempt3.id == 3


class TestAttemptServiceGetAttemptsByRunId:
    """Test retrieving attempts by run ID."""

    def test_get_attempts_for_run_with_no_attempts_returns_empty_list(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempts = attempt_service.get_attempts_by_run_id("run-1")
        assert attempts == []

    def test_get_attempts_for_nonexistent_run_returns_empty_list(self, service):
        attempt_service, _ = service

        attempts = attempt_service.get_attempts_by_run_id("unknown-run")
        assert attempts == []

    def test_get_single_attempt_by_run_id(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        created_attempt = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempts = attempt_service.get_attempts_by_run_id("run-1")
        assert len(attempts) == 1
        assert attempts[0].attempt_number == 1
        assert attempts[0] == created_attempt

    def test_get_multiple_attempts_sorted_by_attempt_number(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=3,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        )

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        attempts = attempt_service.get_attempts_by_run_id("run-1")
        assert len(attempts) == 3
        assert attempts[0].attempt_number == 1
        assert attempts[1].attempt_number == 2
        assert attempts[2].attempt_number == 3

    def test_get_attempts_never_raises_exception(self, service):
        attempt_service, _ = service

        try:
            attempt_service.get_attempts_by_run_id("any-nonexistent-run")
        except Exception as e:
            pytest.fail(f"get_attempts_by_run_id should not raise exceptions, but raised {type(e).__name__}")

    def test_get_attempts_returns_new_list_not_reference(self, service):
        attempt_service, run_service = service
        run = _make_run()
        run_service.add_workflow_run(run)

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempts1 = attempt_service.get_attempts_by_run_id("run-1")
        attempts2 = attempt_service.get_attempts_by_run_id("run-1")

        assert attempts1 is not attempts2
        assert attempts1 == attempts2


class TestAttemptServiceMultipleRuns:
    """Test AttemptService with multiple runs."""

    def test_create_attempts_for_multiple_different_runs(self, service):
        attempt_service, run_service = service
        run1 = _make_run("run-1")
        run2 = _make_run("run-2")
        run_service.add_workflow_run(run1)
        run_service.add_workflow_run(run2)

        attempt1 = attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempt2 = attempt_service.create_attempt(
            run_id="run-2",
            attempt_number=1,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        run1_attempts = attempt_service.get_attempts_by_run_id("run-1")
        run2_attempts = attempt_service.get_attempts_by_run_id("run-2")

        assert len(run1_attempts) == 1
        assert len(run2_attempts) == 1
        assert run1_attempts[0].conclusion == "success"
        assert run2_attempts[0].conclusion == "failure"

    def test_duplicate_attempt_number_only_within_same_run(self, service):
        attempt_service, run_service = service
        run1 = _make_run("run-1")
        run2 = _make_run("run-2")
        run_service.add_workflow_run(run1)
        run_service.add_workflow_run(run2)

        attempt_service.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        attempt_service.create_attempt(
            run_id="run-2",
            attempt_number=1,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        run1_attempts = attempt_service.get_attempts_by_run_id("run-1")
        run2_attempts = attempt_service.get_attempts_by_run_id("run-2")

        assert run1_attempts[0].attempt_number == 1
        assert run2_attempts[0].attempt_number == 1
