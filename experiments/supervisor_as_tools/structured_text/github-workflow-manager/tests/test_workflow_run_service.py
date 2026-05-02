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


class TestDurationSeconds:
    """Tests for the duration_seconds attribute of WorkflowRun."""

    def test_duration_seconds_default_value(self):
        """Test that duration_seconds defaults to 0.0."""
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
        assert run.duration_seconds == 0.0

    def test_duration_seconds_can_be_set(self):
        """Test that duration_seconds can be explicitly set."""
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
            duration_seconds=123.45,
        )
        assert run.duration_seconds == 123.45

    @pytest.mark.parametrize("duration", [0.0, 1.0, 100.5, 3661.0, 999999.99])
    def test_duration_seconds_valid_values(self, duration):
        """Test that various valid non-negative duration values are accepted."""
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
            duration_seconds=duration,
        )
        assert run.duration_seconds == duration

    def test_duration_seconds_negative_raises_error(self):
        """Test that negative duration_seconds raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            WorkflowRun(
                id="run-1",
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=1,
                commit_sha="abc123",
                duration_seconds=-0.1,
            )
        assert "non-negative" in str(exc_info.value).lower()

    def test_duration_seconds_serialization(self):
        """Test that duration_seconds is correctly serialized to dict."""
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
            duration_seconds=456.78,
        )
        data = run.to_dict()
        assert data["duration_seconds"] == 456.78

    def test_duration_seconds_deserialization(self):
        """Test that duration_seconds is correctly deserialized from dict."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 789.01,
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 789.01

    def test_duration_seconds_deserialization_missing_defaults_to_zero(self):
        """Test that missing duration_seconds in dict defaults to 0.0."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 0.0

    def test_duration_seconds_roundtrip_through_service(self, service):
        """Test that duration_seconds survives a roundtrip through service persistence."""
        run = WorkflowRun(
            id="run-with-duration",
            workflow_name="Deploy",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=5,
            commit_sha="xyz789",
            duration_seconds=234.56,
        )
        service.add_workflow_run(run)
        retrieved = service.get_run_detail("run-with-duration")
        assert retrieved.duration_seconds == 234.56

    def test_duration_seconds_zero_is_valid(self):
        """Test that zero duration is valid."""
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
            duration_seconds=0.0,
        )
        assert run.duration_seconds == 0.0

    def test_duration_seconds_large_value(self):
        """Test that large duration values are accepted."""
        large_duration = 1e10  # 10 billion seconds
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
            duration_seconds=large_duration,
        )
        assert run.duration_seconds == large_duration
