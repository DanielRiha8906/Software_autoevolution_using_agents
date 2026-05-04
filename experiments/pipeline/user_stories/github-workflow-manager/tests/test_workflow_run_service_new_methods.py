"""Tests for new methods in WorkflowRunService: replace_run and delete_run."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 0.0,
) -> WorkflowRun:
    """Create a test WorkflowRun."""
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    """Create a service with mocked storage."""
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


class TestReplaceRun:
    """Tests for replace_run method."""

    def test_replace_run_add_new_run(self, service):
        """replace_run adds run if it doesn't exist."""
        run = _make_run("run-1")
        service.replace_run(run)
        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].id == "run-1"

    def test_replace_run_replace_existing_run(self, service):
        """replace_run replaces existing run with same id."""
        run1 = _make_run("run-1", duration_seconds=10.0)
        service.add_workflow_run(run1)

        run2 = _make_run("run-1", duration_seconds=20.0, workflow_name="CD")
        service.replace_run(run2)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 20.0
        assert runs[0].workflow_name == "CD"

    def test_replace_run_does_not_duplicate(self, service):
        """replace_run does not duplicate when replacing."""
        run1 = _make_run("run-1")
        service.add_workflow_run(run1)

        run2 = _make_run("run-1", branch="dev")
        service.replace_run(run2)

        runs = service.list_runs()
        assert len(runs) == 1

    def test_replace_run_updates_internal_list(self, service):
        """replace_run updates the internal list."""
        run1 = _make_run("run-1", branch="main")
        service.add_workflow_run(run1)

        run2 = _make_run("run-1", branch="dev")
        service.replace_run(run2)

        found = service.get_run_detail("run-1")
        assert found is not None
        assert found.branch == "dev"

    def test_replace_run_calls_persist(self, service):
        """replace_run persists changes to storage."""
        run = _make_run("run-1")
        service.replace_run(run)
        service._storage.save.assert_called()

    def test_replace_run_preserves_other_runs(self, service):
        """replace_run does not affect other runs."""
        run1 = _make_run("run-1")
        run2 = _make_run("run-2")
        run3 = _make_run("run-3")

        service.add_workflow_run(run1)
        service.add_workflow_run(run2)
        service.add_workflow_run(run3)

        new_run2 = _make_run("run-2", workflow_name="NewCD")
        service.replace_run(new_run2)

        runs = service.list_runs()
        assert len(runs) == 3
        # Find the replaced run by id
        replaced = next((r for r in runs if r.id == "run-2"), None)
        assert replaced is not None
        assert replaced.workflow_name == "NewCD"
        # Check other runs are still there
        assert any(r.id == "run-1" for r in runs)
        assert any(r.id == "run-3" for r in runs)

    def test_replace_run_on_empty_service(self, service):
        """replace_run works on empty service."""
        run = _make_run("run-1")
        assert len(service.list_runs()) == 0
        service.replace_run(run)
        assert len(service.list_runs()) == 1

    def test_replace_run_multiple_replacements(self, service):
        """replace_run can replace same run multiple times."""
        run1 = _make_run("run-1", duration_seconds=10.0)
        service.replace_run(run1)

        run2 = _make_run("run-1", duration_seconds=20.0)
        service.replace_run(run2)

        run3 = _make_run("run-1", duration_seconds=30.0)
        service.replace_run(run3)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 30.0


class TestDeleteRun:
    """Tests for delete_run method."""

    def test_delete_run_success(self, service):
        """delete_run returns True when run exists and is deleted."""
        run = _make_run("run-1")
        service.add_workflow_run(run)

        result = service.delete_run("run-1")
        assert result is True
        assert len(service.list_runs()) == 0

    def test_delete_run_not_found(self, service):
        """delete_run returns False when run does not exist."""
        result = service.delete_run("nonexistent")
        assert result is False

    def test_delete_run_calls_persist_on_success(self, service):
        """delete_run calls persist when run is deleted."""
        run = _make_run("run-1")
        service.add_workflow_run(run)
        service._storage.reset_mock()

        service.delete_run("run-1")
        service._storage.save.assert_called()

    def test_delete_run_does_not_persist_on_failure(self, service):
        """delete_run does not call persist when run not found."""
        service._storage.reset_mock()
        service.delete_run("nonexistent")
        service._storage.save.assert_not_called()

    def test_delete_run_preserves_other_runs(self, service):
        """delete_run only removes the target run."""
        run1 = _make_run("run-1")
        run2 = _make_run("run-2")
        run3 = _make_run("run-3")

        service.add_workflow_run(run1)
        service.add_workflow_run(run2)
        service.add_workflow_run(run3)

        result = service.delete_run("run-2")

        assert result is True
        runs = service.list_runs()
        assert len(runs) == 2
        assert runs[0].id == "run-1"
        assert runs[1].id == "run-3"

    def test_delete_run_on_empty_service(self, service):
        """delete_run returns False on empty service."""
        result = service.delete_run("run-1")
        assert result is False
        assert len(service.list_runs()) == 0

    def test_delete_run_multiple_times_same_id(self, service):
        """delete_run returns False on second deletion of same id."""
        run = _make_run("run-1")
        service.add_workflow_run(run)

        result1 = service.delete_run("run-1")
        assert result1 is True

        result2 = service.delete_run("run-1")
        assert result2 is False

    def test_delete_run_with_various_ids(self, service):
        """delete_run works with different id formats."""
        run_int = _make_run("123")
        run_uuid = _make_run("550e8400-e29b-41d4-a716-446655440000")
        run_string = _make_run("my-custom-run")

        service.add_workflow_run(run_int)
        service.add_workflow_run(run_uuid)
        service.add_workflow_run(run_string)

        assert service.delete_run("123") is True
        assert service.delete_run("550e8400-e29b-41d4-a716-446655440000") is True
        assert service.delete_run("my-custom-run") is True
        assert len(service.list_runs()) == 0


class TestReplaceAndDeleteIntegration:
    """Integration tests for replace_run and delete_run together."""

    def test_replace_then_delete(self, service):
        """Can replace a run and then delete it."""
        run1 = _make_run("run-1")
        service.replace_run(run1)
        assert len(service.list_runs()) == 1

        run2 = _make_run("run-1", duration_seconds=50.0)
        service.replace_run(run2)
        assert service.list_runs()[0].duration_seconds == 50.0

        result = service.delete_run("run-1")
        assert result is True
        assert len(service.list_runs()) == 0

    def test_delete_then_replace(self, service):
        """Can delete a run and then replace it."""
        run1 = _make_run("run-1")
        service.add_workflow_run(run1)
        service.delete_run("run-1")
        assert len(service.list_runs()) == 0

        run2 = _make_run("run-1", duration_seconds=100.0)
        service.replace_run(run2)
        assert len(service.list_runs()) == 1
        assert service.list_runs()[0].duration_seconds == 100.0

    def test_replace_preserves_position(self, service):
        """replace_run appends run to end (position may change)."""
        run1 = _make_run("run-1")
        run2 = _make_run("run-2")
        run3 = _make_run("run-3")

        service.add_workflow_run(run1)
        service.add_workflow_run(run2)
        service.add_workflow_run(run3)

        new_run2 = _make_run("run-2", workflow_name="Updated")
        service.replace_run(new_run2)

        runs = service.list_runs()
        # After replace, run-2 should be at the end
        assert runs[-1].id == "run-2"
        assert runs[-1].workflow_name == "Updated"

    def test_concurrent_operations_consistency(self, service):
        """Multiple operations maintain consistency."""
        runs = [_make_run(f"run-{i}") for i in range(5)]
        for run in runs:
            service.add_workflow_run(run)

        assert len(service.list_runs()) == 5

        # Replace some
        service.replace_run(_make_run("run-1", duration_seconds=1.0))
        service.replace_run(_make_run("run-3", duration_seconds=3.0))

        assert len(service.list_runs()) == 5

        # Delete some
        assert service.delete_run("run-0") is True
        assert service.delete_run("run-2") is True

        assert len(service.list_runs()) == 3

        # Add new
        service.add_workflow_run(_make_run("run-10"))

        assert len(service.list_runs()) == 4
