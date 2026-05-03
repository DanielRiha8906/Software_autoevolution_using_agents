import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = AttemptService(storage)
    return svc


def test_composite_key_validation_run_id_and_attempt_number(service):
    """Test that composite key (run_id, attempt_number) prevents duplicates."""
    service.create_attempt(
        run_id=100,
        attempt_number=5,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )

    # Same run_id but different attempt_number should work
    attempt2 = service.create_attempt(
        run_id=100,
        attempt_number=6,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    assert attempt2.attempt_number == 6

    # Different run_id but same attempt_number should work
    attempt3 = service.create_attempt(
        run_id=101,
        attempt_number=5,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    assert attempt3.run_id == 101

    # Exact duplicate (same run_id AND attempt_number) should fail
    with pytest.raises(ValueError, match="already exists"):
        service.create_attempt(
            run_id=100,
            attempt_number=5,
            status="queued",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
        )


def test_sorting_by_attempt_number_ascending(service):
    """Test that get_attempts_by_run_id returns attempts sorted by attempt_number in ascending order."""
    # Create in non-sequential order
    service.create_attempt(
        run_id=50,
        attempt_number=3,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    service.create_attempt(
        run_id=50,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    service.create_attempt(
        run_id=50,
        attempt_number=2,
        status="completed",
        conclusion="failure",
        created_at=datetime.now(timezone.utc),
    )

    attempts = service.get_attempts_by_run_id(50)
    assert len(attempts) == 3
    assert [a.attempt_number for a in attempts] == [1, 2, 3]
