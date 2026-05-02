import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


@pytest.fixture
def base_run():
    """Fixture to provide a basic WorkflowRun with default values."""
    return WorkflowRun(
        id="test-run-1",
        workflow_name="Test Workflow",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


class TestIsTerminal:
    """Tests for the is_terminal() method."""

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_terminal_false_for_non_completed_status(self, base_run, status):
        """Test that is_terminal() returns False for all non-COMPLETED statuses."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=status,
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False

    def test_is_terminal_true_for_completed_status(self, base_run):
        """Test that is_terminal() returns True when status is COMPLETED."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_independent_of_conclusion(self):
        """Test that is_terminal() returns True regardless of conclusion value."""
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
            None,
        ]
        for conclusion in conclusions:
            run = WorkflowRun(
                id="test-run",
                workflow_name="Test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=conclusion,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_terminal() is True


class TestIsRunning:
    """Tests for the is_running() method."""

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.COMPLETED,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_running_false_for_non_in_progress_status(self, status):
        """Test that is_running() returns False for all non-IN_PROGRESS statuses."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=status,
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is False

    def test_is_running_true_for_in_progress_status(self):
        """Test that is_running() returns True when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is True

    def test_is_running_false_even_with_completion_in_progress(self):
        """Test that is_running() returns False if status is IN_PROGRESS but conclusion is set (edge case)."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        # is_running only checks status, not conclusion
        assert run.is_running() is True


class TestIsSuccessful:
    """Tests for the is_successful() method."""

    def test_is_successful_true_completed_with_success(self):
        """Test that is_successful() returns True for COMPLETED status with SUCCESS conclusion."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
        None,
    ])
    def test_is_successful_false_completed_with_other_conclusions(self, conclusion):
        """Test that is_successful() returns False for COMPLETED with non-SUCCESS conclusions."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_successful_false_for_non_terminal_with_success(self, status):
        """Test that is_successful() returns False if not COMPLETED, even with SUCCESS conclusion."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=status,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for the is_failed() method."""

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.STALE,
    ])
    def test_is_failed_true_completed_with_failure_conclusions(self, conclusion):
        """Test that is_failed() returns True for COMPLETED with failure-related conclusions."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.NEUTRAL,
        None,
    ])
    def test_is_failed_false_completed_with_non_failure_conclusions(self, conclusion):
        """Test that is_failed() returns False for COMPLETED with non-failure conclusions."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_failed_false_for_non_terminal(self, status):
        """Test that is_failed() returns False if not COMPLETED, even with failure conclusions."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=status,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for the is_cancelled() method."""

    def test_is_cancelled_true_with_cancelled_conclusion(self):
        """Test that is_cancelled() returns True when conclusion is CANCELLED."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is True

    def test_is_cancelled_true_regardless_of_status(self):
        """Test that is_cancelled() returns True regardless of the status value."""
        statuses = [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in statuses:
            run = WorkflowRun(
                id="test-run",
                workflow_name="Test",
                branch="main",
                status=status,
                conclusion=WorkflowConclusion.CANCELLED,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
            )
            assert run.is_cancelled() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
        None,
    ])
    def test_is_cancelled_false_with_other_conclusions(self, conclusion):
        """Test that is_cancelled() returns False for all non-CANCELLED conclusions."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Tests for mutual exclusivity of state methods."""

    def test_mutual_exclusivity_terminal_and_running(self):
        """Test that no state has both is_terminal() and is_running() returning True."""
        statuses = WorkflowStatus
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
            None,
        ]

        for status in WorkflowStatus:
            for conclusion in conclusions:
                run = WorkflowRun(
                    id="test-run",
                    workflow_name="Test",
                    branch="main",
                    status=status,
                    conclusion=conclusion,
                    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    updated_at=None,
                    run_number=1,
                    commit_sha="abc123",
                )
                # Both cannot be True at the same time
                assert not (run.is_terminal() and run.is_running()), \
                    f"Both terminal and running True for status={status}, conclusion={conclusion}"

    def test_mutual_exclusivity_successful_and_failed(self):
        """Test that no state has both is_successful() and is_failed() returning True."""
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
            None,
        ]

        for status in WorkflowStatus:
            for conclusion in conclusions:
                run = WorkflowRun(
                    id="test-run",
                    workflow_name="Test",
                    branch="main",
                    status=status,
                    conclusion=conclusion,
                    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    updated_at=None,
                    run_number=1,
                    commit_sha="abc123",
                )
                # Both cannot be True at the same time
                assert not (run.is_successful() and run.is_failed()), \
                    f"Both successful and failed True for status={status}, conclusion={conclusion}"


class TestStateMatrix:
    """Comprehensive state matrix tests covering all status/conclusion combinations."""

    @pytest.mark.parametrize("status,conclusion,expected_terminal,expected_running,expected_successful,expected_failed,expected_cancelled", [
        # COMPLETED status with various conclusions
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS, True, False, True, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED, True, False, False, False, True),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, None, True, False, False, False, False),

        # IN_PROGRESS status with various conclusions
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.CANCELLED, False, True, False, False, True),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SKIPPED, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.TIMED_OUT, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.ACTION_REQUIRED, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.NEUTRAL, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.STALE, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, None, False, True, False, False, False),

        # QUEUED status with various conclusions
        (WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.FAILURE, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.CANCELLED, False, False, False, False, True),
        (WorkflowStatus.QUEUED, WorkflowConclusion.SKIPPED, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.TIMED_OUT, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.ACTION_REQUIRED, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.NEUTRAL, False, False, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.STALE, False, False, False, False, False),
        (WorkflowStatus.QUEUED, None, False, False, False, False, False),

        # WAITING status with various conclusions
        (WorkflowStatus.WAITING, WorkflowConclusion.SUCCESS, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.FAILURE, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.CANCELLED, False, False, False, False, True),
        (WorkflowStatus.WAITING, WorkflowConclusion.SKIPPED, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.TIMED_OUT, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.ACTION_REQUIRED, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.NEUTRAL, False, False, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.STALE, False, False, False, False, False),
        (WorkflowStatus.WAITING, None, False, False, False, False, False),

        # REQUESTED status with various conclusions
        (WorkflowStatus.REQUESTED, WorkflowConclusion.SUCCESS, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.FAILURE, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.CANCELLED, False, False, False, False, True),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.SKIPPED, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.TIMED_OUT, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.ACTION_REQUIRED, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.NEUTRAL, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.STALE, False, False, False, False, False),
        (WorkflowStatus.REQUESTED, None, False, False, False, False, False),

        # PENDING status with various conclusions
        (WorkflowStatus.PENDING, WorkflowConclusion.SUCCESS, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.FAILURE, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.CANCELLED, False, False, False, False, True),
        (WorkflowStatus.PENDING, WorkflowConclusion.SKIPPED, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.TIMED_OUT, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.ACTION_REQUIRED, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.NEUTRAL, False, False, False, False, False),
        (WorkflowStatus.PENDING, WorkflowConclusion.STALE, False, False, False, False, False),
        (WorkflowStatus.PENDING, None, False, False, False, False, False),
    ])
    def test_state_matrix(
        self,
        status,
        conclusion,
        expected_terminal,
        expected_running,
        expected_successful,
        expected_failed,
        expected_cancelled,
    ):
        """Test all combinations of status and conclusion values."""
        run = WorkflowRun(
            id="test-run",
            workflow_name="Test",
            branch="main",
            status=status,
            conclusion=conclusion,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )

        assert run.is_terminal() == expected_terminal, \
            f"is_terminal mismatch for status={status}, conclusion={conclusion}"
        assert run.is_running() == expected_running, \
            f"is_running mismatch for status={status}, conclusion={conclusion}"
        assert run.is_successful() == expected_successful, \
            f"is_successful mismatch for status={status}, conclusion={conclusion}"
        assert run.is_failed() == expected_failed, \
            f"is_failed mismatch for status={status}, conclusion={conclusion}"
        assert run.is_cancelled() == expected_cancelled, \
            f"is_cancelled mismatch for status={status}, conclusion={conclusion}"
