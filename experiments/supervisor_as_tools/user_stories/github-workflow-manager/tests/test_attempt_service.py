import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_attempt_status import WorkflowAttemptStatus
from src.models.workflow_attempt_conclusion import WorkflowAttemptConclusion
from src.services.attempt_service import AttemptService
from src.services.workflow_run_service import WorkflowRunService


def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
    """Helper to create a WorkflowRun for testing."""
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
        attempts=[],
    )


def _make_attempt(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: WorkflowAttemptStatus = WorkflowAttemptStatus.COMPLETED,
    conclusion: WorkflowAttemptConclusion = WorkflowAttemptConclusion.SUCCESS,
    created_at: datetime = None,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt for testing."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


def _make_attempt_dict(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: str = None,
    duration_seconds: float = None,
) -> dict:
    """Helper to create an attempt data dict for testing."""
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    return {
        "id": id,
        "run_id": run_id,
        "attempt_number": attempt_number,
        "status": status,
        "conclusion": conclusion,
        "created_at": created_at,
        "duration_seconds": duration_seconds,
    }


@pytest.fixture
def run_service():
    """Fixture providing a WorkflowRunService with mocked storage."""
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


@pytest.fixture
def attempt_service(run_service):
    """Fixture providing an AttemptService."""
    return AttemptService(run_service)


class TestCreateAttempt:
    """Tests for AttemptService.create_attempt()"""

    def test_create_attempt_success(self, attempt_service, run_service):
        """Happy path: create an attempt in an existing run."""
        # Setup: add a run
        run = _make_run("run-1")
        run_service.add_workflow_run(run)

        # Execute: create an attempt
        attempt_data = _make_attempt_dict(
            id=1,
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
        )
        result = attempt_service.create_attempt("run-1", attempt_data)

        # Assert
        assert result.id == 1
        assert result.attempt_number == 1
        assert result.status == WorkflowAttemptStatus.COMPLETED
        assert result.conclusion == WorkflowAttemptConclusion.SUCCESS
        # Verify it was added to the run
        updated_run = run_service.get_run_detail("run-1")
        assert len(updated_run.attempts) == 1
        assert updated_run.attempts[0].attempt_number == 1

    def test_create_attempt_duplicate_number(self, attempt_service, run_service):
        """Same run, duplicate attempt_number raises ValueError."""
        # Setup: add a run with an existing attempt
        run = _make_run("run-1")
        existing_attempt = _make_attempt(attempt_number=1)
        run.attempts.append(existing_attempt)
        run_service.add_workflow_run(run)

        # Execute & Assert: attempt to add duplicate
        attempt_data = _make_attempt_dict(
            id=2,
            attempt_number=1,  # Same as existing
            status="completed",
        )
        with pytest.raises(
            ValueError, match="Attempt number 1 already exists in run 'run-1'"
        ):
            attempt_service.create_attempt("run-1", attempt_data)

    def test_create_attempt_nonexistent_run(self, attempt_service):
        """Attempt to add to non-existent run raises ValueError."""
        attempt_data = _make_attempt_dict()
        with pytest.raises(ValueError, match="Run with id 'unknown' not found"):
            attempt_service.create_attempt("unknown", attempt_data)

    def test_create_attempt_multiple_different_numbers(
        self, attempt_service, run_service
    ):
        """Create multiple attempts with different numbers in same run."""
        # Setup
        run = _make_run("run-1")
        run_service.add_workflow_run(run)

        # Execute: create first attempt
        attempt_1_data = _make_attempt_dict(id=1, attempt_number=1)
        result_1 = attempt_service.create_attempt("run-1", attempt_1_data)
        assert result_1.attempt_number == 1

        # Execute: create second attempt
        attempt_2_data = _make_attempt_dict(id=2, attempt_number=2)
        result_2 = attempt_service.create_attempt("run-1", attempt_2_data)
        assert result_2.attempt_number == 2

        # Assert: both are in the run
        updated_run = run_service.get_run_detail("run-1")
        assert len(updated_run.attempts) == 2


class TestGetAttemptsByRun:
    """Tests for AttemptService.get_attempts_by_run()"""

    def test_get_attempts_by_run_success(self, attempt_service, run_service):
        """Get all attempts for a run with multiple attempts."""
        # Setup
        run = _make_run("run-1")
        attempt_1 = _make_attempt(id=1, attempt_number=2)
        attempt_2 = _make_attempt(id=2, attempt_number=1)
        attempt_3 = _make_attempt(id=3, attempt_number=3)
        run.attempts = [attempt_1, attempt_2, attempt_3]
        run_service.add_workflow_run(run)

        # Execute
        results = attempt_service.get_attempts_by_run("run-1")

        # Assert
        assert len(results) == 3
        assert results[0].id == 1
        assert results[1].id == 2
        assert results[2].id == 3

    def test_get_attempts_by_run_empty(self, attempt_service, run_service):
        """Get attempts for run with no attempts returns empty list."""
        # Setup
        run = _make_run("run-1")
        run_service.add_workflow_run(run)

        # Execute
        results = attempt_service.get_attempts_by_run("run-1")

        # Assert
        assert results == []

    def test_get_attempts_by_run_nonexistent(self, attempt_service):
        """Get attempts for non-existent run raises ValueError."""
        with pytest.raises(ValueError, match="Run with id 'unknown' not found"):
            attempt_service.get_attempts_by_run("unknown")

    def test_get_attempts_by_run_sorted(self, attempt_service, run_service):
        """Get attempts sorted by attempt_number ascending."""
        # Setup
        run = _make_run("run-1")
        attempt_1 = _make_attempt(id=1, attempt_number=3)
        attempt_2 = _make_attempt(id=2, attempt_number=1)
        attempt_3 = _make_attempt(id=3, attempt_number=2)
        run.attempts = [attempt_1, attempt_2, attempt_3]
        run_service.add_workflow_run(run)

        # Execute with sorting
        results = attempt_service.get_attempts_by_run("run-1", sort_by_number=True)

        # Assert: should be sorted by attempt_number
        assert len(results) == 3
        assert results[0].attempt_number == 1
        assert results[1].attempt_number == 2
        assert results[2].attempt_number == 3

    def test_get_attempts_by_run_unsorted(self, attempt_service, run_service):
        """Get attempts without sorting preserves insertion order."""
        # Setup
        run = _make_run("run-1")
        attempt_1 = _make_attempt(id=1, attempt_number=3)
        attempt_2 = _make_attempt(id=2, attempt_number=1)
        attempt_3 = _make_attempt(id=3, attempt_number=2)
        run.attempts = [attempt_1, attempt_2, attempt_3]
        run_service.add_workflow_run(run)

        # Execute without sorting
        results = attempt_service.get_attempts_by_run("run-1", sort_by_number=False)

        # Assert: order should match insertion order (not sorted)
        assert len(results) == 3
        assert results[0].attempt_number == 3
        assert results[1].attempt_number == 1
        assert results[2].attempt_number == 2


class TestValidateDuplicateAttemptNumber:
    """Tests for AttemptService.validate_duplicate_attempt_number()"""

    def test_validate_duplicate_attempt_number_valid(self, attempt_service):
        """List with unique attempt numbers returns True."""
        attempts = [
            _make_attempt(attempt_number=1),
            _make_attempt(attempt_number=2),
            _make_attempt(attempt_number=3),
        ]
        result = attempt_service.validate_duplicate_attempt_number(attempts)
        assert result is True

    def test_validate_duplicate_attempt_number_empty(self, attempt_service):
        """Empty list returns True."""
        result = attempt_service.validate_duplicate_attempt_number([])
        assert result is True

    def test_validate_duplicate_attempt_number_duplicates(self, attempt_service):
        """List with duplicate attempt_numbers raises ValueError."""
        attempts = [
            _make_attempt(id=1, attempt_number=1),
            _make_attempt(id=2, attempt_number=2),
            _make_attempt(id=3, attempt_number=1),  # Duplicate
        ]
        with pytest.raises(
            ValueError, match="Attempt numbers must be unique within a workflow run"
        ):
            attempt_service.validate_duplicate_attempt_number(attempts)

    def test_validate_duplicate_attempt_number_single_element(self, attempt_service):
        """Single attempt in list returns True."""
        attempts = [_make_attempt(attempt_number=1)]
        result = attempt_service.validate_duplicate_attempt_number(attempts)
        assert result is True

    def test_validate_duplicate_attempt_number_all_duplicates(self, attempt_service):
        """List where all attempts have same number raises ValueError."""
        attempts = [
            _make_attempt(id=1, attempt_number=1),
            _make_attempt(id=2, attempt_number=1),
            _make_attempt(id=3, attempt_number=1),
        ]
        with pytest.raises(
            ValueError, match="Attempt numbers must be unique within a workflow run"
        ):
            attempt_service.validate_duplicate_attempt_number(attempts)


class TestCreateAndPersist:
    """Integration tests for create_attempt with persistence."""

    def test_create_and_persist(self, attempt_service, run_service):
        """Verify that creating an attempt persists to storage."""
        # Setup
        run = _make_run("run-1")
        run_service.add_workflow_run(run)

        # Execute
        attempt_data = _make_attempt_dict(id=1, attempt_number=1)
        attempt_service.create_attempt("run-1", attempt_data)

        # Assert: retrieve from run service to verify persistence
        persisted_run = run_service.get_run_detail("run-1")
        assert len(persisted_run.attempts) == 1
        assert persisted_run.attempts[0].attempt_number == 1

    def test_create_duplicate_persists_error(self, attempt_service, run_service):
        """Verify duplicate check prevents persistence."""
        # Setup
        run = _make_run("run-1")
        existing_attempt = _make_attempt(attempt_number=1)
        run.attempts.append(existing_attempt)
        run_service.add_workflow_run(run)

        # Verify initial state
        initial_count = len(run_service.get_run_detail("run-1").attempts)
        assert initial_count == 1

        # Execute: attempt to add duplicate
        attempt_data = _make_attempt_dict(id=2, attempt_number=1)
        with pytest.raises(ValueError):
            attempt_service.create_attempt("run-1", attempt_data)

        # Assert: count should not have changed
        final_count = len(run_service.get_run_detail("run-1").attempts)
        assert final_count == initial_count
