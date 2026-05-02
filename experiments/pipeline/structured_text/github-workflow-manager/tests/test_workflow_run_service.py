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
        duration_seconds=0.0,
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


def test_workflow_run_rejects_negative_duration():
    with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
        WorkflowRun(
            id="r1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
            duration_seconds=-1.0,
        )
