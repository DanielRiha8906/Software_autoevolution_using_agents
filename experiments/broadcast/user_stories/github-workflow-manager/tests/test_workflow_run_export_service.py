import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_export_service import WorkflowRunExportService


def _make_run(run_id: str = "run-1", branch: str = "main", conclusion=None) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=conclusion or WorkflowConclusion.SUCCESS,
        created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
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


@pytest.fixture
def temp_file(tmp_path):
    return str(tmp_path / "export.json")


class TestExportToFile:
    def test_export_empty(self, service, temp_file):
        count = WorkflowRunExportService.export_to_file(service, temp_file)
        assert count == 0
        assert Path(temp_file).read_text() == "[]"

    def test_export_single_run(self, service, temp_file):
        run = _make_run()
        service.add_workflow_run(run)
        count = WorkflowRunExportService.export_to_file(service, temp_file)
        assert count == 1
        data = json.loads(Path(temp_file).read_text())
        assert len(data) == 1
        assert data[0]["id"] == "run-1"

    def test_export_multiple_runs(self, service, temp_file):
        r1 = _make_run("run-1", "main")
        r2 = _make_run("run-2", "dev", WorkflowConclusion.FAILURE)
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        count = WorkflowRunExportService.export_to_file(service, temp_file)
        assert count == 2
        data = json.loads(Path(temp_file).read_text())
        assert len(data) == 2
        assert data[0]["id"] == "run-1"
        assert data[1]["id"] == "run-2"

    def test_export_creates_directory(self, service, tmp_path):
        nested_path = str(tmp_path / "nested" / "dir" / "export.json")
        count = WorkflowRunExportService.export_to_file(service, nested_path)
        assert count == 0
        assert Path(nested_path).exists()

    def test_export_preserves_all_fields(self, service, temp_file):
        run = WorkflowRun(
            id="test-id",
            workflow_name="TestWorkflow",
            branch="feature-branch",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime(2026, 5, 3, 15, 30, 45, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 3, 16, 30, 45, tzinfo=timezone.utc),
            run_number=42,
            commit_sha="def456",
        )
        service.add_workflow_run(run)
        WorkflowRunExportService.export_to_file(service, temp_file)
        data = json.loads(Path(temp_file).read_text())
        exported = data[0]

        assert exported["id"] == "test-id"
        assert exported["workflow_name"] == "TestWorkflow"
        assert exported["branch"] == "feature-branch"
        assert exported["status"] == "in_progress"
        assert exported["conclusion"] is None
        assert exported["run_number"] == 42
        assert exported["commit_sha"] == "def456"
        assert exported["created_at"] == "2026-05-03T15:30:45+00:00"
        assert exported["updated_at"] == "2026-05-03T16:30:45+00:00"


class TestImportFromFile:
    def test_import_file_not_found(self, service):
        with pytest.raises(FileNotFoundError):
            WorkflowRunExportService.import_from_file(service, "/nonexistent.json")

    def test_import_not_array(self, service, temp_file):
        Path(temp_file).write_text('{"not": "array"}')
        with pytest.raises(ValueError, match="JSON array"):
            WorkflowRunExportService.import_from_file(service, temp_file)

    def test_import_empty_array(self, service, temp_file):
        Path(temp_file).write_text("[]")
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 0
        assert skips == []

    def test_import_single_run(self, service, temp_file):
        run = _make_run()
        Path(temp_file).write_text(json.dumps([run.to_dict()]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 1
        assert skips == []
        assert service.list_runs() == [run]

    def test_import_multiple_runs(self, service, temp_file):
        r1 = _make_run("run-1", "main")
        r2 = _make_run("run-2", "dev", WorkflowConclusion.FAILURE)
        data = [r1.to_dict(), r2.to_dict()]
        Path(temp_file).write_text(json.dumps(data))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 2
        assert skips == []
        assert len(service.list_runs()) == 2

    def test_import_duplicate_id_skipped(self, service, temp_file):
        run = _make_run("run-1")
        service.add_workflow_run(run)
        Path(temp_file).write_text(json.dumps([run.to_dict()]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 0
        assert len(skips) == 1
        assert "already exists" in skips[0]
        assert "Entry 0" in skips[0]

    def test_import_missing_required_field(self, service, temp_file):
        incomplete = {
            "id": "test-1",
            "workflow_name": "Test",
        }
        Path(temp_file).write_text(json.dumps([incomplete]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 0
        assert len(skips) == 1
        assert "Missing required field" in skips[0]

    def test_import_invalid_status(self, service, temp_file):
        run_dict = _make_run().to_dict()
        run_dict["status"] = "invalid_status"
        Path(temp_file).write_text(json.dumps([run_dict]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 0
        assert len(skips) == 1
        assert "not a valid WorkflowStatus" in skips[0]

    def test_import_invalid_conclusion(self, service, temp_file):
        run_dict = _make_run().to_dict()
        run_dict["conclusion"] = "invalid_conclusion"
        Path(temp_file).write_text(json.dumps([run_dict]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 0
        assert len(skips) == 1
        assert "not a valid WorkflowConclusion" in skips[0]

    def test_import_non_dict_entry(self, service, temp_file):
        Path(temp_file).write_text(json.dumps([_make_run().to_dict(), "not a dict"]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 1
        assert len(skips) == 1
        assert "Not a dictionary" in skips[0]

    def test_import_mixed_valid_invalid(self, service, temp_file):
        r1 = _make_run("run-1")
        r2_dict = _make_run("run-2").to_dict()
        r2_dict["status"] = "bad_status"
        r3 = _make_run("run-3")
        data = [r1.to_dict(), r2_dict, r3.to_dict()]
        Path(temp_file).write_text(json.dumps(data))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 2
        assert len(skips) == 1
        assert service.get_run_detail("run-1") is not None
        assert service.get_run_detail("run-3") is not None
        assert service.get_run_detail("run-2") is None

    def test_import_continues_after_duplicates(self, service, temp_file):
        r1 = _make_run("run-1")
        service.add_workflow_run(r1)
        r2 = _make_run("run-2")
        data = [r1.to_dict(), r2.to_dict()]
        Path(temp_file).write_text(json.dumps(data))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 1
        assert len(skips) == 1
        assert service.get_run_detail("run-2") is not None

    def test_import_roundtrip(self, service, temp_file):
        r1 = _make_run("run-1", "main")
        r2 = _make_run("run-2", "dev")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        WorkflowRunExportService.export_to_file(service, temp_file)

        service2 = MagicMock()
        service2.load.return_value = []
        import_service = WorkflowRunService(service2)
        imported, skips = WorkflowRunExportService.import_from_file(import_service, temp_file)
        assert imported == 2
        assert skips == []
        assert len(import_service.list_runs()) == 2

    def test_import_null_conclusion(self, service, temp_file):
        run_dict = _make_run().to_dict()
        run_dict["conclusion"] = None
        Path(temp_file).write_text(json.dumps([run_dict]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert imported == 1
        assert skips == []

    def test_import_skip_reasons_include_entry_index(self, service, temp_file):
        r1_dict = _make_run("run-1").to_dict()
        r1_dict["status"] = "bad"
        r2_dict = _make_run("run-2").to_dict()
        r2_dict["conclusion"] = "invalid_conclusion"
        Path(temp_file).write_text(json.dumps([r1_dict, r2_dict]))
        imported, skips = WorkflowRunExportService.import_from_file(service, temp_file)
        assert len(skips) == 2
        assert "Entry 0" in skips[0]
        assert "Entry 1" in skips[1]
