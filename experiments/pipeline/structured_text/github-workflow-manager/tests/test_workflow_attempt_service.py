"""
Tests for WorkflowAttemptService.

Covers:
- CRUD operations (add, list, get, filter)
- Persistence
- Filtering by run_id, status, conclusion
- Duplicate detection
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage
from src.services.workflow_attempt_service import WorkflowAttemptService


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


@pytest.fixture
def service_with_real_storage(temp_storage_path):
    """Create a service with real file-based storage."""
    storage = WorkflowAttemptJsonStorage(temp_storage_path)
    return WorkflowAttemptService(storage)


@pytest.fixture
def service_with_mock_storage():
    """Create a service with mocked storage."""
    storage = MagicMock()
    storage.load.return_value = []
    return WorkflowAttemptService(storage)


class TestWorkflowAttemptServiceAddAttempt:
    """Test add_attempt CRUD operation."""

    def test_add_single_attempt(self, service_with_mock_storage):
        """Test adding a single attempt."""
        service = service_with_mock_storage
        attempt = _make_attempt(attempt_id="attempt-1")
        result = service.add_attempt(attempt)

        assert result is attempt
        assert service.list_attempts() == [attempt]

    def test_add_multiple_attempts(self, service_with_mock_storage):
        """Test adding multiple attempts."""
        service = service_with_mock_storage
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i}", attempt_number=i)
            for i in range(3)
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        listed = service.list_attempts()
        assert len(listed) == 3
        assert listed == attempts

    def test_add_duplicate_id_raises(self, service_with_mock_storage):
        """Test that adding duplicate ID raises ValueError."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="duplicate-id")
        attempt2 = _make_attempt(attempt_id="duplicate-id")

        service.add_attempt(attempt1)
        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(attempt2)
        assert "already exists" in str(exc_info.value).lower()

    def test_add_persists_to_storage(self, service_with_real_storage):
        """Test that add_attempt persists to storage."""
        attempt = _make_attempt(attempt_id="persist-1")
        service_with_real_storage.add_attempt(attempt)

        # Create new service instance (should reload from storage)
        storage = service_with_real_storage._storage
        new_service = WorkflowAttemptService(storage)
        listed = new_service.list_attempts()

        assert len(listed) == 1
        assert listed[0].id == "persist-1"

    def test_add_returns_the_same_attempt(self, service_with_mock_storage):
        """Test that add_attempt returns the exact same object."""
        service = service_with_mock_storage
        attempt = _make_attempt()
        returned = service.add_attempt(attempt)

        assert returned is attempt


class TestWorkflowAttemptServiceListAttempts:
    """Test list_attempts operation."""

    def test_list_empty(self, service_with_mock_storage):
        """Test listing when no attempts exist."""
        assert service_with_mock_storage.list_attempts() == []

    def test_list_returns_copy(self, service_with_mock_storage):
        """Test that list_attempts returns a copy, not internal reference."""
        service = service_with_mock_storage
        attempt = _make_attempt()
        service.add_attempt(attempt)

        list1 = service.list_attempts()
        list2 = service.list_attempts()

        assert list1 == list2
        assert list1 is not list2  # Different list objects

    def test_list_multiple_attempts(self, service_with_mock_storage):
        """Test listing multiple attempts."""
        service = service_with_mock_storage
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i}", attempt_number=i)
            for i in range(5)
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        listed = service.list_attempts()
        assert len(listed) == 5
        for i, attempt in enumerate(listed):
            assert attempt.id == f"attempt-{i}"


class TestWorkflowAttemptServiceGetAttemptDetail:
    """Test get_attempt_detail operation."""

    def test_get_existing_attempt(self, service_with_mock_storage):
        """Test getting an existing attempt."""
        service = service_with_mock_storage
        attempt = _make_attempt(attempt_id="get-test-1")
        service.add_attempt(attempt)

        retrieved = service.get_attempt_detail("get-test-1")
        assert retrieved is attempt

    def test_get_nonexistent_returns_none(self, service_with_mock_storage):
        """Test that getting nonexistent attempt returns None."""
        service = service_with_mock_storage
        retrieved = service.get_attempt_detail("nonexistent")
        assert retrieved is None

    def test_get_with_multiple_attempts(self, service_with_mock_storage):
        """Test getting specific attempt when multiple exist."""
        service = service_with_mock_storage
        attempts = [
            _make_attempt(attempt_id=f"attempt-{i}", run_id=f"run-{i}", attempt_number=i)
            for i in range(5)
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        retrieved = service.get_attempt_detail("attempt-2")
        assert retrieved is not None
        assert retrieved.id == "attempt-2"


class TestWorkflowAttemptServiceFilterByRunId:
    """Test filter_by_run_id operation."""

    def test_filter_by_run_id_single_match(self, service_with_mock_storage):
        """Test filtering by run_id with single match."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1")
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-2")
        service.add_attempt(attempt1)
        service.add_attempt(attempt2)

        filtered = service.filter_by_run_id("run-1")
        assert len(filtered) == 1
        assert filtered[0].id == "a1"

    def test_filter_by_run_id_multiple_matches(self, service_with_mock_storage):
        """Test filtering by run_id with multiple matches."""
        service = service_with_mock_storage
        attempts = [
            _make_attempt(attempt_id=f"a{i}", run_id="run-1", attempt_number=i)
            for i in range(3)
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        assert len(filtered) == 3
        assert all(a.run_id == "run-1" for a in filtered)

    def test_filter_by_run_id_no_matches(self, service_with_mock_storage):
        """Test filtering by run_id with no matches."""
        service = service_with_mock_storage
        attempt = _make_attempt(run_id="run-1")
        service.add_attempt(attempt)

        filtered = service.filter_by_run_id("nonexistent-run")
        assert filtered == []

    def test_filter_by_run_id_empty_service(self, service_with_mock_storage):
        """Test filtering by run_id in empty service."""
        filtered = service_with_mock_storage.filter_by_run_id("run-1")
        assert filtered == []


class TestWorkflowAttemptServiceFilterByStatus:
    """Test filter_by_status operation."""

    def test_filter_by_status_single_match(self, service_with_mock_storage):
        """Test filtering by status with single match."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1, status=WorkflowStatus.COMPLETED)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-2", attempt_number=1, status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        service.add_attempt(attempt1)
        service.add_attempt(attempt2)

        filtered = service.filter_by_status(WorkflowStatus.COMPLETED)
        assert len(filtered) == 1
        assert filtered[0].id == "a1"

    def test_filter_by_status_multiple_matches(self, service_with_mock_storage):
        """Test filtering by status with multiple matches."""
        service = service_with_mock_storage
        for i in range(3):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id=f"run-{i}",
                attempt_number=i,
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS if i % 2 == 0 else WorkflowConclusion.FAILURE,
            )
            service.add_attempt(attempt)

        filtered = service.filter_by_status(WorkflowStatus.COMPLETED)
        assert len(filtered) == 3
        assert all(a.status == WorkflowStatus.COMPLETED for a in filtered)

    def test_filter_by_status_all_status_values(self, service_with_mock_storage):
        """Test filtering by all possible status values."""
        service = service_with_mock_storage

        for i, status in enumerate(WorkflowStatus):
            conclusion = WorkflowConclusion.SUCCESS if status == WorkflowStatus.COMPLETED else None
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id=f"run-{i}",
                attempt_number=i,
                status=status,
                conclusion=conclusion,
            )
            service.add_attempt(attempt)

        for status in WorkflowStatus:
            filtered = service.filter_by_status(status)
            assert len(filtered) == 1
            assert filtered[0].status == status


class TestWorkflowAttemptServiceFilterByConclusion:
    """Test filter_by_conclusion operation."""

    def test_filter_by_conclusion_single_match(self, service_with_mock_storage):
        """Test filtering by conclusion with single match."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1, conclusion=WorkflowConclusion.SUCCESS)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-2", attempt_number=1, conclusion=WorkflowConclusion.FAILURE)
        service.add_attempt(attempt1)
        service.add_attempt(attempt2)

        filtered = service.filter_by_conclusion(WorkflowConclusion.SUCCESS)
        assert len(filtered) == 1
        assert filtered[0].id == "a1"

    def test_filter_by_conclusion_multiple_matches(self, service_with_mock_storage):
        """Test filtering by conclusion with multiple matches."""
        service = service_with_mock_storage
        for i in range(3):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id=f"run-{i}",
                attempt_number=i,
                conclusion=WorkflowConclusion.FAILURE,
            )
            service.add_attempt(attempt)

        filtered = service.filter_by_conclusion(WorkflowConclusion.FAILURE)
        assert len(filtered) == 3

    def test_filter_by_conclusion_no_matches(self, service_with_mock_storage):
        """Test filtering by conclusion with no matches."""
        service = service_with_mock_storage
        attempt = _make_attempt(conclusion=WorkflowConclusion.SUCCESS)
        service.add_attempt(attempt)

        filtered = service.filter_by_conclusion(WorkflowConclusion.FAILURE)
        assert filtered == []

    def test_filter_by_conclusion_all_conclusion_values(self, service_with_mock_storage):
        """Test filtering by all possible conclusion values."""
        service = service_with_mock_storage

        for i, conclusion in enumerate(WorkflowConclusion):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id=f"run-{i}",
                attempt_number=i,
                conclusion=conclusion,
            )
            service.add_attempt(attempt)

        for conclusion in WorkflowConclusion:
            filtered = service.filter_by_conclusion(conclusion)
            assert len(filtered) == 1
            assert filtered[0].conclusion == conclusion


class TestWorkflowAttemptServiceCombinedFiltering:
    """Test combining multiple filters."""

    def test_filter_chaining(self, service_with_mock_storage):
        """Test chaining multiple filters."""
        service = service_with_mock_storage

        # Add attempts with different combinations
        a1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1, status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        a2 = _make_attempt(attempt_id="a2", run_id="run-1", attempt_number=2, status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        a3 = _make_attempt(attempt_id="a3", run_id="run-2", attempt_number=1, status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)

        for attempt in [a1, a2, a3]:
            service.add_attempt(attempt)

        # Filter by run_id
        by_run = service.filter_by_run_id("run-1")
        assert len(by_run) == 2

        # Filter by conclusion from that subset
        success_in_run1 = [a for a in by_run if a.conclusion == WorkflowConclusion.SUCCESS]
        assert len(success_in_run1) == 1
        assert success_in_run1[0].id == "a1"


class TestWorkflowAttemptServiceInitialization:
    """Test service initialization and storage interaction."""

    def test_loads_from_storage_on_init(self, temp_storage_path):
        """Test that service loads existing data from storage on init."""
        # Create and populate storage
        storage1 = WorkflowAttemptJsonStorage(temp_storage_path)
        attempts = [_make_attempt(attempt_id=f"a{i}") for i in range(3)]
        storage1.save(attempts)

        # Create new service (should load from storage)
        storage2 = WorkflowAttemptJsonStorage(temp_storage_path)
        service = WorkflowAttemptService(storage2)

        listed = service.list_attempts()
        assert len(listed) == 3
        assert [a.id for a in listed] == ["a0", "a1", "a2"]

    def test_empty_storage_on_init(self, temp_storage_path):
        """Test that service handles empty storage on init."""
        storage = WorkflowAttemptJsonStorage(temp_storage_path)
        service = WorkflowAttemptService(storage)

        assert service.list_attempts() == []


class TestWorkflowAttemptServiceDuplicateRunIdAttemptNumber:
    """Test duplicate (run_id, attempt_number) validation in add_attempt."""

    def test_duplicate_run_id_and_attempt_number_raises(self, service_with_mock_storage):
        """Test that adding duplicate (run_id, attempt_number) raises ValueError."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-1", attempt_number=1)

        service.add_attempt(attempt1)
        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(attempt2)
        assert "Attempt number" in str(exc_info.value)
        assert "run-1" in str(exc_info.value)

    def test_duplicate_error_message_contains_run_id_and_attempt_number(self, service_with_mock_storage):
        """Test error message contains both run_id and attempt_number."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-xyz", attempt_number=5)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-xyz", attempt_number=5)

        service.add_attempt(attempt1)
        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(attempt2)
        error_msg = str(exc_info.value)
        assert "run-xyz" in error_msg
        assert "5" in error_msg

    def test_same_run_id_different_attempt_numbers_allowed(self, service_with_mock_storage):
        """Test that same run_id with different attempt_numbers is allowed."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-1", attempt_number=2)
        attempt3 = _make_attempt(attempt_id="a3", run_id="run-1", attempt_number=3)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        listed = service.list_attempts()
        assert len(listed) == 3
        assert all(a.run_id == "run-1" for a in listed)

    def test_same_attempt_number_different_run_ids_allowed(self, service_with_mock_storage):
        """Test that same attempt_number in different run_ids is allowed."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-2", attempt_number=1)
        attempt3 = _make_attempt(attempt_id="a3", run_id="run-3", attempt_number=1)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        listed = service.list_attempts()
        assert len(listed) == 3
        assert all(a.attempt_number == 1 for a in listed)

    def test_duplicate_id_validation_still_works(self, service_with_mock_storage):
        """Test that duplicate ID validation still works (not replaced by run_id+attempt_number check)."""
        service = service_with_mock_storage
        attempt1 = _make_attempt(attempt_id="same-id", run_id="run-1", attempt_number=1)
        attempt2 = _make_attempt(attempt_id="same-id", run_id="run-2", attempt_number=1)

        service.add_attempt(attempt1)
        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(attempt2)
        assert "id" in str(exc_info.value).lower()
        assert "same-id" in str(exc_info.value)

    def test_duplicate_run_id_attempt_number_persists_after_reload(self, service_with_real_storage):
        """Test that duplicate detection works after reload from storage."""
        attempt1 = _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1)
        service_with_real_storage.add_attempt(attempt1)

        # Reload service from storage
        storage = service_with_real_storage._storage
        reloaded_service = WorkflowAttemptService(storage)

        # Try to add duplicate (run_id, attempt_number)
        attempt2 = _make_attempt(attempt_id="a2", run_id="run-1", attempt_number=1)
        with pytest.raises(ValueError) as exc_info:
            reloaded_service.add_attempt(attempt2)
        assert "Attempt number" in str(exc_info.value)

    def test_multiple_runs_with_overlapping_attempt_numbers(self, service_with_mock_storage):
        """Test mixed runs with overlapping attempt_numbers are handled correctly."""
        service = service_with_mock_storage

        # Add attempts with same attempt_number but different run_ids
        a1 = _make_attempt(attempt_id="a1", run_id="run-alpha", attempt_number=1)
        a2 = _make_attempt(attempt_id="a2", run_id="run-alpha", attempt_number=2)
        a3 = _make_attempt(attempt_id="a3", run_id="run-beta", attempt_number=1)
        a4 = _make_attempt(attempt_id="a4", run_id="run-beta", attempt_number=2)

        service.add_attempt(a1)
        service.add_attempt(a2)
        service.add_attempt(a3)
        service.add_attempt(a4)

        # Should be able to add these without conflict
        listed = service.list_attempts()
        assert len(listed) == 4

        # Verify that duplicates within each run are still rejected
        dup_a2 = _make_attempt(attempt_id="dup", run_id="run-alpha", attempt_number=2)
        with pytest.raises(ValueError):
            service.add_attempt(dup_a2)


class TestWorkflowAttemptServiceFilterByRunIdSorting:
    """Test filter_by_run_id returns sorted results by attempt_number."""

    def test_filter_returns_sorted_by_attempt_number_sequential(self, service_with_mock_storage):
        """Test filter_by_run_id returns attempts sorted by attempt_number (sequential)."""
        service = service_with_mock_storage

        # Add in non-sequential order
        attempts = [
            _make_attempt(attempt_id="a3", run_id="run-1", attempt_number=3),
            _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1),
            _make_attempt(attempt_id="a2", run_id="run-1", attempt_number=2),
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        assert len(filtered) == 3
        assert [a.attempt_number for a in filtered] == [1, 2, 3]
        assert [a.id for a in filtered] == ["a1", "a2", "a3"]

    def test_filter_returns_sorted_by_attempt_number_non_sequential(self, service_with_mock_storage):
        """Test filter_by_run_id returns attempts sorted with non-sequential numbers."""
        service = service_with_mock_storage

        # Add in scrambled order
        attempts = [
            _make_attempt(attempt_id="a5", run_id="run-1", attempt_number=5),
            _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1),
            _make_attempt(attempt_id="a3", run_id="run-1", attempt_number=3),
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        assert len(filtered) == 3
        assert [a.attempt_number for a in filtered] == [1, 3, 5]
        assert [a.id for a in filtered] == ["a1", "a3", "a5"]

    def test_filter_returns_sorted_unsorted_input(self, service_with_mock_storage):
        """Test filter_by_run_id sorts attempts when added in reverse order."""
        service = service_with_mock_storage

        # Add in reverse order
        for i in range(10, 0, -1):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id="run-1",
                attempt_number=i
            )
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        assert len(filtered) == 10
        assert [a.attempt_number for a in filtered] == list(range(1, 11))

    def test_filter_empty_result_returns_empty_list(self, service_with_mock_storage):
        """Test filter_by_run_id returns empty list when no matches (no error)."""
        service = service_with_mock_storage

        # Add some attempts to different run
        for i in range(3):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id="run-1",
                attempt_number=i + 1
            )
            service.add_attempt(attempt)

        # Filter for different run
        filtered = service.filter_by_run_id("nonexistent-run")
        assert filtered == []
        assert isinstance(filtered, list)

    def test_filter_sorting_with_gaps_in_attempt_numbers(self, service_with_mock_storage):
        """Test filter_by_run_id correctly sorts with gaps (1, 3, 7, 10)."""
        service = service_with_mock_storage

        attempts = [
            _make_attempt(attempt_id="a10", run_id="run-1", attempt_number=10),
            _make_attempt(attempt_id="a3", run_id="run-1", attempt_number=3),
            _make_attempt(attempt_id="a1", run_id="run-1", attempt_number=1),
            _make_attempt(attempt_id="a7", run_id="run-1", attempt_number=7),
        ]
        for attempt in attempts:
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        assert [a.attempt_number for a in filtered] == [1, 3, 7, 10]

    def test_filter_sorting_ignores_other_runs(self, service_with_mock_storage):
        """Test filter_by_run_id sorting only applies to filtered run."""
        service = service_with_mock_storage

        # Add to multiple runs in mixed order
        service.add_attempt(_make_attempt(attempt_id="a1", run_id="run-1", attempt_number=2))
        service.add_attempt(_make_attempt(attempt_id="a2", run_id="run-2", attempt_number=2))
        service.add_attempt(_make_attempt(attempt_id="a3", run_id="run-1", attempt_number=1))
        service.add_attempt(_make_attempt(attempt_id="a4", run_id="run-2", attempt_number=1))

        # Filter run-1
        filtered_run1 = service.filter_by_run_id("run-1")
        assert [a.attempt_number for a in filtered_run1] == [1, 2]
        assert all(a.run_id == "run-1" for a in filtered_run1)

        # Filter run-2
        filtered_run2 = service.filter_by_run_id("run-2")
        assert [a.attempt_number for a in filtered_run2] == [1, 2]
        assert all(a.run_id == "run-2" for a in filtered_run2)

    @pytest.mark.parametrize("attempt_numbers", [
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [3, 1, 4, 6, 5, 9, 2, 7],
        [100, 1, 50],
        [1],
    ])
    def test_filter_sorting_parametrized(self, service_with_mock_storage, attempt_numbers):
        """Parametrized test for filter_by_run_id sorting with various attempt_number sequences."""
        service = service_with_mock_storage

        # Add attempts with given numbers in given order
        for i, num in enumerate(attempt_numbers):
            attempt = _make_attempt(
                attempt_id=f"a{i}",
                run_id="run-1",
                attempt_number=num
            )
            service.add_attempt(attempt)

        filtered = service.filter_by_run_id("run-1")
        result_numbers = [a.attempt_number for a in filtered]

        # Should be sorted in ascending order
        assert result_numbers == sorted(attempt_numbers)
