import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.storage.workflow_json_storage import WorkflowJsonStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return WorkflowJsonStorage(str(tmp_path / "runs.json"))


def _sample_run() -> WorkflowRun:
    return WorkflowRun(
        id="r1",
        workflow_name="Deploy",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=42,
        commit_sha="deadbeef",
    )


def test_load_empty(tmp_storage):
    assert tmp_storage.load() == []


def test_save_and_load_roundtrip(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].id == run.id
    assert loaded[0].workflow_name == run.workflow_name
    assert loaded[0].status == run.status
    assert loaded[0].conclusion == run.conclusion
    assert loaded[0].run_number == run.run_number
    assert loaded[0].commit_sha == run.commit_sha


def test_save_persists_json(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["id"] == "r1"
    assert raw[0]["conclusion"] == "success"


class TestDurationSecondsStorage:
    """Tests for duration_seconds serialization and deserialization."""

    def test_save_and_load_with_duration_seconds(self, tmp_storage):
        """Test that duration_seconds is preserved through save/load cycle."""
        run = WorkflowRun(
            id="r1",
            workflow_name="Deploy",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=42,
            commit_sha="deadbeef",
            duration_seconds=123.45,
        )
        tmp_storage.save([run])
        loaded = tmp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].duration_seconds == 123.45

    def test_save_duration_seconds_in_json(self, tmp_storage):
        """Test that duration_seconds appears in persisted JSON."""
        run = WorkflowRun(
            id="r2",
            workflow_name="CI",
            branch="dev",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            updated_at=None,
            run_number=43,
            commit_sha="cafebabe",
            duration_seconds=567.89,
        )
        tmp_storage.save([run])
        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert raw[0]["duration_seconds"] == 567.89

    def test_load_with_default_duration_seconds(self, tmp_storage):
        """Test that missing duration_seconds in JSON defaults to 0.0."""
        # Manually create JSON without duration_seconds
        data = [
            {
                "id": "r3",
                "workflow_name": "Test",
                "branch": "feature",
                "status": "completed",
                "conclusion": "success",
                "created_at": datetime(2024, 1, 3, tzinfo=timezone.utc).isoformat(),
                "updated_at": None,
                "run_number": 44,
                "commit_sha": "beefcafe",
            }
        ]
        Path(tmp_storage.filepath).write_text(json.dumps(data))
        loaded = tmp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].duration_seconds == 0.0

    def test_multiple_runs_with_different_durations(self, tmp_storage):
        """Test saving and loading multiple runs with different durations."""
        runs = [
            WorkflowRun(
                id="r4",
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
                updated_at=None,
                run_number=45,
                commit_sha="abc123",
                duration_seconds=100.0,
            ),
            WorkflowRun(
                id="r5",
                workflow_name="Deploy",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
                updated_at=None,
                run_number=46,
                commit_sha="def456",
                duration_seconds=200.0,
            ),
            WorkflowRun(
                id="r6",
                workflow_name="Test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.FAILURE,
                created_at=datetime(2024, 1, 6, tzinfo=timezone.utc),
                updated_at=None,
                run_number=47,
                commit_sha="ghi789",
                duration_seconds=50.5,
            ),
        ]
        tmp_storage.save(runs)
        loaded = tmp_storage.load()
        assert len(loaded) == 3
        assert loaded[0].duration_seconds == 100.0
        assert loaded[1].duration_seconds == 200.0
        assert loaded[2].duration_seconds == 50.5

    def test_save_zero_duration_seconds(self, tmp_storage):
        """Test that zero duration_seconds is properly persisted."""
        run = WorkflowRun(
            id="r7",
            workflow_name="Quick",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 7, tzinfo=timezone.utc),
            updated_at=None,
            run_number=48,
            commit_sha="zzz000",
            duration_seconds=0.0,
        )
        tmp_storage.save([run])
        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert raw[0]["duration_seconds"] == 0.0
        loaded = tmp_storage.load()
        assert loaded[0].duration_seconds == 0.0
