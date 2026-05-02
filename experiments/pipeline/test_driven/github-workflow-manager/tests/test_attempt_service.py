import pytest
import inspect
from datetime import datetime, timezone, timedelta
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.attempt_service import AttemptService


CEST = timezone(timedelta(hours=2))


def _attempt(**kwargs):
    """Helper to create test WorkflowRunAttempt objects."""
    defaults = dict(
        id="attempt-1",
        run_id="run-1",
        attempt_number=1,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(CEST),
    )
    defaults.update(kwargs)
    return WorkflowRunAttempt(**defaults)


def test_attempt_service_exists():
    """Test that AttemptService class exists and can be instantiated."""
    service = AttemptService()
    assert service is not None


def test_create_attempt():
    """Test that create() adds an attempt and returns it."""
    service = AttemptService()
    attempt = _attempt()
    result = service.create(attempt)
    assert result is attempt
    assert result.id == "attempt-1"
    assert result.run_id == "run-1"


def test_retrieve_attempts_by_run_id():
    """Test that get_by_run_id() retrieves all attempts for a run."""
    service = AttemptService()
    attempt1 = _attempt(id="att-1", run_id="run-1", attempt_number=1)
    attempt2 = _attempt(id="att-2", run_id="run-1", attempt_number=2)
    service.create(attempt1)
    service.create(attempt2)

    results = service.get_by_run_id("run-1")
    assert len(results) == 2
    assert attempt1 in results
    assert attempt2 in results


def test_duplicate_attempt_number_raises():
    """Test that creating a duplicate (run_id, attempt_number) raises ValueError."""
    service = AttemptService()
    attempt1 = _attempt(run_id="run-1", attempt_number=1)
    attempt2 = _attempt(run_id="run-1", attempt_number=1)

    service.create(attempt1)
    with pytest.raises(ValueError):
        service.create(attempt2)


def test_attempts_sorted_by_attempt_number():
    """Test that get_by_run_id() returns attempts sorted by attempt_number ascending."""
    service = AttemptService()
    attempt3 = _attempt(id="att-3", run_id="run-1", attempt_number=3)
    attempt1 = _attempt(id="att-1", run_id="run-1", attempt_number=1)
    attempt2 = _attempt(id="att-2", run_id="run-1", attempt_number=2)

    # Add in non-sorted order
    service.create(attempt3)
    service.create(attempt1)
    service.create(attempt2)

    results = service.get_by_run_id("run-1")
    assert results[0].attempt_number == 1
    assert results[1].attempt_number == 2
    assert results[2].attempt_number == 3


def test_attempt_service_does_not_contain_file_io():
    """Test that AttemptService does not import or use file I/O modules."""
    service = AttemptService()

    # Get the source code of the module
    import src.services.attempt_service as service_module
    source = inspect.getsource(service_module)

    # Check that no file I/O related imports are present
    forbidden_terms = ["import json", "import pickle", "import yaml", "open("]
    for term in forbidden_terms:
        assert term not in source, (
            f"AttemptService should not contain '{term}' for file I/O operations"
        )


def test_get_by_run_id_returns_empty_for_unknown_run():
    """Test that get_by_run_id() returns empty list for unknown run_id."""
    service = AttemptService()
    results = service.get_by_run_id("unknown-run")
    assert results == []


def test_allows_same_run_id_different_attempt_number():
    """Test that same run_id with different attempt_numbers are allowed."""
    service = AttemptService()
    attempt1 = _attempt(run_id="run-1", attempt_number=1)
    attempt2 = _attempt(run_id="run-1", attempt_number=2)

    service.create(attempt1)
    service.create(attempt2)  # Should not raise

    results = service.get_by_run_id("run-1")
    assert len(results) == 2


def test_allows_different_run_id_same_attempt_number():
    """Test that different run_ids with same attempt_number are allowed."""
    service = AttemptService()
    attempt1 = _attempt(run_id="run-1", attempt_number=1)
    attempt2 = _attempt(run_id="run-2", attempt_number=1)

    service.create(attempt1)
    service.create(attempt2)  # Should not raise

    results1 = service.get_by_run_id("run-1")
    results2 = service.get_by_run_id("run-2")
    assert len(results1) == 1
    assert len(results2) == 1


def test_multiple_runs_kept_separate():
    """Test that attempts from different runs are kept separate."""
    service = AttemptService()
    run1_att1 = _attempt(id="att-1", run_id="run-1", attempt_number=1)
    run2_att1 = _attempt(id="att-2", run_id="run-2", attempt_number=1)
    run1_att2 = _attempt(id="att-3", run_id="run-1", attempt_number=2)

    service.create(run1_att1)
    service.create(run2_att1)
    service.create(run1_att2)

    results_run1 = service.get_by_run_id("run-1")
    results_run2 = service.get_by_run_id("run-2")

    assert len(results_run1) == 2
    assert len(results_run2) == 1
    assert all(a.run_id == "run-1" for a in results_run1)
    assert all(a.run_id == "run-2" for a in results_run2)


def test_error_message_includes_run_id_and_attempt_number():
    """Test that error message includes run_id and attempt_number."""
    service = AttemptService()
    attempt1 = _attempt(run_id="run-123", attempt_number=5)
    service.create(attempt1)

    attempt2 = _attempt(run_id="run-123", attempt_number=5)
    with pytest.raises(ValueError) as exc_info:
        service.create(attempt2)

    error_msg = str(exc_info.value)
    assert "run-123" in error_msg
    assert "5" in error_msg
