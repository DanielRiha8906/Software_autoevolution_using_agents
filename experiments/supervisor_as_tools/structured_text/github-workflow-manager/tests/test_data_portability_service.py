import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.data_portability_service import DataPortabilityService
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage
from src.storage.attempt_json_storage import AttemptJsonStorage


# Fixtures

@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary directory for test storage files."""
    return tmp_path


@pytest.fixture
def workflow_service(temp_storage_dir):
    """Create a WorkflowRunService with temporary storage."""
    storage = WorkflowJsonStorage(str(temp_storage_dir / "runs.json"))
    return WorkflowRunService(storage)


@pytest.fixture
def attempt_service(temp_storage_dir):
    """Create an AttemptService with temporary storage."""
    storage = AttemptJsonStorage(str(temp_storage_dir / "attempts.json"))
    return AttemptService(storage)


@pytest.fixture
def portability_service():
    """Create a DataPortabilityService instance."""
    return DataPortabilityService()


# Helper functions

def create_sample_run(
    run_id="test-run-1",
    workflow_name="test-workflow",
    branch="main",
    status=WorkflowStatus.COMPLETED,
    conclusion=WorkflowConclusion.SUCCESS,
    run_number=1,
    commit_sha="abc123",
    duration_seconds=60.5,
):
    """Create a sample WorkflowRun for testing."""
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=run_number,
        commit_sha=commit_sha,
        duration_seconds=duration_seconds,
    )


def create_sample_attempt(
    attempt_id=1,
    run_id=1,
    attempt_number=1,
    status="completed",
    conclusion="success",
    duration_seconds=60.5,
):
    """Create a sample WorkflowRunAttempt for testing."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


# Export Tests

class TestExport:
    """Tests for data export functionality."""

    def test_export_with_runs_and_attempts(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Export creates JSON with correct structure, metadata, counts."""
        # Add sample runs and attempts
        run = create_sample_run()
        workflow_service.add_workflow_run(run)

        attempt = create_sample_attempt(run_id=1)
        attempt_service.create_attempt(
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime.now(timezone.utc),
            duration_seconds=60.5,
        )

        output_file = str(tmp_path / "export.json")
        result = portability_service.export_data(workflow_service, attempt_service, output_file)

        # Verify result object
        assert result.output_path == output_file
        assert result.runs_count == 1
        assert result.attempts_count == 1
        assert Path(output_file).exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "data" in data
        assert data["metadata"]["schema_version"] == "1.0"
        assert data["metadata"]["runs_count"] == 1
        assert data["metadata"]["attempts_count"] == 1
        assert len(data["data"]["runs"]) == 1
        assert len(data["data"]["attempts"]) == 1

    def test_export_empty_database(self, workflow_service, attempt_service, portability_service, tmp_path):
        """Export with no data produces valid envelope."""
        output_file = str(tmp_path / "export_empty.json")
        result = portability_service.export_data(workflow_service, attempt_service, output_file)

        # Verify result
        assert result.runs_count == 0
        assert result.attempts_count == 0
        assert Path(output_file).exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)

        assert data["metadata"]["runs_count"] == 0
        assert data["metadata"]["attempts_count"] == 0
        assert len(data["data"]["runs"]) == 0
        assert len(data["data"]["attempts"]) == 0

    def test_export_creates_parent_directories(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Verify parent directories are created."""
        output_file = str(tmp_path / "nested" / "deep" / "dirs" / "export.json")
        result = portability_service.export_data(workflow_service, attempt_service, output_file)

        # Verify directories were created
        assert Path(output_file).exists()
        assert Path(output_file).parent.exists()

    def test_export_timestamp_format(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Verify ISO 8601 UTC format for timestamp."""
        output_file = str(tmp_path / "export.json")
        result = portability_service.export_data(workflow_service, attempt_service, output_file)

        # Check result timestamp
        assert result.timestamp
        # Should be ISO 8601 format with timezone info
        parsed_dt = datetime.fromisoformat(result.timestamp)
        assert parsed_dt.tzinfo is not None

        # Check file metadata timestamp
        with open(output_file) as f:
            data = json.load(f)

        file_timestamp = data["metadata"]["timestamp"]
        parsed_file_dt = datetime.fromisoformat(file_timestamp)
        assert parsed_file_dt.tzinfo is not None

    def test_export_schema_version_is_1_0(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Verify version field."""
        output_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, output_file)

        with open(output_file) as f:
            data = json.load(f)

        assert data["metadata"]["schema_version"] == "1.0"

    def test_export_file_write_error(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """IOError handling when file cannot be written."""
        # Use a path that cannot be written to (non-existent parent with no permissions)
        bad_path = "/root/no_permission/export.json"

        with pytest.raises(IOError):
            portability_service.export_data(workflow_service, attempt_service, bad_path)


# Import Tests

class TestImport:
    """Tests for data import functionality."""

    def test_import_valid_export(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Full import with correct counts."""
        # Create and export data
        run = create_sample_run(run_id="run-1")
        workflow_service.add_workflow_run(run)

        attempt_service.create_attempt(
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime.now(timezone.utc),
            duration_seconds=60.5,
        )

        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Create fresh services for import
        import_run_service = WorkflowRunService(
            WorkflowJsonStorage(str(tmp_path / "imported_runs.json"))
        )
        import_attempt_service = AttemptService(
            AttemptJsonStorage(str(tmp_path / "imported_attempts.json"))
        )

        # Import the data
        result = portability_service.import_data(
            import_run_service, import_attempt_service, export_file
        )

        assert result.runs_imported == 1
        assert result.attempts_imported == 1
        assert result.runs_skipped == 0
        assert result.attempts_skipped == 0
        assert result.runs_failed == 0
        assert result.attempts_failed == 0

    def test_import_skip_duplicates_true(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Duplicate runs are skipped, not added again."""
        # Add initial run
        run = create_sample_run(run_id="run-1")
        workflow_service.add_workflow_run(run)

        # Create and export
        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Import into same service (which still has the original run)
        result = portability_service.import_data(
            workflow_service, attempt_service, export_file, skip_duplicates=True
        )

        assert result.runs_skipped == 1
        assert result.runs_imported == 0
        assert result.runs_failed == 0
        # Service should still have only 1 run
        assert len(workflow_service.list_runs()) == 1

    def test_import_skip_duplicates_false(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Duplicate run raises ValueError when skip_invalid=False."""
        # Add initial run
        run = create_sample_run(run_id="run-1")
        workflow_service.add_workflow_run(run)

        # Create and export
        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Import with skip_duplicates=False and skip_invalid=False should raise
        with pytest.raises(ValueError, match="Duplicate"):
            portability_service.import_data(
                workflow_service, attempt_service, export_file, skip_duplicates=False, skip_invalid=False
            )

    def test_import_skip_invalid_true(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Invalid items skipped with errors collected."""
        # Create export file with invalid data
        export_file = str(tmp_path / "export_invalid.json")
        invalid_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "runs_count": 1,
                "attempts_count": 0,
            },
            "data": {
                "runs": [
                    {
                        "id": "valid-run",
                        "workflow_name": "test",
                        "branch": "main",
                        "status": "completed",
                        "conclusion": "success",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": None,
                        "run_number": 1,
                        "commit_sha": "abc123",
                        "duration_seconds": 60.5,
                    },
                    {
                        # Missing required field: workflow_name
                        "id": "invalid-run",
                        "branch": "main",
                        "status": "completed",
                        "conclusion": "success",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": None,
                        "run_number": 1,
                        "commit_sha": "abc123",
                        "duration_seconds": 60.5,
                    },
                ],
                "attempts": [],
            },
        }

        with open(export_file, "w") as f:
            json.dump(invalid_data, f)

        # Import with skip_invalid=True should skip invalid item
        result = portability_service.import_data(
            workflow_service, attempt_service, export_file, skip_invalid=True
        )

        assert result.runs_imported == 1
        assert result.runs_failed == 1
        assert len(result.errors) > 0
        assert "Invalid data" in result.errors[0]

    def test_import_skip_invalid_false(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Invalid items raise ValueError immediately."""
        # Create export file with invalid data
        export_file = str(tmp_path / "export_invalid.json")
        invalid_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "runs_count": 1,
                "attempts_count": 0,
            },
            "data": {
                "runs": [
                    {
                        # Missing required field: workflow_name
                        "id": "invalid-run",
                        "branch": "main",
                        "status": "completed",
                        "conclusion": "success",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": None,
                        "run_number": 1,
                        "commit_sha": "abc123",
                        "duration_seconds": 60.5,
                    },
                ],
                "attempts": [],
            },
        }

        with open(export_file, "w") as f:
            json.dump(invalid_data, f)

        # Import with skip_invalid=False should raise
        with pytest.raises(ValueError, match="Invalid data"):
            portability_service.import_data(
                workflow_service, attempt_service, export_file, skip_invalid=False
            )

    def test_import_invalid_schema_version(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Raises ValueError for unsupported schema version."""
        export_file = str(tmp_path / "export_bad_version.json")
        bad_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "2.0",  # Wrong version
                "runs_count": 0,
                "attempts_count": 0,
            },
            "data": {"runs": [], "attempts": []},
        }

        with open(export_file, "w") as f:
            json.dump(bad_data, f)

        with pytest.raises(ValueError, match="Unsupported schema version"):
            portability_service.import_data(workflow_service, attempt_service, export_file)

    def test_import_missing_data_fields(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Raises ValueError for missing data fields."""
        export_file = str(tmp_path / "export_bad_format.json")
        bad_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
            }
            # Missing "data" field
        }

        with open(export_file, "w") as f:
            json.dump(bad_data, f)

        with pytest.raises(ValueError, match="Invalid export format"):
            portability_service.import_data(workflow_service, attempt_service, export_file)

    def test_import_malformed_json(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Raises ValueError for malformed JSON."""
        export_file = str(tmp_path / "export_bad_json.json")
        with open(export_file, "w") as f:
            f.write("{invalid json content")

        with pytest.raises(ValueError, match="Invalid JSON"):
            portability_service.import_data(workflow_service, attempt_service, export_file)

    def test_import_invalid_datetime_format(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Caught during deserialization for bad datetime."""
        export_file = str(tmp_path / "export_bad_datetime.json")
        bad_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "runs_count": 1,
                "attempts_count": 0,
            },
            "data": {
                "runs": [
                    {
                        "id": "bad-datetime-run",
                        "workflow_name": "test",
                        "branch": "main",
                        "status": "completed",
                        "conclusion": "success",
                        "created_at": "not-a-valid-datetime",  # Bad format
                        "updated_at": None,
                        "run_number": 1,
                        "commit_sha": "abc123",
                        "duration_seconds": 60.5,
                    },
                ],
                "attempts": [],
            },
        }

        with open(export_file, "w") as f:
            json.dump(bad_data, f)

        with pytest.raises(ValueError):
            portability_service.import_data(
                workflow_service, attempt_service, export_file, skip_invalid=False
            )

    def test_import_invalid_enum_value(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Caught during deserialization for bad enum value."""
        export_file = str(tmp_path / "export_bad_enum.json")
        bad_data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "runs_count": 1,
                "attempts_count": 0,
            },
            "data": {
                "runs": [
                    {
                        "id": "bad-enum-run",
                        "workflow_name": "test",
                        "branch": "main",
                        "status": "invalid_status",  # Bad enum value
                        "conclusion": "success",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": None,
                        "run_number": 1,
                        "commit_sha": "abc123",
                        "duration_seconds": 60.5,
                    },
                ],
                "attempts": [],
            },
        }

        with open(export_file, "w") as f:
            json.dump(bad_data, f)

        with pytest.raises(ValueError):
            portability_service.import_data(
                workflow_service, attempt_service, export_file, skip_invalid=False
            )

    def test_import_file_not_found(
        self, workflow_service, attempt_service, portability_service
    ):
        """Raises FileNotFoundError."""
        nonexistent_file = "/tmp/nonexistent_file_12345.json"

        with pytest.raises(IOError):
            portability_service.import_data(workflow_service, attempt_service, nonexistent_file)


# Round-Trip Tests

class TestRoundTrip:
    """Tests for export-then-import round-trip preservation."""

    def test_export_then_import_preserves_data(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """Export all, import back, verify identical."""
        # Create multiple runs and attempts
        runs = [
            create_sample_run(run_id="run-1", branch="main"),
            create_sample_run(run_id="run-2", branch="develop"),
        ]
        for run in runs:
            workflow_service.add_workflow_run(run)

        for i, run in enumerate(runs):
            attempt_service.create_attempt(
                run_id=int(run.id.split("-")[1]),  # Extract numeric ID
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=datetime.now(timezone.utc),
                duration_seconds=30.5 + i,
            )

        # Export
        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Create fresh services for import
        import_run_service = WorkflowRunService(
            WorkflowJsonStorage(str(tmp_path / "imported_runs.json"))
        )
        import_attempt_service = AttemptService(
            AttemptJsonStorage(str(tmp_path / "imported_attempts.json"))
        )

        # Import
        portability_service.import_data(
            import_run_service, import_attempt_service, export_file
        )

        # Verify same data
        imported_runs = import_run_service.list_runs()
        imported_attempts = import_attempt_service.list_attempts()

        assert len(imported_runs) == len(workflow_service.list_runs())
        assert len(imported_attempts) == len(attempt_service.list_attempts())

        # Verify IDs match
        original_ids = {r.id for r in workflow_service.list_runs()}
        imported_ids = {r.id for r in imported_runs}
        assert original_ids == imported_ids

    def test_export_then_import_preserves_datetime_precision(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """ISO 8601 maintains precision."""
        # Create a run with microsecond precision
        now = datetime.now(timezone.utc)
        run = WorkflowRun(
            id="datetime-test",
            workflow_name="test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=now,
            updated_at=now,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=60.5,
        )
        workflow_service.add_workflow_run(run)

        # Export
        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Import
        import_run_service = WorkflowRunService(
            WorkflowJsonStorage(str(tmp_path / "imported_runs.json"))
        )
        import_attempt_service = AttemptService(
            AttemptJsonStorage(str(tmp_path / "imported_attempts.json"))
        )

        portability_service.import_data(
            import_run_service, import_attempt_service, export_file
        )

        # Verify datetime precision
        imported_runs = import_run_service.list_runs()
        assert len(imported_runs) == 1

        imported_run = imported_runs[0]
        assert imported_run.created_at == run.created_at
        assert imported_run.updated_at == run.updated_at

    def test_export_then_import_preserves_enums(
        self, workflow_service, attempt_service, portability_service, tmp_path
    ):
        """WorkflowStatus/WorkflowConclusion survive round-trip."""
        # Test all status/conclusion combinations
        statuses = [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS, WorkflowStatus.COMPLETED]
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
        ]

        run_id = 0
        for status in statuses:
            for conclusion in conclusions:
                run_id += 1
                run = WorkflowRun(
                    id=f"enum-test-{run_id}",
                    workflow_name="test",
                    branch="main",
                    status=status,
                    conclusion=conclusion,
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                    run_number=run_id,
                    commit_sha="abc123",
                    duration_seconds=60.5,
                )
                workflow_service.add_workflow_run(run)

        # Export
        export_file = str(tmp_path / "export.json")
        portability_service.export_data(workflow_service, attempt_service, export_file)

        # Import
        import_run_service = WorkflowRunService(
            WorkflowJsonStorage(str(tmp_path / "imported_runs.json"))
        )
        import_attempt_service = AttemptService(
            AttemptJsonStorage(str(tmp_path / "imported_attempts.json"))
        )

        portability_service.import_data(
            import_run_service, import_attempt_service, export_file
        )

        # Verify enums preserved
        original_runs = workflow_service.list_runs()
        imported_runs = import_run_service.list_runs()

        for orig, imported in zip(original_runs, imported_runs):
            assert imported.status == orig.status
            assert isinstance(imported.status, WorkflowStatus)
            assert imported.conclusion == orig.conclusion
            assert isinstance(imported.conclusion, WorkflowConclusion)
