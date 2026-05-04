"""Tests verifying export/import service uses public APIs only."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import inspect

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_export_import_service import WorkflowRunExportImportService
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


def _make_run(run_id: str = "run-1") -> WorkflowRun:
    """Create a test WorkflowRun."""
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


def _make_attempt(attempt_id: int = 1, run_id: int = 1) -> WorkflowRunAttempt:
    """Create a test WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
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


class TestPublicAPIUsageInExport:
    """Tests verifying export uses only public APIs."""

    def test_export_uses_list_runs_public_method(self, export_import_service, mock_run_service, temp_dir):
        """export_to_file calls service.list_runs() (public method)."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        # Mock list_runs to track if it's called
        original_list_runs = mock_run_service.list_runs
        with patch.object(mock_run_service, 'list_runs', wraps=original_list_runs) as mock_list:
            filepath = Path(temp_dir) / "test.json"
            export_import_service.export_to_file(str(filepath), mock_run_service)
            mock_list.assert_called_once()

    def test_export_does_not_access_private_runs_attribute(self, export_import_service, mock_run_service, temp_dir):
        """export_to_file does not access _runs private attribute."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "test.json"
        # Should not raise AttributeError about _runs
        export_import_service.export_to_file(str(filepath), mock_run_service)

        # Verify file was created
        assert filepath.exists()

    def test_export_uses_list_attempts_public_method(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """export_to_file calls attempt_service.list_attempts() (public method)."""
        run = _make_run("run-1")
        attempt = _make_attempt()
        mock_run_service.add_workflow_run(run)
        mock_attempt_service.add_attempt(attempt)

        original_list_attempts = mock_attempt_service.list_attempts
        with patch.object(mock_attempt_service, 'list_attempts', wraps=original_list_attempts) as mock_list:
            filepath = Path(temp_dir) / "test.json"
            export_import_service.export_to_file(
                str(filepath),
                mock_run_service,
                attempt_service=mock_attempt_service,
                include_attempts=True
            )
            mock_list.assert_called_once()


class TestPublicAPIUsageInImport:
    """Tests verifying import uses only public APIs."""

    def test_import_uses_get_run_detail_public_method(self, export_import_service, mock_run_service, temp_dir):
        """import_from_file calls service.get_run_detail() (public method)."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        data = [{
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
        }]
        filepath = Path(temp_dir) / "import.json"
        filepath.write_text(json.dumps(data))

        original_get_run = mock_run_service.get_run_detail
        with patch.object(mock_run_service, 'get_run_detail', wraps=original_get_run) as mock_get:
            export_import_service.import_from_file(str(filepath), mock_run_service, overwrite=False)
            mock_get.assert_called()

    def test_import_uses_add_workflow_run_public_method(self, export_import_service, mock_run_service, temp_dir):
        """import_from_file calls service.add_workflow_run() (public method)."""
        data = [{
            "id": "new-run",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 30.0,
        }]
        filepath = Path(temp_dir) / "import.json"
        filepath.write_text(json.dumps(data))

        original_add = mock_run_service.add_workflow_run
        with patch.object(mock_run_service, 'add_workflow_run', wraps=original_add) as mock_add:
            export_import_service.import_from_file(str(filepath), mock_run_service)
            mock_add.assert_called()

    def test_import_uses_replace_run_public_method(self, export_import_service, mock_run_service, temp_dir):
        """import_from_file calls service.replace_run() (public method) when overwriting."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        data = [{
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
        }]
        filepath = Path(temp_dir) / "import.json"
        filepath.write_text(json.dumps(data))

        original_replace = mock_run_service.replace_run
        with patch.object(mock_run_service, 'replace_run', wraps=original_replace) as mock_replace:
            export_import_service.import_from_file(str(filepath), mock_run_service, overwrite=True)
            mock_replace.assert_called()

    def test_import_uses_get_attempt_public_method(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """import_from_file calls attempt_service.get_attempt() (public method)."""
        attempt = _make_attempt(attempt_id=1)
        mock_attempt_service.add_attempt(attempt)

        runs_data = [{
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
        }]
        attempts_data = [{
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:05:00+00:00",
            "duration_seconds": 25.0,
        }]

        filepath = Path(temp_dir) / "import.json"
        attempts_filepath = Path(temp_dir) / "import_attempts.json"
        filepath.write_text(json.dumps(runs_data))
        attempts_filepath.write_text(json.dumps(attempts_data))

        original_get = mock_attempt_service.get_attempt
        with patch.object(mock_attempt_service, 'get_attempt', wraps=original_get) as mock_get:
            export_import_service.import_from_file(
                str(filepath),
                mock_run_service,
                attempt_service=mock_attempt_service,
                overwrite=False
            )
            mock_get.assert_called()

    def test_import_uses_add_attempt_public_method(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """import_from_file calls attempt_service.add_attempt() (public method)."""
        runs_data = [{
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
        }]
        attempts_data = [{
            "id": 100,
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:05:00+00:00",
            "duration_seconds": 25.0,
        }]

        filepath = Path(temp_dir) / "import.json"
        attempts_filepath = Path(temp_dir) / "import_attempts.json"
        filepath.write_text(json.dumps(runs_data))
        attempts_filepath.write_text(json.dumps(attempts_data))

        original_add = mock_attempt_service.add_attempt
        with patch.object(mock_attempt_service, 'add_attempt', wraps=original_add) as mock_add:
            export_import_service.import_from_file(
                str(filepath),
                mock_run_service,
                attempt_service=mock_attempt_service
            )
            mock_add.assert_called()

    def test_import_uses_replace_attempt_public_method(self, export_import_service, mock_run_service, mock_attempt_service, temp_dir):
        """import_from_file calls attempt_service.replace_attempt() (public method) when overwriting."""
        attempt = _make_attempt(attempt_id=1)
        mock_attempt_service.add_attempt(attempt)

        runs_data = [{
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
        }]
        attempts_data = [{
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "failed",
            "conclusion": "failure",
            "created_at": "2025-05-03T10:05:00+00:00",
            "duration_seconds": 25.0,
        }]

        filepath = Path(temp_dir) / "import.json"
        attempts_filepath = Path(temp_dir) / "import_attempts.json"
        filepath.write_text(json.dumps(runs_data))
        attempts_filepath.write_text(json.dumps(attempts_data))

        original_replace = mock_attempt_service.replace_attempt
        with patch.object(mock_attempt_service, 'replace_attempt', wraps=original_replace) as mock_replace:
            export_import_service.import_from_file(
                str(filepath),
                mock_run_service,
                attempt_service=mock_attempt_service,
                overwrite=True
            )
            mock_replace.assert_called()


class TestPublicAPIMethodSignatures:
    """Tests verifying public API methods exist and have correct signatures."""

    def test_service_has_public_list_runs(self, mock_run_service):
        """WorkflowRunService has public list_runs method."""
        assert hasattr(mock_run_service, 'list_runs')
        assert callable(mock_run_service.list_runs)
        # Verify it's public (doesn't start with _)
        assert not mock_run_service.list_runs.__name__.startswith('_')

    def test_service_has_public_get_run_detail(self, mock_run_service):
        """WorkflowRunService has public get_run_detail method."""
        assert hasattr(mock_run_service, 'get_run_detail')
        assert callable(mock_run_service.get_run_detail)
        assert not mock_run_service.get_run_detail.__name__.startswith('_')

    def test_service_has_public_add_workflow_run(self, mock_run_service):
        """WorkflowRunService has public add_workflow_run method."""
        assert hasattr(mock_run_service, 'add_workflow_run')
        assert callable(mock_run_service.add_workflow_run)
        assert not mock_run_service.add_workflow_run.__name__.startswith('_')

    def test_service_has_public_replace_run(self, mock_run_service):
        """WorkflowRunService has public replace_run method."""
        assert hasattr(mock_run_service, 'replace_run')
        assert callable(mock_run_service.replace_run)
        assert not mock_run_service.replace_run.__name__.startswith('_')

    def test_attempt_service_has_public_list_attempts(self, mock_attempt_service):
        """WorkflowRunAttemptService has public list_attempts method."""
        assert hasattr(mock_attempt_service, 'list_attempts')
        assert callable(mock_attempt_service.list_attempts)
        assert not mock_attempt_service.list_attempts.__name__.startswith('_')

    def test_attempt_service_has_public_get_attempt(self, mock_attempt_service):
        """WorkflowRunAttemptService has public get_attempt method."""
        assert hasattr(mock_attempt_service, 'get_attempt')
        assert callable(mock_attempt_service.get_attempt)
        assert not mock_attempt_service.get_attempt.__name__.startswith('_')

    def test_attempt_service_has_public_add_attempt(self, mock_attempt_service):
        """WorkflowRunAttemptService has public add_attempt method."""
        assert hasattr(mock_attempt_service, 'add_attempt')
        assert callable(mock_attempt_service.add_attempt)
        assert not mock_attempt_service.add_attempt.__name__.startswith('_')

    def test_attempt_service_has_public_replace_attempt(self, mock_attempt_service):
        """WorkflowRunAttemptService has public replace_attempt method."""
        assert hasattr(mock_attempt_service, 'replace_attempt')
        assert callable(mock_attempt_service.replace_attempt)
        assert not mock_attempt_service.replace_attempt.__name__.startswith('_')


class TestNoPrivateMemberAccessInExportImport:
    """Tests verifying export/import doesn't access private members."""

    def test_export_import_source_uses_only_public_methods(self):
        """Verify export/import source code doesn't reference private _storage, _runs, _attempts."""
        import inspect
        source = inspect.getsource(WorkflowRunExportImportService)

        # Check that private members are not accessed in export/import methods
        assert 'service._storage' not in source
        assert 'service._runs' not in source
        assert 'attempt_service._attempts' not in source
        assert 'attempt_service._storage' not in source

    def test_export_uses_to_dict_public_method(self, export_import_service, mock_run_service, temp_dir):
        """export_to_file uses run.to_dict() and attempt.to_dict() public methods."""
        run = _make_run("run-1")
        mock_run_service.add_workflow_run(run)

        filepath = Path(temp_dir) / "test.json"
        export_import_service.export_to_file(str(filepath), mock_run_service)

        data = json.loads(filepath.read_text())
        assert len(data) == 1
        # Verify to_dict was used (it converts enums to values)
        assert data[0]["status"] == "completed"
        assert data[0]["conclusion"] == "success"
