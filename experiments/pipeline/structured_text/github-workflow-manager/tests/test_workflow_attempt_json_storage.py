"""
Tests for WorkflowAttemptJsonStorage.

Covers:
- save and load operations
- Persistence across instances
- Empty file handling
- Multiple attempts
- Serialization roundtrips
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage


def _make_attempt(
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt."""
    now = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        started_at=now,
        completed_at=now,
        duration_seconds=0.0,
        logs_url=None,
    )


@pytest.fixture
def temp_storage_path():
    """Create a temporary file path for storage testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = str(Path(tmpdir) / "attempts.json")
        yield filepath


class TestWorkflowAttemptJsonStorageSaveLoad:
    """Test basic save and load operations."""

    def test_save_empty_list(self, temp_storage_path):
        """Test saving an empty list."""
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([])

        assert Path(temp_storage_path).exists()
        content = json.loads(Path(temp_storage_path).read_text())
        assert content == []

    def test_save_single_attempt(self, temp_storage_path):
        """Test saving a single attempt."""
        attempt = _make_attempt()
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])

        content = json.loads(Path(temp_storage_path).read_text())
        assert len(content) == 1
        assert content[0]["id"] == "attempt-1"

    def test_save_multiple_attempts(self, temp_storage_path):
        """Test saving multiple attempts."""
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i}")
            for i in range(5)
        ]
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save(attempts)

        content = json.loads(Path(temp_storage_path).read_text())
        assert len(content) == 5
        for i, attempt_dict in enumerate(content):
            assert attempt_dict["id"] == f"attempt-{i}"

    def test_load_empty_file_nonexistent(self, temp_storage_path):
        """Test load returns empty list when file doesn't exist."""
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        attempts = storage.load()
        assert attempts == []

    def test_load_single_attempt(self, temp_storage_path):
        """Test loading a single attempt."""
        attempt = _make_attempt()
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])

        storage2 = WorkflowAttemptJsonStorage(temp_storage_path)
        loaded = storage2.load()

        assert len(loaded) == 1
        assert loaded[0].id == "attempt-1"
        assert loaded[0].run_id == "run-1"
        assert loaded[0].status == WorkflowStatus.COMPLETED
        assert loaded[0].conclusion == WorkflowConclusion.SUCCESS

    def test_load_multiple_attempts(self, temp_storage_path):
        """Test loading multiple attempts."""
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i}")
            for i in range(3)
        ]
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save(attempts)

        storage2 = WorkflowAttemptJsonStorage(temp_storage_path)
        loaded = storage2.load()

        assert len(loaded) == 3
        for i, attempt in enumerate(loaded):
            assert attempt.id == f"attempt-{i}"
            assert attempt.run_id == f"run-{i}"


class TestWorkflowAttemptJsonStoragePersistence:
    """Test persistence across storage instances."""

    def test_persistence_across_instances(self, temp_storage_path):
        """Test that data persists across different storage instances."""
        # First instance: save
        attempt = _make_attempt(attempt_id="persistent-1")
        storage1 = WorkflowAttemptJsonStorage(temp_storage_path)
        storage1.save([attempt])

        # Second instance: load
        storage2 = WorkflowAttemptJsonStorage(temp_storage_path)
        loaded = storage2.load()

        assert len(loaded) == 1
        assert loaded[0].id == "persistent-1"

    def test_overwrite_existing_file(self, temp_storage_path):
        """Test that save overwrites previous data."""
        # First save
        attempt1 = _make_attempt(attempt_id="attempt-1")
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt1])

        # Second save with different data
        attempt2 = _make_attempt(attempt_id="attempt-2")
        storage.save([attempt2])

        # Load and verify
        loaded = storage.load()
        assert len(loaded) == 1
        assert loaded[0].id == "attempt-2"

    def test_update_append_pattern(self, temp_storage_path):
        """Test the pattern of load, append, save."""
        storage = WorkflowAttemptJsonStorage(temp_storage_path)

        # Initial save
        attempt1 = _make_attempt(attempt_id="attempt-1")
        storage.save([attempt1])

        # Load, append, save
        loaded = storage.load()
        attempt2 = _make_attempt(attempt_id="attempt-2")
        loaded.append(attempt2)
        storage.save(loaded)

        # Verify both are present
        reloaded = storage.load()
        assert len(reloaded) == 2
        ids = {a.id for a in reloaded}
        assert ids == {"attempt-1", "attempt-2"}


class TestWorkflowAttemptJsonStorageRoundtrip:
    """Test serialization roundtrips."""

    def test_roundtrip_preserves_all_fields(self, temp_storage_path):
        """Test that roundtrip preserves all attempt fields."""
        now = datetime.now(timezone.utc)
        attempt = WorkflowRunAttempt(
            id="attempt-rt-1",
            run_id="run-rt-1",
            attempt_number=3,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            started_at=now,
            completed_at=now,
            duration_seconds=123.45,
            logs_url="https://example.com/logs",
        )

        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])
        loaded = storage.load()

        assert len(loaded) == 1
        loaded_attempt = loaded[0]
        assert loaded_attempt.id == attempt.id
        assert loaded_attempt.run_id == attempt.run_id
        assert loaded_attempt.attempt_number == attempt.attempt_number
        assert loaded_attempt.status == attempt.status
        assert loaded_attempt.conclusion == attempt.conclusion
        assert loaded_attempt.duration_seconds == attempt.duration_seconds
        assert loaded_attempt.logs_url == attempt.logs_url

    def test_roundtrip_with_none_values(self, temp_storage_path):
        """Test roundtrip with None values."""
        now = datetime.now(timezone.utc)
        attempt = WorkflowRunAttempt(
            id="attempt-none-1",
            run_id="run-none-1",
            attempt_number=1,
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            started_at=now,
            completed_at=None,
            duration_seconds=0.0,
            logs_url=None,
        )

        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])
        loaded = storage.load()

        assert len(loaded) == 1
        assert loaded[0].conclusion is None
        assert loaded[0].completed_at is None
        assert loaded[0].logs_url is None

    def test_roundtrip_multiple_status_values(self, temp_storage_path):
        """Test roundtrip with different status values."""
        attempts = []
        for status in WorkflowStatus:
            conclusion = WorkflowConclusion.SUCCESS if status == WorkflowStatus.COMPLETED else None
            attempt = _make_attempt(
                attempt_id=f"attempt-{status.value}",
                status=status,
                conclusion=conclusion,
            )
            attempts.append(attempt)

        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save(attempts)
        loaded = storage.load()

        assert len(loaded) == len(WorkflowStatus)
        for i, status in enumerate(WorkflowStatus):
            assert loaded[i].status == status

    def test_roundtrip_multiple_conclusion_values(self, temp_storage_path):
        """Test roundtrip with different conclusion values."""
        attempts = []
        for conclusion in WorkflowConclusion:
            attempt = _make_attempt(
                attempt_id=f"attempt-{conclusion.value}",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
            )
            attempts.append(attempt)

        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save(attempts)
        loaded = storage.load()

        assert len(loaded) == len(WorkflowConclusion)
        for i, conclusion in enumerate(WorkflowConclusion):
            assert loaded[i].conclusion == conclusion


class TestWorkflowAttemptJsonStorageDirectoryCreation:
    """Test directory creation behavior."""

    def test_creates_parent_directory(self, temp_storage_path):
        """Test that storage creates parent directories."""
        nested_path = str(Path(temp_storage_path).parent / "nested" / "deep" / "attempts.json")

        storage = WorkflowAttemptJsonStorage(nested_path)
        assert Path(nested_path).parent.exists()

    def test_works_with_existing_directory(self, temp_storage_path):
        """Test that storage works when directory already exists."""
        storage1 = WorkflowAttemptJsonStorage(temp_storage_path)
        attempt1 = _make_attempt(attempt_id="attempt-1")
        storage1.save([attempt1])

        # Create another storage instance with same path
        storage2 = WorkflowAttemptJsonStorage(temp_storage_path)
        loaded = storage2.load()

        assert len(loaded) == 1


class TestWorkflowAttemptJsonStorageDataIntegrity:
    """Test data integrity during save/load."""

    def test_json_format_is_valid(self, temp_storage_path):
        """Test that saved file is valid JSON."""
        attempt = _make_attempt()
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])

        # Verify file can be parsed as JSON
        with open(temp_storage_path) as f:
            data = json.load(f)
        assert isinstance(data, list)

    def test_json_is_readable(self, temp_storage_path):
        """Test that JSON is human-readable (indented)."""
        attempt = _make_attempt()
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([attempt])

        content = Path(temp_storage_path).read_text()
        # Check for indentation (valid JSON with indent=2)
        assert "\n" in content  # Should have newlines from indentation
        lines = content.split("\n")
        assert any(line.startswith("  ") for line in lines)  # Check for indent


class TestWorkflowAttemptJsonStorageEdgeCases:
    """Test edge cases."""

    def test_empty_list_roundtrip(self, temp_storage_path):
        """Test saving and loading empty list."""
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save([])
        loaded = storage.load()
        assert loaded == []

    def test_large_list_roundtrip(self, temp_storage_path):
        """Test saving and loading large list."""
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i // 10}")
            for i in range(100)
        ]
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        storage.save(attempts)
        loaded = storage.load()

        assert len(loaded) == 100
        assert [a.id for a in loaded] == [f"attempt-{i}" for i in range(100)]
