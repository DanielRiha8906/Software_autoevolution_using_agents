"""
Tests for WorkflowRunTracker.create_attempt() method.

Covers:
- create_attempt basic functionality
- Generated IDs (UUID)
- Timestamp generation (started_at)
- Validation (attempt_number, duration_seconds)
- RuntimeError when attempt_service is None
- Integration with WorkflowAttemptService
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID

from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_tracker import WorkflowRunTracker
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_attempt_service import WorkflowAttemptService
from src.storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage


@pytest.fixture
def temp_storage_path():
    """Create a temporary file path for storage testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = str(Path(tmpdir) / "attempts.json")
        yield filepath


@pytest.fixture
def tracker_with_mock_services():
    """Create a tracker with mocked services."""
    run_service = MagicMock()
    run_service.load.return_value = []
    run_service.add_workflow_run = MagicMock()

    attempt_service = MagicMock()
    attempt_service.load.return_value = []
    attempt_service.add_attempt = MagicMock(side_effect=lambda a: a)

    tracker = WorkflowRunTracker(run_service, attempt_service)
    return tracker


@pytest.fixture
def tracker_with_real_services(temp_storage_path):
    """Create a tracker with real file-based services."""
    run_storage = MagicMock()
    run_storage.load.return_value = []
    run_service = WorkflowRunService(run_storage)

    attempt_storage = WorkflowAttemptJsonStorage(temp_storage_path)
    attempt_service = WorkflowAttemptService(attempt_storage)

    tracker = WorkflowRunTracker(run_service, attempt_service)
    return tracker


class TestWorkflowRunTrackerCreateAttemptBasic:
    """Test basic create_attempt functionality."""

    def test_create_attempt_minimal_args(self, tracker_with_mock_services):
        """Test creating attempt with minimal required arguments."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
        )

        assert attempt.id is not None
        assert attempt.run_id == "run-1"
        assert attempt.attempt_number == 1
        assert attempt.status == WorkflowStatus.COMPLETED
        assert attempt.conclusion is None
        assert attempt.started_at is not None
        assert attempt.completed_at is None
        assert attempt.duration_seconds == 0.0
        assert attempt.logs_url is None

    def test_create_attempt_with_all_args(self, tracker_with_mock_services):
        """Test creating attempt with all arguments."""
        tracker = tracker_with_mock_services
        now = datetime.now(timezone.utc)

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            completed_at=now,
            duration_seconds=120.5,
            logs_url="https://example.com/logs",
            attempt_id="custom-id-123",
        )

        assert attempt.id == "custom-id-123"
        assert attempt.run_id == "run-1"
        assert attempt.attempt_number == 2
        assert attempt.status == WorkflowStatus.COMPLETED
        assert attempt.conclusion == WorkflowConclusion.SUCCESS
        assert attempt.completed_at == now
        assert attempt.duration_seconds == 120.5
        assert attempt.logs_url == "https://example.com/logs"

    def test_create_attempt_returns_stored_attempt(self, tracker_with_real_services):
        """Test that create_attempt returns the stored attempt."""
        tracker = tracker_with_real_services

        returned = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )

        # Verify the attempt was actually stored
        service = tracker._attempt_service
        listed = service.list_attempts()
        assert len(listed) == 1
        assert listed[0].id == returned.id


class TestWorkflowRunTrackerCreateAttemptIdGeneration:
    """Test ID generation behavior."""

    def test_generated_id_is_uuid(self, tracker_with_mock_services):
        """Test that generated ID is a valid UUID."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
        )

        # Should be a valid UUID string
        try:
            UUID(attempt.id)
        except ValueError:
            pytest.fail(f"Generated ID '{attempt.id}' is not a valid UUID")

    def test_generated_ids_are_unique(self, tracker_with_mock_services):
        """Test that generated IDs are unique."""
        tracker = tracker_with_mock_services

        attempt1 = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
        )
        attempt2 = tracker.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status=WorkflowStatus.COMPLETED,
        )

        assert attempt1.id != attempt2.id

    def test_custom_id_used_when_provided(self, tracker_with_mock_services):
        """Test that custom ID is used when provided."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            attempt_id="my-custom-id",
        )

        assert attempt.id == "my-custom-id"


class TestWorkflowRunTrackerCreateAttemptTimestamp:
    """Test timestamp generation."""

    def test_started_at_is_generated(self, tracker_with_mock_services):
        """Test that started_at is automatically generated."""
        tracker = tracker_with_mock_services
        before = datetime.now(timezone.utc)

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
        )

        after = datetime.now(timezone.utc)
        assert before <= attempt.started_at <= after

    def test_started_at_is_in_utc(self, tracker_with_mock_services):
        """Test that started_at is in UTC timezone."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
        )

        assert attempt.started_at.tzinfo == timezone.utc

    def test_completed_at_none_by_default(self, tracker_with_mock_services):
        """Test that completed_at is None by default."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.IN_PROGRESS,
        )

        assert attempt.completed_at is None

    def test_completed_at_can_be_set(self, tracker_with_mock_services):
        """Test that completed_at can be explicitly set."""
        tracker = tracker_with_mock_services
        now = datetime.now(timezone.utc)

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            completed_at=now,
        )

        assert attempt.completed_at == now


class TestWorkflowRunTrackerCreateAttemptValidation:
    """Test validation of attempt creation."""

    def test_create_attempt_with_zero_duration(self, tracker_with_mock_services):
        """Test creating attempt with zero duration."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            duration_seconds=0.0,
        )

        assert attempt.duration_seconds == 0.0

    def test_create_attempt_with_large_duration(self, tracker_with_mock_services):
        """Test creating attempt with large duration."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            duration_seconds=999999.99,
        )

        assert attempt.duration_seconds == 999999.99

    def test_create_attempt_all_status_values(self, tracker_with_mock_services):
        """Test creating attempts with all possible status values."""
        tracker = tracker_with_mock_services

        for i, status in enumerate(WorkflowStatus):
            conclusion = WorkflowConclusion.SUCCESS if status == WorkflowStatus.COMPLETED else None
            attempt = tracker.create_attempt(
                run_id="run-1",
                attempt_number=i + 1,
                status=status,
                conclusion=conclusion,
            )

            assert attempt.status == status

    def test_create_attempt_all_conclusion_values(self, tracker_with_mock_services):
        """Test creating attempts with all possible conclusion values."""
        tracker = tracker_with_mock_services

        for i, conclusion in enumerate(WorkflowConclusion):
            attempt = tracker.create_attempt(
                run_id="run-1",
                attempt_number=i + 1,
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
            )

            assert attempt.conclusion == conclusion


class TestWorkflowRunTrackerCreateAttemptRuntimeError:
    """Test RuntimeError when attempt_service is not initialized."""

    def test_create_attempt_without_service_raises(self):
        """Test that create_attempt raises RuntimeError when attempt_service is None."""
        run_service = MagicMock()
        tracker = WorkflowRunTracker(run_service, attempt_service=None)

        with pytest.raises(RuntimeError) as exc_info:
            tracker.create_attempt(
                run_id="run-1",
                attempt_number=1,
                status=WorkflowStatus.COMPLETED,
            )

        assert "not initialized" in str(exc_info.value).lower()


class TestWorkflowRunTrackerCreateAttemptIntegration:
    """Test integration with WorkflowAttemptService."""

    def test_created_attempt_is_stored(self, tracker_with_real_services):
        """Test that created attempt is persisted to storage."""
        tracker = tracker_with_real_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )

        # Retrieve from service
        service = tracker._attempt_service
        retrieved = service.get_attempt_detail(attempt.id)

        assert retrieved is not None
        assert retrieved.id == attempt.id
        assert retrieved.run_id == "run-1"
        assert retrieved.status == WorkflowStatus.COMPLETED
        assert retrieved.conclusion == WorkflowConclusion.SUCCESS

    def test_multiple_attempts_for_same_run(self, tracker_with_real_services):
        """Test creating multiple attempts for the same run."""
        tracker = tracker_with_real_services

        attempt1 = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
        )
        attempt2 = tracker.create_attempt(
            run_id="run-1",
            attempt_number=2,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )

        # Both should be accessible
        service = tracker._attempt_service
        by_run = service.filter_by_run_id("run-1")
        assert len(by_run) == 2
        assert {a.attempt_number for a in by_run} == {1, 2}

    def test_attempts_for_different_runs(self, tracker_with_real_services):
        """Test creating attempts for different runs."""
        tracker = tracker_with_real_services

        attempt1 = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        attempt2 = tracker.create_attempt(
            run_id="run-2",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
        )

        # Each should be accessible by run_id
        service = tracker._attempt_service
        by_run1 = service.filter_by_run_id("run-1")
        by_run2 = service.filter_by_run_id("run-2")

        assert len(by_run1) == 1
        assert len(by_run2) == 1
        assert by_run1[0].run_id == "run-1"
        assert by_run2[0].run_id == "run-2"


class TestWorkflowRunTrackerCreateAttemptParametrized:
    """Parametrized tests for create_attempt variations."""

    @pytest.mark.parametrize("attempt_number", [1, 2, 5, 100])
    def test_create_attempt_various_numbers(self, tracker_with_mock_services, attempt_number):
        """Test creating attempts with various attempt numbers."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=attempt_number,
            status=WorkflowStatus.COMPLETED,
        )

        assert attempt.attempt_number == attempt_number

    @pytest.mark.parametrize("duration", [0.0, 1.0, 10.5, 3600.0, 999999.99])
    def test_create_attempt_various_durations(self, tracker_with_mock_services, duration):
        """Test creating attempts with various durations."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.COMPLETED,
            duration_seconds=duration,
        )

        assert attempt.duration_seconds == duration

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.QUEUED, None),
        (WorkflowStatus.IN_PROGRESS, None),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
    ])
    def test_create_attempt_status_conclusion_pairs(self, tracker_with_mock_services, status, conclusion):
        """Test creating attempts with various status/conclusion pairs."""
        tracker = tracker_with_mock_services

        attempt = tracker.create_attempt(
            run_id="run-1",
            attempt_number=1,
            status=status,
            conclusion=conclusion,
        )

        assert attempt.status == status
        assert attempt.conclusion == conclusion
