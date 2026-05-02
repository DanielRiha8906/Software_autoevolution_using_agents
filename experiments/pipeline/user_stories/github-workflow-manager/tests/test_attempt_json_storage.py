import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.storage.attempt_json_storage import AttemptJsonStorage


@pytest.fixture
def tmp_storage(tmp_path):
    """Create a temporary AttemptJsonStorage instance."""
    return AttemptJsonStorage(str(tmp_path / "attempts.json"))


def _sample_attempt(
    attempt_id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    """Helper to create a sample WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=duration_seconds,
    )


class TestAttemptJsonStorageBasic:
    """Test basic storage functionality."""

    def test_load_empty(self, tmp_storage):
        """Test loading from non-existent file returns empty list."""
        assert tmp_storage.load() == []

    def test_save_and_load_roundtrip(self, tmp_storage):
        """Test save and load preserve attempt data."""
        attempt = _sample_attempt()
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert len(loaded) == 1
        assert loaded[0].id == attempt.id
        assert loaded[0].run_id == attempt.run_id
        assert loaded[0].attempt_number == attempt.attempt_number
        assert loaded[0].status == attempt.status
        assert loaded[0].conclusion == attempt.conclusion
        assert loaded[0].duration_seconds == attempt.duration_seconds

    def test_save_multiple_attempts(self, tmp_storage):
        """Test saving and loading multiple attempts."""
        a1 = _sample_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _sample_attempt(attempt_id=2, run_id=100, attempt_number=2)
        a3 = _sample_attempt(attempt_id=3, run_id=101, attempt_number=1)

        tmp_storage.save([a1, a2, a3])
        loaded = tmp_storage.load()

        assert len(loaded) == 3
        assert loaded[0].attempt_number == 1
        assert loaded[1].attempt_number == 2
        assert loaded[2].run_id == 101

    def test_save_overwrites_previous(self, tmp_storage):
        """Test that save overwrites previous data."""
        a1 = _sample_attempt(attempt_id=1)
        tmp_storage.save([a1])

        a2 = _sample_attempt(attempt_id=2)
        tmp_storage.save([a2])

        loaded = tmp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].id == 2


class TestAttemptJsonStorageJSON:
    """Test JSON serialization format."""

    def test_save_produces_valid_json(self, tmp_storage):
        """Test that saved file is valid JSON."""
        attempt = _sample_attempt()
        tmp_storage.save([attempt])

        # Should not raise
        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert isinstance(raw, list)
        assert len(raw) == 1

    def test_json_contains_expected_fields(self, tmp_storage):
        """Test JSON has all expected fields."""
        attempt = _sample_attempt(
            attempt_id=42,
            run_id=100,
            attempt_number=3,
            status="in_progress",
            conclusion=None,
            duration_seconds=123.45,
        )
        tmp_storage.save([attempt])

        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert raw[0]["id"] == 42
        assert raw[0]["run_id"] == 100
        assert raw[0]["attempt_number"] == 3
        assert raw[0]["status"] == "in_progress"
        assert raw[0]["conclusion"] is None
        assert raw[0]["duration_seconds"] == 123.45
        assert "created_at" in raw[0]

    def test_json_created_at_is_string(self, tmp_storage):
        """Test that created_at is serialized as ISO string."""
        attempt = _sample_attempt()
        tmp_storage.save([attempt])

        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert isinstance(raw[0]["created_at"], str)
        assert "T" in raw[0]["created_at"]  # ISO 8601 format


class TestAttemptJsonStorageDurations:
    """Test duration_seconds handling."""

    def test_roundtrip_zero_duration(self, tmp_storage):
        """Test zero duration round-trips correctly."""
        attempt = _sample_attempt(duration_seconds=0.0)
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].duration_seconds == 0.0

    def test_roundtrip_nonzero_duration(self, tmp_storage):
        """Test non-zero duration round-trips correctly."""
        attempt = _sample_attempt(duration_seconds=456.789)
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].duration_seconds == 456.789

    def test_roundtrip_large_duration(self, tmp_storage):
        """Test large duration values round-trip correctly."""
        attempt = _sample_attempt(duration_seconds=604800.0)  # 1 week
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].duration_seconds == 604800.0

    def test_backward_compatibility_missing_duration(self, tmp_storage):
        """Test that missing duration_seconds defaults to 0.0."""
        # Simulate old JSON without duration_seconds
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        json_content = json.dumps([data])
        Path(tmp_storage.filepath).write_text(json_content)

        loaded = tmp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].duration_seconds == 0.0


class TestAttemptJsonStorageConclusion:
    """Test conclusion field handling."""

    def test_roundtrip_with_conclusion(self, tmp_storage):
        """Test conclusion value round-trips correctly."""
        attempt = _sample_attempt(conclusion="failure")
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].conclusion == "failure"

    def test_roundtrip_with_none_conclusion(self, tmp_storage):
        """Test None conclusion round-trips correctly."""
        attempt = _sample_attempt(conclusion=None)
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].conclusion is None

    def test_various_conclusion_values(self, tmp_storage):
        """Test various conclusion values."""
        conclusions = ["success", "failure", "cancelled", "skipped", "timed_out", None]
        attempts = [
            _sample_attempt(attempt_id=i, conclusion=c)
            for i, c in enumerate(conclusions)
        ]

        tmp_storage.save(attempts)
        loaded = tmp_storage.load()

        assert len(loaded) == len(conclusions)
        for loaded_attempt, original_conclusion in zip(loaded, conclusions):
            assert loaded_attempt.conclusion == original_conclusion


class TestAttemptJsonStorageDatetime:
    """Test datetime handling."""

    def test_roundtrip_preserves_timezone(self, tmp_storage):
        """Test that timezone information is preserved."""
        from datetime import timezone as tz
        dt = datetime(2024, 6, 15, 14, 30, 45, tzinfo=tz.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=dt,
        )

        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].created_at == dt
        assert loaded[0].created_at.tzinfo == tz.utc

    def test_roundtrip_different_datetimes(self, tmp_storage):
        """Test various datetime values round-trip correctly."""
        datetimes = [
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            datetime(2025, 6, 15, 12, 30, 45, 123456, tzinfo=timezone.utc),
        ]

        attempts = [
            _sample_attempt(attempt_id=i, attempt_number=i + 1)
            for i in range(len(datetimes))
        ]

        for attempt, dt in zip(attempts, datetimes):
            attempt.created_at = dt

        tmp_storage.save(attempts)
        loaded = tmp_storage.load()

        for loaded_attempt, original_dt in zip(loaded, datetimes):
            assert loaded_attempt.created_at == original_dt


class TestAttemptJsonStorageFilepath:
    """Test filepath handling."""

    def test_default_filepath(self):
        """Test default filepath is correct."""
        storage = AttemptJsonStorage()
        assert str(storage.filepath) == "artifacts/workflow_run_attempts.json"

    def test_custom_filepath(self, tmp_path):
        """Test custom filepath is respected."""
        custom_path = tmp_path / "custom" / "path" / "attempts.json"
        storage = AttemptJsonStorage(str(custom_path))

        attempt = _sample_attempt()
        storage.save([attempt])

        assert custom_path.exists()
        loaded = storage.load()
        assert len(loaded) == 1

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        filepath = tmp_path / "a" / "b" / "c" / "attempts.json"
        assert not filepath.parent.exists()

        storage = AttemptJsonStorage(str(filepath))
        assert filepath.parent.exists()


class TestAttemptJsonStorageEdgeCases:
    """Test edge cases and special scenarios."""

    def test_save_empty_list(self, tmp_storage):
        """Test saving an empty list."""
        tmp_storage.save([])
        loaded = tmp_storage.load()

        assert loaded == []

    def test_status_with_special_characters(self, tmp_storage):
        """Test status with special characters."""
        attempt = _sample_attempt(status="in_progress_with_retry")
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].status == "in_progress_with_retry"

    def test_large_attempt_id(self, tmp_storage):
        """Test large attempt ID values."""
        attempt = _sample_attempt(attempt_id=999999999)
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].id == 999999999

    def test_large_run_id(self, tmp_storage):
        """Test large run ID values."""
        attempt = _sample_attempt(run_id=999999999)
        tmp_storage.save([attempt])
        loaded = tmp_storage.load()

        assert loaded[0].run_id == 999999999

    def test_large_attempt_number_sequence(self, tmp_storage):
        """Test large attempt numbers."""
        attempts = [
            _sample_attempt(attempt_id=i, attempt_number=i)
            for i in range(1, 101)  # 100 attempts
        ]

        tmp_storage.save(attempts)
        loaded = tmp_storage.load()

        assert len(loaded) == 100
        assert loaded[-1].attempt_number == 100
