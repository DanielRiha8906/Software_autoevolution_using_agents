import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService


def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
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


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


def test_add_and_list(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.list_runs() == [run]


def test_add_duplicate_raises(service):
    run = _make_run()
    service.add_workflow_run(run)
    with pytest.raises(ValueError):
        service.add_workflow_run(run)


def test_get_run_detail(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.get_run_detail("run-1") is run
    assert service.get_run_detail("unknown") is None


def test_filter_by_branch(service):
    r1 = _make_run("r1", "main")
    r2 = _make_run("r2", "dev")
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    assert service.filter_by_branch("main") == [r1]
    assert service.filter_by_branch("dev") == [r2]


def test_filter_by_status(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.filter_by_status(WorkflowStatus.COMPLETED) == [run]
    assert service.filter_by_status(WorkflowStatus.QUEUED) == []


def test_filter_by_conclusion(service):
    run = _make_run()
    service.add_workflow_run(run)
    assert service.filter_by_conclusion(WorkflowConclusion.SUCCESS) == [run]
    assert service.filter_by_conclusion(WorkflowConclusion.FAILURE) == []


# Tests for WorkflowRun state-checking methods


class TestWorkflowRunStateChecking:
    """Test suite for WorkflowRun state-checking methods."""

    def test_is_terminal_with_completed_status(self):
        """Terminal state when status is COMPLETED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_with_non_completed_status(self):
        """Not terminal when status is not COMPLETED."""
        for status in [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]:
            run = WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=status,
                conclusion=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_terminal() is False, f"Should not be terminal with {status}"

    def test_is_running_with_in_progress_status(self):
        """Running state when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is True

    def test_is_running_with_non_in_progress_status(self):
        """Not running when status is not IN_PROGRESS."""
        for status in [
            WorkflowStatus.QUEUED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]:
            run = WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=status,
                conclusion=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_running() is False, f"Should not be running with {status}"

    def test_is_successful_with_success_conclusion(self):
        """Successful state when conclusion is SUCCESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is True

    def test_is_successful_with_non_success_conclusion(self):
        """Not successful when conclusion is not SUCCESS."""
        for conclusion in [
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_successful() is False, f"Should not be successful with {conclusion}"

    def test_is_successful_with_none_conclusion(self):
        """Not successful when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_failed_with_failure_conclusion(self):
        """Failed state when conclusion is FAILURE."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is True

    def test_is_failed_with_non_failure_conclusion(self):
        """Not failed when conclusion is not FAILURE."""
        for conclusion in [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_failed() is False, f"Should not be failed with {conclusion}"

    def test_is_failed_with_none_conclusion(self):
        """Not failed when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_cancelled_with_cancelled_conclusion(self):
        """Cancelled state when conclusion is CANCELLED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is True

    def test_is_cancelled_with_non_cancelled_conclusion(self):
        """Not cancelled when conclusion is not CANCELLED."""
        for conclusion in [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_cancelled() is False, f"Should not be cancelled with {conclusion}"

    def test_is_cancelled_with_none_conclusion(self):
        """Not cancelled when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False

    def test_terminal_and_running_are_mutually_exclusive(self):
        """Terminal and running states are mutually exclusive."""
        # Terminal (completed) with None conclusion
        terminal_run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert terminal_run.is_terminal() is True
        assert terminal_run.is_running() is False

        # Running (in progress) with None conclusion
        running_run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert running_run.is_running() is True
        assert running_run.is_terminal() is False

    def test_successful_and_failed_are_mutually_exclusive(self):
        """Successful and failed states are mutually exclusive."""
        # Successful
        successful_run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert successful_run.is_successful() is True
        assert successful_run.is_failed() is False

        # Failed
        failed_run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert failed_run.is_failed() is True
        assert failed_run.is_successful() is False
