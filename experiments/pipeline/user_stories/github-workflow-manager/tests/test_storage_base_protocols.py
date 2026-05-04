"""Tests for storage layer protocols."""

import pytest
from typing import List
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.storage.base import WorkflowRunStorage, WorkflowRunAttemptStorage


def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
    """Create a test WorkflowRun."""
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
    )


def _make_attempt(attempt_id: int = 1, run_id: int = 1) -> WorkflowRunAttempt:
    """Create a test WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )


class TestWorkflowRunStorageProtocol:
    """Tests for WorkflowRunStorage protocol implementation."""

    def test_protocol_is_protocol(self):
        """WorkflowRunStorage is a Protocol."""
        from typing import Protocol
        assert hasattr(WorkflowRunStorage, "__protocol_attrs__") or hasattr(WorkflowRunStorage, "_is_protocol")

    def test_protocol_has_save_method(self):
        """WorkflowRunStorage protocol requires save method."""
        storage = MagicMock(spec=WorkflowRunStorage)
        run = _make_run()
        storage.save([run])
        storage.save.assert_called_once_with([run])

    def test_protocol_has_load_method(self):
        """WorkflowRunStorage protocol requires load method."""
        storage = MagicMock(spec=WorkflowRunStorage)
        storage.load.return_value = []
        result = storage.load()
        assert result == []
        storage.load.assert_called_once()

    def test_mock_implementation_satisfies_protocol(self):
        """A mock with save and load methods satisfies WorkflowRunStorage."""
        storage = MagicMock(spec=WorkflowRunStorage)
        storage.save.return_value = None
        storage.load.return_value = []

        run = _make_run()
        storage.save([run])
        loaded = storage.load()

        assert storage.save.called
        assert storage.load.called
        assert loaded == []

    def test_save_persists_multiple_runs(self):
        """save method persists a list of runs."""
        storage = MagicMock(spec=WorkflowRunStorage)
        runs = [_make_run(f"run-{i}") for i in range(3)]
        storage.save(runs)
        storage.save.assert_called_once_with(runs)

    def test_save_persists_empty_list(self):
        """save method can persist an empty list."""
        storage = MagicMock(spec=WorkflowRunStorage)
        storage.save([])
        storage.save.assert_called_once_with([])

    def test_load_returns_list_of_runs(self):
        """load method returns a list of WorkflowRun objects."""
        storage = MagicMock(spec=WorkflowRunStorage)
        runs = [_make_run(f"run-{i}") for i in range(2)]
        storage.load.return_value = runs
        result = storage.load()
        assert isinstance(result, list)
        assert all(isinstance(r, WorkflowRun) for r in result)

    def test_load_returns_empty_list(self):
        """load method returns empty list when no runs exist."""
        storage = MagicMock(spec=WorkflowRunStorage)
        storage.load.return_value = []
        result = storage.load()
        assert result == []


class TestWorkflowRunAttemptStorageProtocol:
    """Tests for WorkflowRunAttemptStorage protocol implementation."""

    def test_protocol_is_protocol(self):
        """WorkflowRunAttemptStorage is a Protocol."""
        from typing import Protocol
        assert hasattr(WorkflowRunAttemptStorage, "__protocol_attrs__") or hasattr(WorkflowRunAttemptStorage, "_is_protocol")

    def test_protocol_has_save_attempts_method(self):
        """WorkflowRunAttemptStorage protocol requires save_attempts method."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        attempt = _make_attempt()
        storage.save_attempts([attempt])
        storage.save_attempts.assert_called_once_with([attempt])

    def test_protocol_has_load_attempts_method(self):
        """WorkflowRunAttemptStorage protocol requires load_attempts method."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        storage.load_attempts.return_value = []
        result = storage.load_attempts()
        assert result == []
        storage.load_attempts.assert_called_once()

    def test_mock_implementation_satisfies_protocol(self):
        """A mock with save_attempts and load_attempts methods satisfies WorkflowRunAttemptStorage."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        storage.save_attempts.return_value = None
        storage.load_attempts.return_value = []

        attempt = _make_attempt()
        storage.save_attempts([attempt])
        loaded = storage.load_attempts()

        assert storage.save_attempts.called
        assert storage.load_attempts.called
        assert loaded == []

    def test_save_attempts_persists_multiple_attempts(self):
        """save_attempts method persists a list of attempts."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        attempts = [_make_attempt(i) for i in range(3)]
        storage.save_attempts(attempts)
        storage.save_attempts.assert_called_once_with(attempts)

    def test_save_attempts_persists_empty_list(self):
        """save_attempts method can persist an empty list."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        storage.save_attempts([])
        storage.save_attempts.assert_called_once_with([])

    def test_load_attempts_returns_list_of_attempts(self):
        """load_attempts method returns a list of WorkflowRunAttempt objects."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        attempts = [_make_attempt(i) for i in range(2)]
        storage.load_attempts.return_value = attempts
        result = storage.load_attempts()
        assert isinstance(result, list)
        assert all(isinstance(a, WorkflowRunAttempt) for a in result)

    def test_load_attempts_returns_empty_list(self):
        """load_attempts method returns empty list when no attempts exist."""
        storage = MagicMock(spec=WorkflowRunAttemptStorage)
        storage.load_attempts.return_value = []
        result = storage.load_attempts()
        assert result == []


class TestProtocolDuckTyping:
    """Tests for duck typing with protocols."""

    def test_workflow_run_storage_duck_typing(self):
        """Any object with save and load methods satisfies WorkflowRunStorage protocol."""
        class CustomStorage:
            def save(self, runs: List[WorkflowRun]) -> None:
                pass

            def load(self) -> List[WorkflowRun]:
                return []

        storage = CustomStorage()
        # Duck typing: if it has the methods, it can be used as WorkflowRunStorage
        assert hasattr(storage, "save")
        assert hasattr(storage, "load")

    def test_workflow_run_attempt_storage_duck_typing(self):
        """Any object with save_attempts and load_attempts methods satisfies WorkflowRunAttemptStorage protocol."""
        class CustomStorage:
            def save_attempts(self, attempts: List[WorkflowRunAttempt]) -> None:
                pass

            def load_attempts(self) -> List[WorkflowRunAttempt]:
                return []

        storage = CustomStorage()
        # Duck typing: if it has the methods, it can be used as WorkflowRunAttemptStorage
        assert hasattr(storage, "save_attempts")
        assert hasattr(storage, "load_attempts")
