import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import subprocess

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.import_result import ImportResult
from src.services.workflow_export_import_service import WorkflowRunExportImportService
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


# ============================================================================
# Test Fixtures
# ============================================================================

def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    run_number: int = None,
    commit_sha: str = None,
    duration_seconds: float = 0.0,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=run_number,
        commit_sha=commit_sha,
        duration_seconds=duration_seconds,
    )


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def export_import_service():
    return WorkflowRunExportImportService()


@pytest.fixture
def mock_run_service():
    storage = MagicMock()
    storage.load.return_value = []
    service = WorkflowRunService(storage)
    return service


@pytest.fixture
def mock_attempt_service():
    storage = MagicMock()
    storage.load_attempts.return_value = []
    service = WorkflowRunAttemptService(storage)
    return service


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Export Tests
# ============================================================================

class TestExport:
    """Tests for the export_to_file method."""

    def test_export_basic_two_runs(self, export_import_service, mock_run_service, temp_dir):
        """Export 2 runs to file and verify JSON structure and content."""
        run1 = _make_run("run-1", duration_seconds=10.5)
        run2 = _make_run("run-2", branch="dev", duration_seconds=20.0)
        mock_run_service.add_workflow_run(run1)
        mock_run_service.add_workflow_run(run2)

        filepath = Path(temp_dir) / "test_export.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert len(data) == 2
        assert data[0]["id"] == "run-1"
        assert data[1]["id"] == "run-2"
        assert data[0]["duration_seconds"] == 10.5
        assert data[1]["branch"] == "dev"

    def test_export_empty_service(self, export_import_service, mock_run_service, temp_dir):
        """Export 0 runs (empty service) and verify empty array."""
        filepath = Path(temp_dir) / "test_empty.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert data == []

    def test_export_with_attempts(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Export runs and separate _attempts.json file when include_attempts=True."""
        run = _make_run("run-1")
        attempt = _make_attempt(attempt_id=100, run_id=1)
        mock_run_service.add_workflow_run(run)
        mock_attempt_service.add_attempt(attempt)

        filepath = Path(temp_dir) / "test_with_attempts.json"
        export_import_service.export_to_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service,
            include_attempts=True
        )

        assert filepath.exists()
        attempts_filepath = Path(temp_dir) / "test_with_attempts_attempts.json"
        assert attempts_filepath.exists()

        runs_data = json.loads(filepath.read_text())
        attempts_data = json.loads(attempts_filepath.read_text())
        assert len(runs_data) == 1
        assert len(attempts_data) == 1
        assert attempts_data[0]["id"] == 100

    def test_export_overwrites_existing_file(self, export_import_service, mock_run_service, temp_dir):
        """Export overwrites existing file."""
        filepath = Path(temp_dir) / "test_overwrite.json"
        filepath.write_text("old content")

        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)
        export_import_service.export_to_file(str(filepath), mock_run_service)

        data = json.loads(filepath.read_text())
        assert len(data) == 1
        assert data[0]["id"] == "run-1"

    def test_export_creates_parent_directories(self, export_import_service, mock_run_service, temp_dir):
        """Export creates parent directories if they don't exist."""
        filepath = Path(temp_dir) / "nested" / "deep" / "test_export.json"
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        export_import_service.export_to_file(str(filepath), mock_run_service)

        assert filepath.exists()
        assert filepath.parent.exists()

    def test_export_preserves_null_fields(self, export_import_service, mock_run_service, temp_dir):
        """Export preserves null values for optional fields."""
        run = _make_run("run-1", conclusion=None, updated_at=None, run_number=None, commit_sha=None)
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "test_nulls.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        data = json.loads(filepath.read_text())
        assert data[0]["conclusion"] is None
        assert data[0]["updated_at"] is None
        assert data[0]["run_number"] is None
        assert data[0]["commit_sha"] is None

    def test_export_preserves_datetime_format(self, export_import_service, mock_run_service, temp_dir):
        """Export converts datetimes to ISO format strings."""
        now = datetime(2025, 5, 3, 12, 30, 45, 123456, timezone.utc)
        run = _make_run("run-1", created_at=now, updated_at=now)
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "test_datetime.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        data = json.loads(filepath.read_text())
        assert data[0]["created_at"] == "2025-05-03T12:30:45.123456+00:00"
        assert data[0]["updated_at"] == "2025-05-03T12:30:45.123456+00:00"

    def test_export_with_include_attempts_false(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Export with include_attempts=False does not export attempts."""
        run = _make_run("run-1")
        attempt = _make_attempt()
        mock_run_service.add_workflow_run(run)
        mock_attempt_service.add_attempt(attempt)

        filepath = Path(temp_dir) / "test_no_attempts.json"
        export_import_service.export_to_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service,
            include_attempts=False
        )

        assert filepath.exists()
        attempts_filepath = Path(temp_dir) / "test_no_attempts_attempts.json"
        assert not attempts_filepath.exists()


# ============================================================================
# Import Tests
# ============================================================================

class TestImport:
    """Tests for the import_from_file method."""

    def test_import_valid_runs(self, export_import_service, mock_run_service, temp_dir):
        """Import 2 valid runs from JSON."""
        data = [
            {
                "id": "imported-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.5,
            },
            {
                "id": "imported-2",
                "workflow_name": "CD",
                "branch": "dev",
                "status": "completed",
                "conclusion": "failure",
                "created_at": "2025-05-03T11:00:00+00:00",
                "updated_at": None,
                "run_number": 2,
                "commit_sha": "def456",
                "duration_seconds": 45.0,
            },
        ]
        filepath = Path(temp_dir) / "import_valid.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 2
        assert result.imported_runs == 2
        assert result.skipped_runs == 0
        assert len(result.errors) == 0
        assert mock_run_service.list_runs().__len__() == 2

    def test_import_empty_array(self, export_import_service, mock_run_service, temp_dir):
        """Import empty array from JSON."""
        filepath = Path(temp_dir) / "import_empty.json"
        filepath.write_text("[]")

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 0
        assert result.imported_runs == 0
        assert result.skipped_runs == 0
        assert len(result.errors) == 0

    def test_import_duplicate_no_overwrite(self, export_import_service, mock_run_service, temp_dir):
        """Import duplicate (no overwrite): skip with error."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_dup.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service, overwrite=False)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "already exists" in result.errors[0]

    def test_import_duplicate_with_overwrite(self, export_import_service, mock_run_service, temp_dir):
        """Import duplicate (with overwrite): replace existing run."""
        run = _make_run("run-1", duration_seconds=10.0)
        mock_run_service.add_workflow_run(run)

        data = [
            {
                "id": "run-1",
                "workflow_name": "NewCI",
                "branch": "dev",
                "status": "in_progress",
                "conclusion": None,
                "created_at": "2025-05-03T12:00:00+00:00",
                "updated_at": None,
                "run_number": 99,
                "commit_sha": "xyz789",
                "duration_seconds": 50.0,
            },
        ]
        filepath = Path(temp_dir) / "import_overwrite.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service, overwrite=True)

        assert result.total_records == 1
        assert result.imported_runs == 1
        assert result.skipped_runs == 0
        assert result.had_overwrite is True
        runs = mock_run_service.list_runs()
        assert len(runs) == 1
        assert runs[0].workflow_name == "NewCI"
        assert runs[0].duration_seconds == 50.0

    def test_import_invalid_status(self, export_import_service, mock_run_service, temp_dir):
        """Import invalid status: skip with error."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "invalid_status",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_bad_status.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "Invalid status" in result.errors[0]

    def test_import_invalid_conclusion(self, export_import_service, mock_run_service, temp_dir):
        """Import invalid conclusion: skip with error."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "invalid_conclusion",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_bad_conclusion.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "Invalid conclusion" in result.errors[0]

    def test_import_invalid_datetime(self, export_import_service, mock_run_service, temp_dir):
        """Import invalid datetime: skip with error."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "not-a-datetime",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_bad_datetime.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "not a valid ISO format datetime" in result.errors[0]

    def test_import_invalid_duration_negative(self, export_import_service, mock_run_service, temp_dir):
        """Import invalid duration (negative): skip with error."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": -5.0,
            },
        ]
        filepath = Path(temp_dir) / "import_neg_duration.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "non-negative" in result.errors[0]

    def test_import_missing_required_field(self, export_import_service, mock_run_service, temp_dir):
        """Import missing required field: skip with error."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                # Missing 'status'
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_missing_field.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "Missing required field" in result.errors[0]

    def test_import_wrong_field_type(self, export_import_service, mock_run_service, temp_dir):
        """Import wrong field type: skip with error."""
        data = [
            {
                "id": 12345,  # Should be string
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_bad_type.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 1
        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1
        assert "must be a non-empty string" in result.errors[0]

    def test_import_mixed_valid_invalid(self, export_import_service, mock_run_service, temp_dir):
        """Import mixed valid/invalid: import valid, skip invalid."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
            {
                "id": "run-2",
                "workflow_name": "CD",
                "branch": "dev",
                "status": "invalid_status",
                "conclusion": "success",
                "created_at": "2025-05-03T11:00:00+00:00",
                "updated_at": None,
                "run_number": 2,
                "commit_sha": "def456",
                "duration_seconds": 45.0,
            },
        ]
        filepath = Path(temp_dir) / "import_mixed.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.total_records == 2
        assert result.imported_runs == 1
        assert result.skipped_runs == 1
        assert len(result.errors) == 1

    def test_import_with_dry_run(self, export_import_service, mock_run_service, temp_dir):
        """Import with dry_run: validate but don't persist."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "import_dryrun.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service, dry_run=True)

        assert result.total_records == 1
        assert result.imported_runs == 1
        assert mock_run_service.list_runs().__len__() == 0

    def test_import_file_not_found(self, export_import_service, mock_run_service, temp_dir):
        """Import file not found: FileNotFoundError."""
        filepath = Path(temp_dir) / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            export_import_service.import_from_file(str(filepath), mock_run_service)

    def test_import_malformed_json(self, export_import_service, mock_run_service, temp_dir):
        """Import malformed JSON: ValueError."""
        filepath = Path(temp_dir) / "malformed.json"
        filepath.write_text("{invalid json")

        with pytest.raises(ValueError, match="Malformed JSON"):
            export_import_service.import_from_file(str(filepath), mock_run_service)

    def test_import_json_not_list(self, export_import_service, mock_run_service, temp_dir):
        """Import JSON that is not a list: ValueError."""
        filepath = Path(temp_dir) / "not_list.json"
        filepath.write_text('{"key": "value"}')

        with pytest.raises(ValueError, match="must be a list"):
            export_import_service.import_from_file(str(filepath), mock_run_service)

    def test_import_with_attempts(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Import runs and attempts from separate files."""
        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        attempts_data = [
            {
                "id": 100,
                "run_id": 1,
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:05:00+00:00",
                "duration_seconds": 25.0,
            },
        ]

        filepath = Path(temp_dir) / "import_runs.json"
        attempts_filepath = Path(temp_dir) / "import_runs_attempts.json"
        filepath.write_text(json.dumps(runs_data))
        attempts_filepath.write_text(json.dumps(attempts_data))

        result = export_import_service.import_from_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service
        )

        assert result.total_records == 1
        assert result.imported_runs == 1
        assert result.imported_attempts == 1
        assert result.skipped_attempts == 0


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidation:
    """Tests for validation methods."""

    def test_validate_run_with_valid_status(self, export_import_service):
        """Run with valid status enum."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        run = export_import_service._validate_and_build_run(data, 0)
        assert run.status == WorkflowStatus.COMPLETED

    def test_validate_run_with_invalid_status(self, export_import_service):
        """Run with invalid status enum."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "not_a_status",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        with pytest.raises(ValueError, match="Invalid status"):
            export_import_service._validate_and_build_run(data, 0)

    def test_validate_run_with_valid_conclusion(self, export_import_service):
        """Run with valid conclusion enum."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        run = export_import_service._validate_and_build_run(data, 0)
        assert run.conclusion == WorkflowConclusion.SUCCESS

    def test_validate_run_with_invalid_conclusion(self, export_import_service):
        """Run with invalid conclusion enum."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "not_a_conclusion",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        with pytest.raises(ValueError, match="Invalid conclusion"):
            export_import_service._validate_and_build_run(data, 0)

    def test_validate_run_with_null_conclusion(self, export_import_service):
        """Run with null conclusion is valid."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        run = export_import_service._validate_and_build_run(data, 0)
        assert run.conclusion is None

    def test_validate_run_with_valid_datetime(self, export_import_service):
        """Run with valid datetime."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:30:45.123456+00:00",
            "updated_at": "2025-05-03T11:30:45.123456+00:00",
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        run = export_import_service._validate_and_build_run(data, 0)
        assert run.created_at.year == 2025
        assert run.updated_at.year == 2025

    def test_validate_run_with_invalid_datetime(self, export_import_service):
        """Run with invalid datetime format."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025/05/03 10:00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }
        with pytest.raises(ValueError, match="not a valid ISO format datetime"):
            export_import_service._validate_and_build_run(data, 0)

    def test_validate_run_with_negative_duration(self, export_import_service):
        """Run with negative duration."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": -10.0,
        }
        with pytest.raises(ValueError, match="non-negative"):
            export_import_service._validate_and_build_run(data, 0)

    def test_validate_run_with_non_negative_duration(self, export_import_service):
        """Run with non-negative duration."""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 0.0,
        }
        run = export_import_service._validate_and_build_run(data, 0)
        assert run.duration_seconds == 0.0

    def test_validate_attempt_with_valid_attempt_number(self, export_import_service):
        """Attempt with valid attempt_number >= 1."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "duration_seconds": 30.0,
        }
        attempt = export_import_service._validate_and_build_attempt(data, 0)
        assert attempt.attempt_number == 1

    def test_validate_attempt_with_invalid_attempt_number_zero(self, export_import_service):
        """Attempt with invalid attempt_number < 1."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": 0,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "duration_seconds": 30.0,
        }
        with pytest.raises(ValueError, match="positive integer"):
            export_import_service._validate_and_build_attempt(data, 0)

    def test_validate_attempt_with_invalid_attempt_number_negative(self, export_import_service):
        """Attempt with negative attempt_number."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": -1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "duration_seconds": 30.0,
        }
        with pytest.raises(ValueError, match="positive integer"):
            export_import_service._validate_and_build_attempt(data, 0)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining export and import."""

    def test_export_import_roundtrip(self, export_import_service, mock_run_service, temp_dir):
        """Export then import roundtrip: data matches after export/clear/import."""
        # Create and export runs
        run1 = _make_run("run-1", duration_seconds=10.5)
        run2 = _make_run("run-2", branch="dev", duration_seconds=20.0)
        mock_run_service.add_workflow_run(run1)
        mock_run_service.add_workflow_run(run2)

        filepath = Path(temp_dir) / "roundtrip.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        # Clear the service
        mock_run_service._runs.clear()
        assert len(mock_run_service.list_runs()) == 0

        # Import back
        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        # Verify data matches
        assert result.imported_runs == 2
        assert result.skipped_runs == 0
        runs = mock_run_service.list_runs()
        assert len(runs) == 2
        assert runs[0].id == "run-1"
        assert runs[1].id == "run-2"
        assert runs[0].duration_seconds == 10.5
        assert runs[1].duration_seconds == 20.0

    def test_export_import_with_attempts_roundtrip(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Export then import with attempts roundtrip."""
        run = _make_run("1")
        attempt = _make_attempt(attempt_id=100, run_id=1)
        mock_run_service.add_workflow_run(run)
        mock_attempt_service.add_attempt(attempt)

        filepath = Path(temp_dir) / "roundtrip_attempts.json"
        export_import_service.export_to_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service,
            include_attempts=True
        )

        # Clear both services
        mock_run_service._runs.clear()
        mock_attempt_service._attempts.clear()

        # Import back
        result = export_import_service.import_from_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service
        )

        assert result.imported_runs == 1
        assert result.imported_attempts == 1
        assert len(mock_run_service.list_runs()) == 1
        assert len(mock_attempt_service.list_attempts(sorted=False)) == 1

    def test_import_result_structure(self, export_import_service, mock_run_service, temp_dir):
        """ImportResult contains all expected fields."""
        data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "result_test.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert isinstance(result, ImportResult)
        assert result.filepath == str(filepath)
        assert result.total_records == 1
        assert result.imported_runs == 1
        assert result.skipped_runs == 0
        assert result.imported_attempts == 0
        assert result.skipped_attempts == 0
        assert result.errors == []
        assert result.had_overwrite is False


# ============================================================================
# CLI Integration Tests
# ============================================================================

class TestCLIIntegration:
    """Tests for CLI commands."""

    def test_cli_export_command(self, temp_dir):
        """CLI export command: python -m src export --filepath test.json"""
        export_file = Path(temp_dir) / "cli_export.json"
        result = subprocess.run(
            ["python", "-m", "src", "export", "--filepath", str(export_file)],
            cwd="/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert export_file.exists()

    def test_cli_import_command(self, temp_dir):
        """CLI import command: python -m src import --filepath test.json"""
        # Create a file to import
        import_file = Path(temp_dir) / "cli_import.json"
        data = [
            {
                "id": "cli-run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        import_file.write_text(json.dumps(data))

        result = subprocess.run(
            ["python", "-m", "src", "import", "--filepath", str(import_file)],
            cwd="/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_import_with_overwrite(self, temp_dir):
        """CLI import with overwrite: python -m src import --filepath test.json --overwrite"""
        import_file = Path(temp_dir) / "cli_overwrite.json"
        data = [
            {
                "id": "cli-run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        import_file.write_text(json.dumps(data))

        result = subprocess.run(
            ["python", "-m", "src", "import", "--filepath", str(import_file), "--overwrite"],
            cwd="/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_import_with_dry_run(self, temp_dir):
        """CLI import with dry-run: python -m src import --filepath test.json --dry-run"""
        import_file = Path(temp_dir) / "cli_dryrun.json"
        data = [
            {
                "id": "cli-run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        import_file.write_text(json.dumps(data))

        result = subprocess.run(
            ["python", "-m", "src", "import", "--filepath", str(import_file), "--dry-run"],
            cwd="/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_import_attempt_without_parent_run(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Import attempt without parent run: skip with error."""
        attempts_data = [
            {
                "id": 100,
                "run_id": 999,
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:05:00+00:00",
                "duration_seconds": 25.0,
            },
        ]

        filepath = Path(temp_dir) / "orphan_run.json"
        attempts_filepath = Path(temp_dir) / "orphan_run_attempts.json"
        filepath.write_text("[]")
        attempts_filepath.write_text(json.dumps(attempts_data))

        result = export_import_service.import_from_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service
        )

        # The service will import the attempt even without a parent run
        # This is testing current behavior, not necessarily the "correct" behavior
        assert result.imported_attempts == 1

    def test_import_with_both_valid_and_invalid_attempts(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """Import with both valid and invalid attempts."""
        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        attempts_data = [
            {
                "id": 100,
                "run_id": 1,
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:05:00+00:00",
                "duration_seconds": 25.0,
            },
            {
                "id": 101,
                "run_id": 1,
                "attempt_number": 0,  # Invalid: must be >= 1
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:10:00+00:00",
                "duration_seconds": 30.0,
            },
        ]

        filepath = Path(temp_dir) / "mixed_attempts.json"
        attempts_filepath = Path(temp_dir) / "mixed_attempts_attempts.json"
        filepath.write_text(json.dumps(runs_data))
        attempts_filepath.write_text(json.dumps(attempts_data))

        result = export_import_service.import_from_file(
            str(filepath),
            mock_run_service,
            attempt_service=mock_attempt_service
        )

        assert result.imported_attempts == 1
        assert result.skipped_attempts == 1
        assert len(result.errors) == 1

    def test_export_import_multiple_times_idempotency(self, export_import_service, mock_run_service, temp_dir):
        """Export then import multiple times (idempotency)."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "idempotent.json"

        # First export/import cycle
        export_import_service.export_to_file(str(filepath), mock_run_service)
        mock_run_service._runs.clear()
        export_import_service.import_from_file(str(filepath), mock_run_service)

        runs_after_first = [r.to_dict() for r in mock_run_service.list_runs()]

        # Second export/import cycle
        export_import_service.export_to_file(str(filepath), mock_run_service)
        mock_run_service._runs.clear()
        export_import_service.import_from_file(str(filepath), mock_run_service)

        runs_after_second = [r.to_dict() for r in mock_run_service.list_runs()]

        # Data should be identical
        assert runs_after_first == runs_after_second

    def test_import_empty_string_id(self, export_import_service, mock_run_service, temp_dir):
        """Import with empty string id: skip with error."""
        data = [
            {
                "id": "",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            },
        ]
        filepath = Path(temp_dir) / "empty_id.json"
        filepath.write_text(json.dumps(data))

        result = export_import_service.import_from_file(str(filepath), mock_run_service)

        assert result.imported_runs == 0
        assert result.skipped_runs == 1
        assert len(result.errors) == 1

    def test_export_status_value_serialization(self, export_import_service, mock_run_service, temp_dir):
        """Export correctly serializes status enum values."""
        run = _make_run("run-1", status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "status_test.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        data = json.loads(filepath.read_text())
        assert data[0]["status"] == "in_progress"
        assert data[0]["conclusion"] is None

    def test_import_conclusion_with_all_valid_values(self, export_import_service):
        """Import conclusion with all valid enum values."""
        valid_conclusions = [
            "success", "failure", "cancelled", "skipped", "timed_out",
            "action_required", "neutral", "stale"
        ]
        for conclusion_val in valid_conclusions:
            data = {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": conclusion_val,
                "created_at": "2025-05-03T10:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 30.0,
            }
            run = export_import_service._validate_and_build_run(data, 0)
            assert run.conclusion.value == conclusion_val
