"""Comprehensive tests for WorkflowDataPortabilityService."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.models.workflow_run import WorkflowRun
from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_data_portability_service import WorkflowDataPortabilityService


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    run_number: int = 1,
    commit_sha: str = "abc123",
    duration_seconds: float = 10.0,
) -> WorkflowRun:
    """Helper to create a WorkflowRun."""
    if created_at is None:
        created_at = datetime(2026, 5, 3, 10, 0, 0)
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
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    started_at: datetime = None,
    completed_at: datetime = None,
    duration_seconds: float = 5.0,
    logs_url: str = "https://logs.example.com",
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt."""
    if started_at is None:
        started_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        logs_url=logs_url,
    )


@pytest.fixture
def mock_run_service():
    """Mock WorkflowRunService."""
    service = MagicMock()
    service.list_runs.return_value = []
    service.get_run_detail.return_value = None
    return service


@pytest.fixture
def mock_attempt_service():
    """Mock WorkflowAttemptService."""
    service = MagicMock()
    service.list_attempts.return_value = []
    service.get_attempt_detail.return_value = None
    return service


@pytest.fixture
def portability_service(mock_run_service, mock_attempt_service):
    """Create a WorkflowDataPortabilityService with mocked dependencies."""
    return WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)


class TestExportRuns:
    """Test cases for export_runs method."""

    def test_export_runs_with_explicit_list(self, portability_service, tmp_path):
        """Export a list of explicitly provided runs."""
        runs = [
            _make_run("run-1", duration_seconds=10.0),
            _make_run("run-2", branch="develop", duration_seconds=20.0),
        ]

        output_file = tmp_path / "export.json"
        count = portability_service.export_runs(str(output_file), runs=runs)

        assert count == 2
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["id"] == "run-1"
        assert data[1]["id"] == "run-2"
        assert data[0]["duration_seconds"] == 10.0
        assert data[1]["duration_seconds"] == 20.0

    def test_export_runs_from_service(self, mock_run_service, mock_attempt_service, tmp_path):
        """Export all runs from service when no explicit list provided."""
        runs = [
            _make_run("run-1"),
            _make_run("run-2", branch="develop"),
        ]
        mock_run_service.list_runs.return_value = runs

        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        output_file = tmp_path / "export.json"
        count = service.export_runs(str(output_file))

        assert count == 2
        mock_run_service.list_runs.assert_called_once()

    def test_export_runs_empty_list(self, portability_service, tmp_path):
        """Export an empty list of runs."""
        output_file = tmp_path / "export.json"
        count = portability_service.export_runs(str(output_file), runs=[])

        assert count == 0
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data == []

    def test_export_runs_creates_parent_directories(self, portability_service, tmp_path):
        """Export creates parent directories if they don't exist."""
        output_file = tmp_path / "subdir1" / "subdir2" / "export.json"
        runs = [_make_run("run-1")]

        count = portability_service.export_runs(str(output_file), runs=runs)

        assert count == 1
        assert output_file.exists()

    def test_export_runs_preserves_all_fields(self, portability_service, tmp_path):
        """Export preserves all run fields including optional ones."""
        created_at = datetime(2026, 5, 3, 10, 30, 45)
        updated_at = datetime(2026, 5, 3, 11, 0, 0)

        run = WorkflowRun(
            id="run-special",
            workflow_name="Deploy",
            branch="release-1.0",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=created_at,
            updated_at=updated_at,
            run_number=42,
            commit_sha="deadbeef",
            duration_seconds=123.456,
        )

        output_file = tmp_path / "export.json"
        portability_service.export_runs(str(output_file), runs=[run])

        with open(output_file, "r") as f:
            data = json.load(f)

        exported = data[0]
        assert exported["id"] == "run-special"
        assert exported["workflow_name"] == "Deploy"
        assert exported["branch"] == "release-1.0"
        assert exported["status"] == "completed"
        assert exported["conclusion"] == "failure"
        assert exported["created_at"] == created_at.isoformat()
        assert exported["updated_at"] == updated_at.isoformat()
        assert exported["run_number"] == 42
        assert exported["commit_sha"] == "deadbeef"
        assert exported["duration_seconds"] == 123.456

    def test_export_runs_handles_none_optional_fields(self, portability_service, tmp_path):
        """Export handles None values for optional fields."""
        run = WorkflowRun(
            id="run-minimal",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime(2026, 5, 3, 10, 0, 0),
            updated_at=None,
            run_number=None,
            commit_sha=None,
            duration_seconds=0.0,
        )

        output_file = tmp_path / "export.json"
        portability_service.export_runs(str(output_file), runs=[run])

        with open(output_file, "r") as f:
            data = json.load(f)

        exported = data[0]
        assert exported["conclusion"] is None
        assert exported["updated_at"] is None
        assert exported["run_number"] is None
        assert exported["commit_sha"] is None

    def test_export_runs_invalid_filepath_raises_ioerror(self, portability_service):
        """Export raises IOError for invalid filepath."""
        # Use a path that cannot be created (e.g., in /proc on Linux)
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
            with pytest.raises(IOError):
                portability_service.export_runs("/proc/invalid/path.json", runs=[_make_run()])


class TestImportRuns:
    """Test cases for import_runs method."""

    def test_import_runs_valid_file(self, mock_run_service, mock_attempt_service, tmp_path):
        """Import valid runs from JSON file."""
        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)

        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": "2026-05-03T11:00:00",
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 10.0,
            },
            {
                "id": "run-2",
                "workflow_name": "CD",
                "branch": "develop",
                "status": "in_progress",
                "conclusion": None,
                "created_at": "2026-05-03T10:30:00",
                "updated_at": None,
                "run_number": 2,
                "commit_sha": "def456",
                "duration_seconds": 0.0,
            },
        ]

        input_file = tmp_path / "import.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = service.import_runs(str(input_file))

        assert result["count"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["imported"]) == 2
        assert len(result["skipped"]) == 0
        assert result["imported"][0].id == "run-1"
        assert result["imported"][1].id == "run-2"
        assert mock_run_service.add_workflow_run.call_count == 2

    def test_import_runs_skip_duplicates_true(self, mock_run_service, mock_attempt_service, tmp_path):
        """Import with skip_duplicates=True skips duplicate IDs."""
        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)

        # Mock that run-1 already exists
        mock_run_service.get_run_detail.side_effect = lambda id: (
            _make_run("run-1") if id == "run-1" else None
        )

        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 10.0,
            },
            {
                "id": "run-2",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": None,
                "run_number": 2,
                "commit_sha": "def456",
                "duration_seconds": 10.0,
            },
        ]

        input_file = tmp_path / "import.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = service.import_runs(str(input_file), skip_duplicates=True)

        assert result["count"] == 2
        assert result["successful"] == 1
        assert len(result["skipped"]) == 1
        assert result["skipped"][0]["id"] == "run-1"
        assert mock_run_service.add_workflow_run.call_count == 1

    def test_import_runs_skip_duplicates_false_raises_error(self, mock_run_service, mock_attempt_service, tmp_path):
        """Import with skip_duplicates=False raises error on duplicate."""
        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)

        # Mock that run-1 already exists
        mock_run_service.get_run_detail.side_effect = lambda id: (
            _make_run("run-1") if id == "run-1" else None
        )

        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 10.0,
            },
        ]

        input_file = tmp_path / "import.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = service.import_runs(str(input_file), skip_duplicates=False)

        # With skip_duplicates=False, the run is counted as failed but processing continues
        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_runs_file_not_found(self, portability_service):
        """Import raises IOError when file does not exist."""
        with pytest.raises(IOError, match="File not found"):
            portability_service.import_runs("/nonexistent/file.json")

    def test_import_runs_invalid_json(self, portability_service, tmp_path):
        """Import raises ValueError on invalid JSON."""
        input_file = tmp_path / "invalid.json"
        with open(input_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            portability_service.import_runs(str(input_file))

    def test_import_runs_not_list_raises_error(self, portability_service, tmp_path):
        """Import raises IOError when JSON is not an array."""
        input_file = tmp_path / "notlist.json"
        with open(input_file, "w") as f:
            json.dump({"id": "run-1"}, f)

        with pytest.raises(IOError, match="Expected JSON file to contain an array of runs"):
            portability_service.import_runs(str(input_file))

    def test_import_runs_missing_required_fields(self, portability_service, tmp_path):
        """Import counts as failed when required fields are missing."""
        runs_data = [
            {
                "id": "run-1",
                # Missing: workflow_name, branch, status, created_at
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
            },
        ]

        input_file = tmp_path / "missing.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = portability_service.import_runs(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_runs_invalid_enum_value(self, portability_service, tmp_path):
        """Import counts as failed when enum values are invalid."""
        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "invalid_status",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": 10.0,
            },
        ]

        input_file = tmp_path / "invalid_enum.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = portability_service.import_runs(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_runs_negative_duration_raises_error(self, portability_service, tmp_path):
        """Import fails when duration_seconds is negative."""
        runs_data = [
            {
                "id": "run-1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-05-03T10:00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
                "duration_seconds": -5.0,
            },
        ]

        input_file = tmp_path / "negative_duration.json"
        with open(input_file, "w") as f:
            json.dump(runs_data, f)

        result = portability_service.import_runs(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_runs_empty_file(self, portability_service, tmp_path):
        """Import empty array succeeds with no imports."""
        input_file = tmp_path / "empty.json"
        with open(input_file, "w") as f:
            json.dump([], f)

        result = portability_service.import_runs(str(input_file))

        assert result["count"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0


class TestExportAttempts:
    """Test cases for export_attempts method."""

    def test_export_attempts_with_explicit_list(self, portability_service, tmp_path):
        """Export a list of explicitly provided attempts."""
        attempts = [
            _make_attempt("attempt-1", run_id="run-1"),
            _make_attempt("attempt-2", run_id="run-1", attempt_number=2),
        ]

        output_file = tmp_path / "export.json"
        count = portability_service.export_attempts(str(output_file), attempts=attempts)

        assert count == 2
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["id"] == "attempt-1"
        assert data[1]["id"] == "attempt-2"

    def test_export_attempts_from_service(self, mock_run_service, mock_attempt_service, tmp_path):
        """Export all attempts from service when no explicit list provided."""
        attempts = [
            _make_attempt("attempt-1", run_id="run-1"),
            _make_attempt("attempt-2", run_id="run-1", attempt_number=2),
        ]
        mock_attempt_service.list_attempts.return_value = attempts

        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        output_file = tmp_path / "export.json"
        count = service.export_attempts(str(output_file))

        assert count == 2
        mock_attempt_service.list_attempts.assert_called_once()

    def test_export_attempts_empty_list(self, portability_service, tmp_path):
        """Export an empty list of attempts."""
        output_file = tmp_path / "export.json"
        count = portability_service.export_attempts(str(output_file), attempts=[])

        assert count == 0
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data == []

    def test_export_attempts_preserves_all_fields(self, portability_service, tmp_path):
        """Export preserves all attempt fields."""
        started_at = datetime(2026, 5, 3, 10, 30, 45)
        completed_at = datetime(2026, 5, 3, 10, 35, 0)

        attempt = WorkflowRunAttempt(
            id="attempt-special",
            run_id="run-123",
            attempt_number=3,
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.TIMED_OUT,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=254.5,
            logs_url="https://logs.example.com/attempt-3",
        )

        output_file = tmp_path / "export.json"
        portability_service.export_attempts(str(output_file), attempts=[attempt])

        with open(output_file, "r") as f:
            data = json.load(f)

        exported = data[0]
        assert exported["id"] == "attempt-special"
        assert exported["run_id"] == "run-123"
        assert exported["attempt_number"] == 3
        assert exported["status"] == "completed"
        assert exported["conclusion"] == "timed_out"
        assert exported["started_at"] == started_at.isoformat()
        assert exported["completed_at"] == completed_at.isoformat()
        assert exported["duration_seconds"] == 254.5
        assert exported["logs_url"] == "https://logs.example.com/attempt-3"

    def test_export_attempts_handles_none_optional_fields(self, portability_service, tmp_path):
        """Export handles None values for optional fields."""
        attempt = WorkflowRunAttempt(
            id="attempt-minimal",
            run_id="run-1",
            attempt_number=1,
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            started_at=datetime(2026, 5, 3, 10, 0, 0),
            completed_at=None,
            duration_seconds=0.0,
            logs_url=None,
        )

        output_file = tmp_path / "export.json"
        portability_service.export_attempts(str(output_file), attempts=[attempt])

        with open(output_file, "r") as f:
            data = json.load(f)

        exported = data[0]
        assert exported["conclusion"] is None
        assert exported["completed_at"] is None
        assert exported["logs_url"] is None


class TestImportAttempts:
    """Test cases for import_attempts method."""

    def test_import_attempts_valid_file(self, mock_run_service, mock_attempt_service, tmp_path):
        """Import valid attempts from JSON file."""
        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)

        attempts_data = [
            {
                "id": "attempt-1",
                "run_id": "run-1",
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-05-03T10:00:00",
                "completed_at": "2026-05-03T10:05:00",
                "duration_seconds": 300.0,
                "logs_url": "https://logs.example.com/1",
            },
            {
                "id": "attempt-2",
                "run_id": "run-2",
                "attempt_number": 1,
                "status": "in_progress",
                "conclusion": None,
                "started_at": "2026-05-03T10:30:00",
                "completed_at": None,
                "duration_seconds": 0.0,
                "logs_url": None,
            },
        ]

        input_file = tmp_path / "import.json"
        with open(input_file, "w") as f:
            json.dump(attempts_data, f)

        result = service.import_attempts(str(input_file))

        assert result["count"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["imported"]) == 2
        assert len(result["skipped"]) == 0
        assert result["imported"][0].id == "attempt-1"
        assert result["imported"][1].id == "attempt-2"
        assert mock_attempt_service.add_attempt.call_count == 2

    def test_import_attempts_skip_duplicates_true(self, mock_run_service, mock_attempt_service, tmp_path):
        """Import with skip_duplicates=True skips duplicate IDs."""
        service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)

        # Mock that attempt-1 already exists
        mock_attempt_service.get_attempt_detail.side_effect = lambda id: (
            _make_attempt("attempt-1") if id == "attempt-1" else None
        )

        attempts_data = [
            {
                "id": "attempt-1",
                "run_id": "run-1",
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-05-03T10:00:00",
                "completed_at": "2026-05-03T10:05:00",
                "duration_seconds": 300.0,
                "logs_url": None,
            },
            {
                "id": "attempt-2",
                "run_id": "run-1",
                "attempt_number": 2,
                "status": "completed",
                "conclusion": "failure",
                "started_at": "2026-05-03T10:10:00",
                "completed_at": "2026-05-03T10:15:00",
                "duration_seconds": 300.0,
                "logs_url": None,
            },
        ]

        input_file = tmp_path / "import.json"
        with open(input_file, "w") as f:
            json.dump(attempts_data, f)

        result = service.import_attempts(str(input_file), skip_duplicates=True)

        assert result["count"] == 2
        assert result["successful"] == 1
        assert len(result["skipped"]) == 1
        assert result["skipped"][0]["id"] == "attempt-1"
        assert mock_attempt_service.add_attempt.call_count == 1

    def test_import_attempts_file_not_found(self, portability_service):
        """Import raises IOError when file does not exist."""
        with pytest.raises(IOError, match="File not found"):
            portability_service.import_attempts("/nonexistent/file.json")

    def test_import_attempts_invalid_json(self, portability_service, tmp_path):
        """Import raises ValueError on invalid JSON."""
        input_file = tmp_path / "invalid.json"
        with open(input_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            portability_service.import_attempts(str(input_file))

    def test_import_attempts_not_list_raises_error(self, portability_service, tmp_path):
        """Import raises IOError when JSON is not an array."""
        input_file = tmp_path / "notlist.json"
        with open(input_file, "w") as f:
            json.dump({"id": "attempt-1"}, f)

        with pytest.raises(IOError, match="Expected JSON file to contain an array of attempts"):
            portability_service.import_attempts(str(input_file))

    def test_import_attempts_missing_required_fields(self, portability_service, tmp_path):
        """Import counts as failed when required fields are missing."""
        attempts_data = [
            {
                "id": "attempt-1",
                # Missing: run_id, attempt_number, status, started_at
                "conclusion": "success",
                "started_at": "2026-05-03T10:00:00",
            },
        ]

        input_file = tmp_path / "missing.json"
        with open(input_file, "w") as f:
            json.dump(attempts_data, f)

        result = portability_service.import_attempts(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_attempts_invalid_enum_value(self, portability_service, tmp_path):
        """Import counts as failed when enum values are invalid."""
        attempts_data = [
            {
                "id": "attempt-1",
                "run_id": "run-1",
                "attempt_number": 1,
                "status": "invalid_status",
                "conclusion": "success",
                "started_at": "2026-05-03T10:00:00",
                "completed_at": None,
                "duration_seconds": 0.0,
                "logs_url": None,
            },
        ]

        input_file = tmp_path / "invalid_enum.json"
        with open(input_file, "w") as f:
            json.dump(attempts_data, f)

        result = portability_service.import_attempts(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_attempts_negative_duration_raises_error(self, portability_service, tmp_path):
        """Import fails when duration_seconds is negative."""
        attempts_data = [
            {
                "id": "attempt-1",
                "run_id": "run-1",
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-05-03T10:00:00",
                "completed_at": "2026-05-03T10:05:00",
                "duration_seconds": -5.0,
                "logs_url": None,
            },
        ]

        input_file = tmp_path / "negative_duration.json"
        with open(input_file, "w") as f:
            json.dump(attempts_data, f)

        result = portability_service.import_attempts(str(input_file))

        assert result["count"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

    def test_import_attempts_empty_file(self, portability_service, tmp_path):
        """Import empty array succeeds with no imports."""
        input_file = tmp_path / "empty.json"
        with open(input_file, "w") as f:
            json.dump([], f)

        result = portability_service.import_attempts(str(input_file))

        assert result["count"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0


class TestValidateRunSchema:
    """Test cases for _validate_run_schema method."""

    def test_validate_run_schema_valid(self, portability_service):
        """Validate schema accepts valid run data."""
        valid_run = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "created_at": "2026-05-03T10:00:00",
        }

        # Should not raise
        portability_service._validate_run_schema(valid_run)

    def test_validate_run_schema_missing_id(self, portability_service):
        """Validate schema rejects missing id."""
        invalid_run = {
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "created_at": "2026-05-03T10:00:00",
        }

        with pytest.raises(ValueError, match="Missing required fields for run"):
            portability_service._validate_run_schema(invalid_run)

    def test_validate_run_schema_missing_multiple_fields(self, portability_service):
        """Validate schema rejects multiple missing fields."""
        invalid_run = {
            "id": "run-1",
            "status": "completed",
        }

        with pytest.raises(ValueError, match="Missing required fields for run"):
            portability_service._validate_run_schema(invalid_run)

    def test_validate_run_schema_all_required_fields(self, portability_service):
        """Validate schema accepts data with all required fields."""
        required_fields = ["id", "workflow_name", "branch", "status", "created_at"]
        run_data = {field: "value" for field in required_fields}

        # Should not raise
        portability_service._validate_run_schema(run_data)


class TestValidateAttemptSchema:
    """Test cases for _validate_attempt_schema method."""

    def test_validate_attempt_schema_valid(self, portability_service):
        """Validate schema accepts valid attempt data."""
        valid_attempt = {
            "id": "attempt-1",
            "run_id": "run-1",
            "attempt_number": 1,
            "status": "completed",
            "started_at": "2026-05-03T10:00:00",
        }

        # Should not raise
        portability_service._validate_attempt_schema(valid_attempt)

    def test_validate_attempt_schema_missing_id(self, portability_service):
        """Validate schema rejects missing id."""
        invalid_attempt = {
            "run_id": "run-1",
            "attempt_number": 1,
            "status": "completed",
            "started_at": "2026-05-03T10:00:00",
        }

        with pytest.raises(ValueError, match="Missing required fields for attempt"):
            portability_service._validate_attempt_schema(invalid_attempt)

    def test_validate_attempt_schema_missing_multiple_fields(self, portability_service):
        """Validate schema rejects multiple missing fields."""
        invalid_attempt = {
            "id": "attempt-1",
            "run_id": "run-1",
        }

        with pytest.raises(ValueError, match="Missing required fields for attempt"):
            portability_service._validate_attempt_schema(invalid_attempt)

    def test_validate_attempt_schema_all_required_fields(self, portability_service):
        """Validate schema accepts data with all required fields."""
        required_fields = ["id", "run_id", "attempt_number", "status", "started_at"]
        attempt_data = {field: "value" for field in required_fields}

        # Should not raise
        portability_service._validate_attempt_schema(attempt_data)


class TestRoundTripIntegration:
    """Test round-trip export then import consistency."""

    def test_export_then_import_runs_preserves_data(self, mock_run_service, mock_attempt_service, tmp_path):
        """Export and then import runs should preserve all data."""
        # Create runs
        original_runs = [
            _make_run("run-1", duration_seconds=10.0),
            _make_run("run-2", branch="develop", duration_seconds=20.0),
        ]

        # First service exports
        export_service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        export_file = tmp_path / "export.json"
        export_service.export_runs(str(export_file), runs=original_runs)

        # Second service imports
        import_service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        result = import_service.import_runs(str(export_file))

        assert result["successful"] == 2
        assert len(result["imported"]) == 2

        imported_runs = result["imported"]
        for orig, imported in zip(original_runs, imported_runs):
            assert imported.id == orig.id
            assert imported.workflow_name == orig.workflow_name
            assert imported.branch == orig.branch
            assert imported.status == orig.status
            assert imported.conclusion == orig.conclusion
            assert imported.created_at == orig.created_at
            assert imported.updated_at == orig.updated_at
            assert imported.run_number == orig.run_number
            assert imported.commit_sha == orig.commit_sha
            assert imported.duration_seconds == orig.duration_seconds

    def test_export_then_import_attempts_preserves_data(self, mock_run_service, mock_attempt_service, tmp_path):
        """Export and then import attempts should preserve all data."""
        # Create attempts
        original_attempts = [
            _make_attempt("attempt-1", run_id="run-1", attempt_number=1),
            _make_attempt("attempt-2", run_id="run-1", attempt_number=2),
        ]

        # First service exports
        export_service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        export_file = tmp_path / "export.json"
        export_service.export_attempts(str(export_file), attempts=original_attempts)

        # Second service imports
        import_service = WorkflowDataPortabilityService(mock_run_service, mock_attempt_service)
        result = import_service.import_attempts(str(export_file))

        assert result["successful"] == 2
        assert len(result["imported"]) == 2

        imported_attempts = result["imported"]
        for orig, imported in zip(original_attempts, imported_attempts):
            assert imported.id == orig.id
            assert imported.run_id == orig.run_id
            assert imported.attempt_number == orig.attempt_number
            assert imported.status == orig.status
            assert imported.conclusion == orig.conclusion
            assert imported.started_at == orig.started_at
            assert imported.completed_at == orig.completed_at
            assert imported.duration_seconds == orig.duration_seconds
            assert imported.logs_url == orig.logs_url
