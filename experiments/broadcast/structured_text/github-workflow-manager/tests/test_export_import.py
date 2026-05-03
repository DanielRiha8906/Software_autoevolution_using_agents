import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.storage.workflow_json_storage import WorkflowJsonStorage


def _sample_run(run_id: str = "r1", branch: str = "main") -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="Deploy",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        run_number=42,
        commit_sha="deadbeef",
        duration_seconds=120.5,
    )


@pytest.fixture
def tmp_service(tmp_path):
    """Create a temporary service with empty storage."""
    storage_path = tmp_path / "runs.json"
    storage = WorkflowJsonStorage(str(storage_path))
    service = WorkflowRunService(storage)
    return service, tmp_path


def test_export_empty_runs(tmp_service):
    """Test exporting when no runs exist."""
    service, tmp_path = tmp_service
    output_file = tmp_path / "export.json"
    count = service.export_runs(str(output_file))
    assert count == 0
    assert output_file.exists()
    assert json.loads(output_file.read_text()) == []


def test_export_single_run(tmp_service):
    """Test exporting a single run."""
    service, tmp_path = tmp_service
    run = _sample_run()
    service.add_workflow_run(run)
    output_file = tmp_path / "export.json"
    count = service.export_runs(str(output_file))
    assert count == 1
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert len(data) == 1
    assert data[0]["id"] == "r1"
    assert data[0]["workflow_name"] == "Deploy"
    assert data[0]["status"] == "completed"
    assert data[0]["conclusion"] == "success"


def test_export_multiple_runs(tmp_service):
    """Test exporting multiple runs."""
    service, tmp_path = tmp_service
    r1 = _sample_run("r1", "main")
    r2 = _sample_run("r2", "dev")
    r3 = _sample_run("r3", "feature")
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)
    output_file = tmp_path / "export.json"
    count = service.export_runs(str(output_file))
    assert count == 3
    data = json.loads(output_file.read_text())
    assert len(data) == 3
    assert {d["id"] for d in data} == {"r1", "r2", "r3"}


def test_export_creates_parent_directory(tmp_service):
    """Test that export creates parent directories if they don't exist."""
    service, tmp_path = tmp_service
    run = _sample_run()
    service.add_workflow_run(run)
    output_file = tmp_path / "subdir" / "nested" / "export.json"
    count = service.export_runs(str(output_file))
    assert count == 1
    assert output_file.exists()


def test_import_empty_file(tmp_service):
    """Test importing from an empty JSON array."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "import.json"
    import_file.write_text(json.dumps([]))
    count, errors = service.import_runs(str(import_file))
    assert count == 0
    assert errors == []


def test_import_single_run(tmp_path):
    """Test importing a single run."""
    # Create first service and export
    storage1 = WorkflowJsonStorage(str(tmp_path / "runs1.json"))
    service1 = WorkflowRunService(storage1)
    run = _sample_run()
    export_file = tmp_path / "export.json"
    service1.add_workflow_run(run)
    service1.export_runs(str(export_file))

    # Create second service and import
    storage2 = WorkflowJsonStorage(str(tmp_path / "runs2.json"))
    service2 = WorkflowRunService(storage2)
    count, errors = service2.import_runs(str(export_file))
    assert count == 1
    assert errors == []
    imported = service2.list_runs()
    assert len(imported) == 1
    assert imported[0].id == "r1"
    assert imported[0].workflow_name == "Deploy"


def test_import_multiple_runs(tmp_path):
    """Test importing multiple runs."""
    # Create first service and export
    storage1 = WorkflowJsonStorage(str(tmp_path / "runs1.json"))
    service1 = WorkflowRunService(storage1)
    r1 = _sample_run("r1", "main")
    r2 = _sample_run("r2", "dev")
    service1.add_workflow_run(r1)
    service1.add_workflow_run(r2)
    export_file = tmp_path / "export.json"
    service1.export_runs(str(export_file))

    # Create second service and import
    storage2 = WorkflowJsonStorage(str(tmp_path / "runs2.json"))
    service2 = WorkflowRunService(storage2)
    count, errors = service2.import_runs(str(export_file))
    assert count == 2
    assert errors == []
    imported = service2.list_runs()
    assert len(imported) == 2
    assert {r.id for r in imported} == {"r1", "r2"}


def test_import_file_not_found(tmp_service):
    """Test importing from a non-existent file."""
    service, _ = tmp_service
    with pytest.raises(FileNotFoundError):
        service.import_runs("/nonexistent/path/file.json")


def test_import_invalid_json(tmp_service):
    """Test importing from a file with invalid JSON."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "bad.json"
    import_file.write_text("{ not valid json")
    with pytest.raises(ValueError, match="Invalid JSON"):
        service.import_runs(str(import_file))


def test_import_not_array(tmp_service):
    """Test importing from a file that doesn't contain a JSON array."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "bad.json"
    import_file.write_text(json.dumps({"id": "r1"}))  # Object, not array
    with pytest.raises(ValueError, match="must contain a JSON array"):
        service.import_runs(str(import_file))


def test_import_duplicate_id_fails_by_default(tmp_service):
    """Test that duplicate IDs cause import to fail by default."""
    service, tmp_path = tmp_service
    run = _sample_run("r1")
    service.add_workflow_run(run)

    # Create a file with the same run
    import_file = tmp_path / "import.json"
    import_file.write_text(json.dumps([run.to_dict()]))

    # Import should fail on duplicate
    count, errors = service.import_runs(str(import_file))
    assert count == 0  # No runs imported
    assert any("already exists" in err for err in errors)


def test_import_duplicate_id_skip(tmp_service):
    """Test that duplicate IDs are skipped when skip_duplicates=True."""
    service, tmp_path = tmp_service
    r1 = _sample_run("r1")
    service.add_workflow_run(r1)

    import_file = tmp_path / "import.json"
    r2 = _sample_run("r1")  # Same ID as r1
    r3 = _sample_run("r3")  # New ID
    import_file.write_text(json.dumps([r2.to_dict(), r3.to_dict()]))

    count, errors = service.import_runs(str(import_file), skip_duplicates=True)
    assert count == 1  # Only r3 imported
    assert len(errors) == 1  # One duplicate skipped
    assert any("already exists" in err for err in errors)
    imported = service.list_runs()
    assert len(imported) == 2  # r1 + r3
    assert {r.id for r in imported} == {"r1", "r3"}


def test_import_validation_errors(tmp_service):
    """Test importing data with validation errors."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "import.json"
    # Missing required fields
    bad_data = [
        {"id": "r1", "workflow_name": "CI"},  # Missing other fields
        {"workflow_name": "CI"},  # Missing id
    ]
    import_file.write_text(json.dumps(bad_data))

    count, errors = service.import_runs(str(import_file))
    assert count == 0  # No runs imported due to errors
    assert len(errors) == 2  # Both items had errors


def test_import_partial_success_with_errors(tmp_service):
    """Test importing with some valid and some invalid items."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "import.json"
    valid_run = _sample_run("r1")
    invalid_run = {"id": "r2"}  # Missing required fields

    import_file.write_text(json.dumps([valid_run.to_dict(), invalid_run]))

    count, errors = service.import_runs(str(import_file))
    assert count == 1  # Only valid run imported
    assert len(errors) == 1  # One error
    imported = service.list_runs()
    assert len(imported) == 1
    assert imported[0].id == "r1"


def test_export_import_roundtrip(tmp_path):
    """Test complete roundtrip: create runs, export, import to new service."""
    # Create first service and export
    storage1 = WorkflowJsonStorage(str(tmp_path / "runs1.json"))
    service1 = WorkflowRunService(storage1)
    r1 = _sample_run("r1", "main")
    r2 = WorkflowRun(
        id="r2",
        workflow_name="Test",
        branch="dev",
        status=WorkflowStatus.IN_PROGRESS,
        conclusion=None,
        created_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=10,
        commit_sha="abc123",
        duration_seconds=45.0,
    )
    service1.add_workflow_run(r1)
    service1.add_workflow_run(r2)

    export_file = tmp_path / "roundtrip.json"
    service1.export_runs(str(export_file))

    # Create second service and import
    storage2 = WorkflowJsonStorage(str(tmp_path / "runs2.json"))
    service2 = WorkflowRunService(storage2)
    count, errors = service2.import_runs(str(export_file))
    assert count == 2
    assert errors == []

    imported = service2.list_runs()
    assert len(imported) == 2

    # Verify data integrity
    r1_imported = service2.get_run_detail("r1")
    assert r1_imported is not None
    assert r1_imported.workflow_name == "Deploy"
    assert r1_imported.branch == "main"
    assert r1_imported.status == WorkflowStatus.COMPLETED
    assert r1_imported.conclusion == WorkflowConclusion.SUCCESS
    assert r1_imported.run_number == 42
    assert r1_imported.commit_sha == "deadbeef"
    assert r1_imported.duration_seconds == 120.5

    r2_imported = service2.get_run_detail("r2")
    assert r2_imported is not None
    assert r2_imported.workflow_name == "Test"
    assert r2_imported.status == WorkflowStatus.IN_PROGRESS
    assert r2_imported.conclusion is None


def test_import_with_non_dict_items(tmp_service):
    """Test importing a file with non-dictionary items in the array."""
    service, tmp_path = tmp_service
    import_file = tmp_path / "import.json"
    bad_data = [
        _sample_run("r1").to_dict(),
        "invalid string item",
        123,
    ]
    import_file.write_text(json.dumps(bad_data))

    count, errors = service.import_runs(str(import_file))
    assert count == 1  # Only first valid item imported
    assert len(errors) == 2  # Two invalid items
