import pytest
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage


# ============================================================================
# Fixtures and Helpers
# ============================================================================

def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    """Factory for creating test WorkflowRunAttempt instances."""
    if created_at is None:
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(temp_storage_dir):
    """Create a WorkflowJsonStorage instance with temp paths."""
    return WorkflowJsonStorage(
        filepath=str(Path(temp_storage_dir) / "runs.json"),
        attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
    )


@pytest.fixture
def service(storage):
    """Create a WorkflowRunAttemptService instance."""
    return WorkflowRunAttemptService(storage)


# ============================================================================
# Task 1: Model Validation (__post_init__)
# ============================================================================

class TestWorkflowRunAttemptValidation:
    """Tests for WorkflowRunAttempt.__post_init__() validation."""

    def test_valid_attempt_minimum_values(self):
        """Attempt with minimum valid values creates successfully."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,  # Minimum valid
            status="queued",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,  # Minimum valid
        )
        assert attempt.attempt_number == 1
        assert attempt.duration_seconds == 0.0

    def test_valid_attempt_typical_values(self):
        """Attempt with typical values creates successfully."""
        now = datetime(2024, 5, 3, 14, 30, 45, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=42,
            run_id=999,
            attempt_number=3,
            status="completed",
            conclusion="success",
            created_at=now,
            duration_seconds=123.45,
        )
        assert attempt.id == 42
        assert attempt.run_id == 999
        assert attempt.attempt_number == 3
        assert attempt.duration_seconds == 123.45

    def test_attempt_number_zero_raises_error(self):
        """attempt_number = 0 raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=0,
                status="queued",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
            )

    def test_attempt_number_negative_raises_error(self):
        """attempt_number < 0 raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=-5,
                status="queued",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
            )

    def test_attempt_number_float_raises_error(self):
        """attempt_number as float raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1.5,
                status="queued",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
            )

    def test_attempt_number_string_raises_error(self):
        """attempt_number as string raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number="1",  # type: ignore
                status="queued",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
            )

    def test_duration_seconds_negative_raises_error(self):
        """duration_seconds < 0 raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="queued",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
                duration_seconds=-0.1,
            )

    def test_duration_seconds_zero_allowed(self):
        """duration_seconds = 0.0 is allowed."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="queued",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        assert attempt.duration_seconds == 0.0

    def test_duration_seconds_large_value_allowed(self):
        """duration_seconds with large value is allowed."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="queued",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=999999.99,
        )
        assert attempt.duration_seconds == 999999.99


# ============================================================================
# Task 2: Serialization (to_dict and from_dict)
# ============================================================================

class TestWorkflowRunAttemptSerialization:
    """Tests for to_dict() and from_dict() serialization."""

    def test_to_dict_complete_attempt(self):
        """to_dict() produces correct dictionary with all fields."""
        now = datetime(2024, 5, 3, 10, 15, 30, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=2,
            status="completed",
            conclusion="success",
            created_at=now,
            duration_seconds=45.5,
        )
        result = attempt.to_dict()
        assert result["id"] == 1
        assert result["run_id"] == 100
        assert result["attempt_number"] == 2
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["created_at"] == now.isoformat()
        assert result["duration_seconds"] == 45.5

    def test_to_dict_nullable_conclusion(self):
        """to_dict() handles nullable conclusion correctly."""
        attempt = _make_attempt(conclusion=None)
        result = attempt.to_dict()
        assert result["conclusion"] is None

    def test_to_dict_returns_isoformat_datetime(self):
        """to_dict() converts created_at to ISO format string."""
        now = datetime(2024, 5, 3, 14, 30, 45, 123456, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=now)
        result = attempt.to_dict()
        assert isinstance(result["created_at"], str)
        assert result["created_at"] == now.isoformat()

    def test_from_dict_complete_data(self):
        """from_dict() reconstructs attempt from complete dictionary."""
        now = datetime(2024, 5, 3, 10, 15, 30, tzinfo=timezone.utc)
        data = {
            "id": 5,
            "run_id": 200,
            "attempt_number": 3,
            "status": "completed",
            "conclusion": "failure",
            "created_at": now.isoformat(),
            "duration_seconds": 120.75,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 5
        assert attempt.run_id == 200
        assert attempt.attempt_number == 3
        assert attempt.status == "completed"
        assert attempt.conclusion == "failure"
        assert attempt.created_at == now
        assert attempt.duration_seconds == 120.75

    def test_from_dict_nullable_conclusion(self):
        """from_dict() handles missing/null conclusion correctly."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_missing_conclusion_key(self):
        """from_dict() handles missing conclusion key as None."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_missing_duration_defaults_to_zero(self):
        """from_dict() defaults duration_seconds to 0.0 if missing."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_from_dict_parses_isoformat_datetime(self):
        """from_dict() correctly parses ISO format datetime strings."""
        now = datetime(2024, 5, 3, 14, 30, 45, 123456, tzinfo=timezone.utc)
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": now.isoformat(),
            "duration_seconds": 10.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.created_at == now

    def test_round_trip_with_conclusion(self):
        """Serialization round-trip preserves all fields including conclusion."""
        original = _make_attempt(
            attempt_id=7,
            run_id=555,
            attempt_number=4,
            status="completed",
            conclusion="success",
            duration_seconds=89.5,
        )
        data = original.to_dict()
        reconstructed = WorkflowRunAttempt.from_dict(data)
        assert reconstructed.id == original.id
        assert reconstructed.run_id == original.run_id
        assert reconstructed.attempt_number == original.attempt_number
        assert reconstructed.status == original.status
        assert reconstructed.conclusion == original.conclusion
        assert reconstructed.created_at == original.created_at
        assert reconstructed.duration_seconds == original.duration_seconds

    def test_round_trip_without_conclusion(self):
        """Serialization round-trip preserves null conclusion."""
        original = _make_attempt(conclusion=None)
        data = original.to_dict()
        reconstructed = WorkflowRunAttempt.from_dict(data)
        assert reconstructed.conclusion is None


# ============================================================================
# Task 3: Service CRUD Operations
# ============================================================================

class TestWorkflowRunAttemptServiceCRUD:
    """Tests for WorkflowRunAttemptService CRUD operations."""

    def test_add_attempt_single(self, service):
        """add_attempt() stores a new attempt."""
        attempt = _make_attempt()
        result = service.add_attempt(attempt)
        assert result is attempt
        assert service.list_attempts() == [attempt]

    def test_add_attempt_multiple(self, service):
        """add_attempt() stores multiple attempts."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.add_attempt(a1)
        service.add_attempt(a2)
        assert len(service.list_attempts()) == 2
        assert a1 in service.list_attempts()
        assert a2 in service.list_attempts()

    def test_list_attempts_empty(self, service):
        """list_attempts() returns empty list when no attempts added."""
        assert service.list_attempts() == []

    def test_list_attempts_returns_copy(self, service):
        """list_attempts() returns a list copy, not the internal reference."""
        attempt = _make_attempt()
        service.add_attempt(attempt)
        list1 = service.list_attempts()
        list2 = service.list_attempts()
        assert list1 == list2
        assert list1 is not list2  # Different list objects

    def test_get_attempt_by_id_found(self, service):
        """get_attempt() returns attempt by id when it exists."""
        attempt = _make_attempt(attempt_id=42)
        service.add_attempt(attempt)
        result = service.get_attempt(42)
        assert result is attempt

    def test_get_attempt_by_id_not_found(self, service):
        """get_attempt() returns None when attempt_id not found."""
        service.add_attempt(_make_attempt(attempt_id=1))
        result = service.get_attempt(999)
        assert result is None

    def test_get_attempts_for_run_single(self, service):
        """get_attempts_for_run() returns all attempts for a given run_id."""
        attempt = _make_attempt(run_id=100, attempt_number=1)
        service.add_attempt(attempt)
        results = service.get_attempts_for_run(100)
        assert results == [attempt]

    def test_get_attempts_for_run_multiple(self, service):
        """get_attempts_for_run() returns multiple attempts for same run."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        a3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=3)
        service.add_attempt(a1)
        service.add_attempt(a2)
        service.add_attempt(a3)
        results = service.get_attempts_for_run(100)
        assert results == [a1, a2, a3]

    def test_get_attempts_for_run_filters_by_run_id(self, service):
        """get_attempts_for_run() filters to only the specified run_id."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        a3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=2)
        service.add_attempt(a1)
        service.add_attempt(a2)
        service.add_attempt(a3)
        results = service.get_attempts_for_run(100)
        assert len(results) == 2
        assert a1 in results
        assert a3 in results
        assert a2 not in results

    def test_get_attempts_for_run_not_found_returns_empty(self, service):
        """get_attempts_for_run() returns empty list for nonexistent run_id."""
        service.add_attempt(_make_attempt(run_id=100))
        results = service.get_attempts_for_run(999)
        assert results == []


# ============================================================================
# Task 3: Unique Constraint Enforcement
# ============================================================================

class TestWorkflowRunAttemptServiceUniqueness:
    """Tests for unique constraint enforcement on (run_id, attempt_number)."""

    def test_unique_constraint_prevents_duplicate(self, service):
        """Adding attempt with duplicate (run_id, attempt_number) raises ValueError."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.add_attempt(a1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=1)  # Same run, same attempt #
        with pytest.raises(ValueError, match="already exists"):
            service.add_attempt(a2)

    def test_unique_constraint_allows_same_attempt_number_different_run(self, service):
        """Same attempt_number in different runs is allowed."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        service.add_attempt(a1)
        service.add_attempt(a2)  # Should not raise
        assert len(service.list_attempts()) == 2

    def test_unique_constraint_allows_different_attempt_numbers_same_run(self, service):
        """Different attempt_numbers for same run is allowed."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.add_attempt(a1)
        service.add_attempt(a2)  # Should not raise
        assert len(service.list_attempts()) == 2

    def test_unique_constraint_error_message_format(self, service):
        """Error message includes run_id and attempt_number."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=5)
        service.add_attempt(a1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=5)
        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(a2)
        assert "100" in str(exc_info.value)
        assert "5" in str(exc_info.value)


# ============================================================================
# Task 4: JSON Persistence and Reload Cycles
# ============================================================================

class TestWorkflowRunAttemptPersistence:
    """Tests for JSON persistence and reload cycles."""

    def test_persistence_single_attempt(self, temp_storage_dir):
        """Adding attempt persists it to JSON and can be reloaded."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)
        attempt = _make_attempt(attempt_id=1, run_id=100)
        service1.add_attempt(attempt)

        # Create new service instance to reload from storage
        service2 = WorkflowRunAttemptService(storage)
        loaded = service2.list_attempts()
        assert len(loaded) == 1
        assert loaded[0].id == 1
        assert loaded[0].run_id == 100

    def test_persistence_multiple_attempts(self, temp_storage_dir):
        """Multiple attempts persist and reload correctly."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        a3 = _make_attempt(attempt_id=3, run_id=200, attempt_number=1)
        service1.add_attempt(a1)
        service1.add_attempt(a2)
        service1.add_attempt(a3)

        service2 = WorkflowRunAttemptService(storage)
        loaded = service2.list_attempts()
        assert len(loaded) == 3

    def test_persistence_preserves_field_values(self, temp_storage_dir):
        """JSON persistence preserves all field values across reload."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)
        now = datetime(2024, 5, 3, 10, 15, 30, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=42,
            run_id=555,
            attempt_number=7,
            status="completed",
            conclusion="success",
            created_at=now,
            duration_seconds=234.56,
        )
        service1.add_attempt(attempt)

        service2 = WorkflowRunAttemptService(storage)
        loaded = service2.list_attempts()[0]
        assert loaded.id == 42
        assert loaded.run_id == 555
        assert loaded.attempt_number == 7
        assert loaded.status == "completed"
        assert loaded.conclusion == "success"
        assert loaded.created_at == now
        assert loaded.duration_seconds == 234.56

    def test_persistence_nullable_conclusion(self, temp_storage_dir):
        """JSON persistence handles null conclusion correctly."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)
        attempt = _make_attempt(conclusion=None)
        service1.add_attempt(attempt)

        service2 = WorkflowRunAttemptService(storage)
        loaded = service2.list_attempts()[0]
        assert loaded.conclusion is None

    def test_persistence_creates_json_file(self, temp_storage_dir):
        """add_attempt() creates JSON file in correct location."""
        attempts_path = Path(temp_storage_dir) / "attempts.json"
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(attempts_path),
        )
        service = WorkflowRunAttemptService(storage)
        attempt = _make_attempt()
        service.add_attempt(attempt)
        assert attempts_path.exists()

    def test_persistence_json_format_valid(self, temp_storage_dir):
        """Persisted JSON is valid and readable."""
        attempts_path = Path(temp_storage_dir) / "attempts.json"
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(attempts_path),
        )
        service = WorkflowRunAttemptService(storage)
        a1 = _make_attempt(attempt_id=1, run_id=100)
        service.add_attempt(a1)

        # Read and parse JSON directly
        with open(attempts_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 1

    def test_load_attempts_missing_file_returns_empty(self, temp_storage_dir):
        """load_attempts() returns empty list if file doesn't exist."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "nonexistent.json"),
        )
        service = WorkflowRunAttemptService(storage)
        assert service.list_attempts() == []

    def test_persistence_overwrites_on_new_add(self, temp_storage_dir):
        """Adding to service updates the JSON file correctly."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)
        a1 = _make_attempt(attempt_id=1)
        service1.add_attempt(a1)

        service2 = WorkflowRunAttemptService(storage)
        a2 = _make_attempt(attempt_id=2, run_id=101)
        service2.add_attempt(a2)

        service3 = WorkflowRunAttemptService(storage)
        loaded = service3.list_attempts()
        assert len(loaded) == 2
        ids = [a.id for a in loaded]
        assert 1 in ids
        assert 2 in ids


# ============================================================================
# Task 5: Nullable Conclusion Field Handling
# ============================================================================

class TestNullableConclusionField:
    """Tests for nullable conclusion field in various contexts."""

    @pytest.mark.parametrize(
        "conclusion",
        [None, "success", "failure", "cancelled", "skipped", "timed_out"],
    )
    def test_various_conclusion_values(self, service, conclusion):
        """Conclusion accepts various values including None."""
        attempt = _make_attempt(conclusion=conclusion)
        service.add_attempt(attempt)
        result = service.get_attempt(attempt.id)
        assert result.conclusion == conclusion

    def test_conclusion_none_in_progress_status(self, service):
        """Conclusion is None when status is in_progress."""
        attempt = _make_attempt(status="in_progress", conclusion=None)
        service.add_attempt(attempt)
        result = service.get_attempt(attempt.id)
        assert result.status == "in_progress"
        assert result.conclusion is None

    def test_conclusion_none_preserves_through_serialization(self):
        """None conclusion preserves through to_dict/from_dict."""
        attempt = _make_attempt(conclusion=None)
        data = attempt.to_dict()
        reconstructed = WorkflowRunAttempt.from_dict(data)
        assert reconstructed.conclusion is None

    def test_conclusion_none_filtered_in_list(self, service):
        """Null conclusions don't break filtering operations."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1, conclusion=None)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2, conclusion="success")
        service.add_attempt(a1)
        service.add_attempt(a2)
        results = service.get_attempts_for_run(100)
        assert len(results) == 2


# ============================================================================
# Task 6: Edge Cases and Boundary Conditions
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_attempt_number_maximum_valid_int(self, service):
        """Very large attempt_number values are accepted."""
        attempt = _make_attempt(attempt_number=999999999)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).attempt_number == 999999999

    def test_duration_seconds_very_large_value(self, service):
        """Very large duration_seconds is accepted."""
        attempt = _make_attempt(duration_seconds=1e10)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).duration_seconds == 1e10

    def test_duration_seconds_very_small_positive_value(self, service):
        """Very small positive duration_seconds is accepted."""
        attempt = _make_attempt(duration_seconds=1e-10)
        service.add_attempt(attempt)
        result = service.get_attempt(attempt.id)
        assert result.duration_seconds == pytest.approx(1e-10)

    def test_run_id_zero(self, service):
        """run_id = 0 is allowed."""
        attempt = _make_attempt(run_id=0)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).run_id == 0

    def test_run_id_negative(self, service):
        """Negative run_id is allowed (not validated)."""
        attempt = _make_attempt(run_id=-1)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).run_id == -1

    def test_status_empty_string(self, service):
        """Empty string status is allowed (not validated)."""
        attempt = _make_attempt(status="")
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).status == ""

    def test_status_unusual_value(self, service):
        """Unusual status values are allowed (not validated)."""
        attempt = _make_attempt(status="unknown_status_xyz")
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).status == "unknown_status_xyz"

    def test_conclusion_unusual_value(self, service):
        """Unusual conclusion values are allowed (not validated)."""
        attempt = _make_attempt(conclusion="weird_conclusion")
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).conclusion == "weird_conclusion"

    def test_datetime_past_far_ago(self, service):
        """Very old datetime is accepted."""
        old_date = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=old_date)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).created_at == old_date

    def test_datetime_future(self, service):
        """Future datetime is accepted."""
        future_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=future_date)
        service.add_attempt(attempt)
        assert service.get_attempt(attempt.id).created_at == future_date

    def test_datetime_with_microseconds(self, service):
        """Datetime with microseconds preserves precision."""
        precise_date = datetime(2024, 5, 3, 14, 30, 45, 123456, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=precise_date)
        service.add_attempt(attempt)
        result = service.get_attempt(attempt.id)
        assert result.created_at == precise_date
        assert result.created_at.microsecond == 123456

    def test_id_zero(self, service):
        """id = 0 is allowed."""
        attempt = _make_attempt(attempt_id=0)
        service.add_attempt(attempt)
        assert service.get_attempt(0) is attempt

    def test_id_negative(self, service):
        """Negative id is allowed."""
        attempt = _make_attempt(attempt_id=-5)
        service.add_attempt(attempt)
        assert service.get_attempt(-5) is attempt


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_add_query_persist_reload(self, temp_storage_dir):
        """Full workflow: add, query, persist, reload."""
        storage = WorkflowJsonStorage(
            filepath=str(Path(temp_storage_dir) / "runs.json"),
            attempts_filepath=str(Path(temp_storage_dir) / "attempts.json"),
        )
        service1 = WorkflowRunAttemptService(storage)

        # Add multiple attempts
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1, conclusion="success")
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2, conclusion=None)
        a3 = _make_attempt(attempt_id=3, run_id=200, attempt_number=1, conclusion="failure")
        service1.add_attempt(a1)
        service1.add_attempt(a2)
        service1.add_attempt(a3)

        # Query operations
        assert service1.get_attempt(1) is a1
        assert len(service1.get_attempts_for_run(100)) == 2
        assert len(service1.get_attempts_for_run(200)) == 1

        # Reload and verify
        service2 = WorkflowRunAttemptService(storage)
        assert len(service2.list_attempts()) == 3
        assert service2.get_attempt(2).conclusion is None
        assert service2.get_attempt(3).run_id == 200

    def test_service_rejects_duplicate_then_accepts_different(self, service):
        """Service rejects duplicate constraint violation but accepts new valid attempt."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.add_attempt(a1)

        # Try duplicate - should fail
        a2_dup = _make_attempt(attempt_id=2, run_id=100, attempt_number=1)
        with pytest.raises(ValueError):
            service.add_attempt(a2_dup)

        # But different attempt number should succeed
        a2_new = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.add_attempt(a2_new)
        assert len(service.list_attempts()) == 2

    def test_validation_happens_before_persistence(self, service):
        """Invalid attempt raises during construction before persistence."""
        valid = _make_attempt(attempt_id=1)
        service.add_attempt(valid)

        # Try to construct invalid attempt (negative duration)
        # Validation error happens during __post_init__, not during add_attempt
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt(
                id=2,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion=None,
                created_at=datetime.now(timezone.utc),
                duration_seconds=-1.0,
            )

        # Verify only the valid one was persisted
        assert len(service.list_attempts()) == 1
        assert service.list_attempts()[0].id == 1

    @pytest.mark.parametrize(
        "attempt_id,run_id,attempt_num",
        [(1, 100, 1), (2, 100, 2), (3, 200, 1), (99, 999, 1)],
    )
    def test_multiple_add_and_get_combinations(self, service, attempt_id, run_id, attempt_num):
        """Parametrized test for various add/get combinations."""
        attempt = _make_attempt(attempt_id=attempt_id, run_id=run_id, attempt_number=attempt_num)
        service.add_attempt(attempt)
        result = service.get_attempt(attempt_id)
        assert result.run_id == run_id
        assert result.attempt_number == attempt_num
