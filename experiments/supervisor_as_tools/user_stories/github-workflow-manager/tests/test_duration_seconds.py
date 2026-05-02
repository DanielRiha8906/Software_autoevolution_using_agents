"""
Comprehensive tests for duration_seconds functionality.

Covers:
- WorkflowRun accepts duration_seconds with default 0.0
- Negative values are rejected with validation error
- Serialization/deserialization works correctly
- Backward compatibility with old JSON files (missing duration_seconds field)
- CLI and interactive menu accept duration_seconds
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_tracker import WorkflowRunTracker
from src.storage.workflow_json_storage import WorkflowJsonStorage
from src.cli.workflow_cli import run_cli, build_parser


# ============================================================================
# WorkflowRun Model Tests
# ============================================================================

class TestWorkflowRunDurationDefault:
    """Test that duration_seconds defaults to 0.0"""

    def test_default_duration_seconds_is_zero(self):
        """duration_seconds should default to 0.0 when not provided"""
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

    def test_explicit_zero_duration(self):
        """Explicitly setting duration_seconds to 0.0 should work"""
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


class TestWorkflowRunDurationValidation:
    """Test validation of duration_seconds values"""

    def test_negative_duration_raises_value_error(self):
        """Negative duration_seconds should raise ValueError"""
        with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
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

    def test_negative_integer_duration_raises_value_error(self):
        """Negative integer duration_seconds should raise ValueError"""
        with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
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
                duration_seconds=-100,
            )

    @pytest.mark.parametrize("duration", [0.0, 0.1, 1.0, 45.5, 3600.0, 999999.99])
    def test_valid_positive_durations(self, duration):
        """Positive durations and zero should be accepted"""
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


class TestWorkflowRunSerialization:
    """Test to_dict and from_dict with duration_seconds"""

    def test_to_dict_includes_duration_seconds(self):
        """to_dict() should include duration_seconds"""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=42.5,
        )
        data = run.to_dict()
        assert "duration_seconds" in data
        assert data["duration_seconds"] == 42.5

    def test_from_dict_with_duration_seconds(self):
        """from_dict() should reconstruct duration_seconds correctly"""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 42.5,
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 42.5

    def test_from_dict_without_duration_seconds_defaults_to_zero(self):
        """from_dict() should default to 0.0 when duration_seconds is missing"""
        data = {
            "id": "run-1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 0.0

    @pytest.mark.parametrize("duration", [0.0, 0.1, 1.0, 45.5, 3600.0, 999999.99])
    def test_roundtrip_serialization(self, duration):
        """to_dict/from_dict roundtrip should preserve duration_seconds"""
        original = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=duration,
        )
        data = original.to_dict()
        reconstructed = WorkflowRun.from_dict(data)
        assert reconstructed.duration_seconds == duration


# ============================================================================
# JSON Storage Tests
# ============================================================================

class TestWorkflowJsonStorageDuration:
    """Test JSON storage persistence of duration_seconds"""

    @pytest.fixture
    def tmp_storage(self, tmp_path):
        return WorkflowJsonStorage(str(tmp_path / "runs.json"))

    def test_save_and_load_preserves_duration(self, tmp_storage):
        """Save/load cycle should preserve duration_seconds"""
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

    def test_json_file_contains_duration_field(self, tmp_storage):
        """Raw JSON file should contain duration_seconds"""
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
            duration_seconds=50.0,
        )
        tmp_storage.save([run])
        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert raw[0]["duration_seconds"] == 50.0

    def test_backward_compatibility_old_json_without_duration(self, tmp_storage):
        """Loading old JSON without duration_seconds should default to 0.0"""
        old_json = json.dumps([{
            "id": "r1",
            "workflow_name": "Deploy",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 42,
            "commit_sha": "deadbeef",
        }])
        Path(tmp_storage.filepath).write_text(old_json)
        loaded = tmp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].duration_seconds == 0.0

    def test_backward_compatibility_mixed_old_new_json(self, tmp_storage):
        """Loading JSON with mix of old and new records should work"""
        mixed_json = json.dumps([
            {
                "id": "r1",
                "workflow_name": "Deploy",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": None,
                "run_number": 42,
                "commit_sha": "deadbeef",
            },
            {
                "id": "r2",
                "workflow_name": "Test",
                "branch": "dev",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-02T00:00:00+00:00",
                "updated_at": None,
                "run_number": 43,
                "commit_sha": "cafebabe",
                "duration_seconds": 100.5,
            },
        ])
        Path(tmp_storage.filepath).write_text(mixed_json)
        loaded = tmp_storage.load()
        assert len(loaded) == 2
        assert loaded[0].duration_seconds == 0.0
        assert loaded[1].duration_seconds == 100.5


# ============================================================================
# Service Layer Tests
# ============================================================================

class TestWorkflowRunServiceDuration:
    """Test WorkflowRunService with duration_seconds"""

    @pytest.fixture
    def service(self):
        storage = MagicMock()
        storage.load.return_value = []
        return WorkflowRunService(storage)

    def test_service_preserves_duration_on_add(self, service):
        """Service should preserve duration_seconds when adding runs"""
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
            duration_seconds=75.5,
        )
        service.add_workflow_run(run)
        listed = service.list_runs()
        assert listed[0].duration_seconds == 75.5

    def test_tracker_passes_duration_to_service(self, service):
        """WorkflowRunTracker.track() should pass duration_seconds to service"""
        tracker = WorkflowRunTracker(service)
        run = tracker.track(
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=88.8,
        )
        assert run.duration_seconds == 88.8
        assert service.get_run_detail(run.id).duration_seconds == 88.8


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLIDurationSeconds:
    """Test CLI parsing and handling of --duration-seconds flag"""

    def test_cli_parser_has_duration_seconds_argument(self):
        """CLI parser should have --duration-seconds argument for add command"""
        parser = build_parser()
        # Parse add command with duration
        args = parser.parse_args(["add", "--name", "CI", "--branch", "main",
                                   "--status", "completed", "--duration-seconds", "42.5"])
        assert hasattr(args, 'duration_seconds')
        assert args.duration_seconds == 42.5

    def test_cli_duration_seconds_default_is_zero(self):
        """CLI should default --duration-seconds to 0.0"""
        parser = build_parser()
        args = parser.parse_args(["add", "--name", "CI", "--branch", "main",
                                   "--status", "completed"])
        assert args.duration_seconds == 0.0

    def test_cli_accepts_float_duration(self):
        """CLI should accept float values for duration_seconds"""
        parser = build_parser()
        args = parser.parse_args(["add", "--name", "CI", "--branch", "main",
                                   "--status", "completed", "--duration-seconds", "123.456"])
        assert args.duration_seconds == 123.456

    def test_cli_accepts_integer_duration(self):
        """CLI should accept integer values for duration_seconds"""
        parser = build_parser()
        args = parser.parse_args(["add", "--name", "CI", "--branch", "main",
                                   "--status", "completed", "--duration-seconds", "100"])
        assert args.duration_seconds == 100.0

    def test_cli_run_add_command_with_duration(self):
        """run_cli should create run with duration_seconds from args"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        run_cli(
            service,
            args=["add", "--name", "CI", "--branch", "main", "--status", "completed",
                  "--duration-seconds", "55.5"],
        )
        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 55.5

    def test_cli_run_add_command_without_duration_uses_default(self):
        """run_cli without --duration-seconds should use default 0.0"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        run_cli(
            service,
            args=["add", "--name", "CI", "--branch", "main", "--status", "completed"],
        )
        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 0.0

    def test_cli_add_command_output_includes_run_id(self):
        """CLI add command should output confirmation with run ID"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(
                service,
                args=["add", "--id", "test-123", "--name", "CI", "--branch", "main",
                      "--status", "completed", "--duration-seconds", "42.5"],
            )
            output = fake_out.getvalue()
            assert "test-123" in output
            assert "Added run" in output

    def test_cli_list_command_shows_duration_in_detail_format(self):
        """CLI list command should display duration_seconds"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        # Add a run with specific duration
        run_cli(
            service,
            args=["add", "--id", "test-123", "--name", "CI", "--branch", "main",
                  "--status", "completed", "--duration-seconds", "42.5"],
        )

        # List runs
        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["list"])
            output = fake_out.getvalue()
            assert "duration_seconds" in output
            assert "42.5" in output

    def test_cli_detail_command_shows_duration(self):
        """CLI detail command should display run's duration_seconds"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        run_cli(
            service,
            args=["add", "--id", "test-123", "--name", "CI", "--branch", "main",
                  "--status", "completed", "--duration-seconds", "99.9"],
        )

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["detail", "test-123"])
            output = fake_out.getvalue()
            assert "duration_seconds" in output
            assert "99.9" in output


# ============================================================================
# Interactive Menu Tests
# ============================================================================

class TestInteractiveMenuDuration:
    """Test interactive menu handling of duration_seconds"""

    def test_add_run_menu_prompts_for_duration(self):
        """Interactive _add_run should prompt for duration"""
        from src.cli.interactive_menu import _add_run

        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        inputs = [
            "TestWorkflow",  # workflow name
            "main",  # branch
            "1",  # status choice (first option)
            "0",  # no conclusion
            "",  # no run number
            "",  # no commit_sha
            "77.7",  # duration in seconds
        ]
        with patch('builtins.input', side_effect=inputs):
            _add_run(service)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 77.7

    def test_add_run_menu_defaults_duration_to_zero(self):
        """Interactive _add_run should default duration to 0 when blank"""
        from src.cli.interactive_menu import _add_run

        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        inputs = [
            "TestWorkflow",  # workflow name
            "main",  # branch
            "1",  # status choice
            "0",  # no conclusion
            "",  # no run number
            "",  # no commit_sha
            "",  # blank duration (default to 0)
        ]
        with patch('builtins.input', side_effect=inputs):
            _add_run(service)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 0.0

    def test_add_run_menu_rejects_negative_duration(self):
        """Interactive _add_run should reject negative duration and prompt again"""
        from src.cli.interactive_menu import _add_run

        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        inputs = [
            "TestWorkflow",  # workflow name
            "main",  # branch
            "1",  # status choice
            "0",  # no conclusion
            "",  # no run number
            "",  # no commit_sha
            "-10",  # negative duration (invalid)
            "20",  # valid duration on retry
        ]
        with patch('builtins.input', side_effect=inputs):
            _add_run(service)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 20.0

    def test_add_run_menu_validates_non_numeric_duration(self):
        """Interactive _add_run should validate numeric input for duration"""
        from src.cli.interactive_menu import _add_run

        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        inputs = [
            "TestWorkflow",  # workflow name
            "main",  # branch
            "1",  # status choice
            "0",  # no conclusion
            "",  # no run number
            "",  # no commit_sha
            "not_a_number",  # invalid (non-numeric)
            "45.5",  # valid on retry
        ]
        with patch('builtins.input', side_effect=inputs):
            _add_run(service)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 45.5

    def test_list_runs_menu_displays_duration(self):
        """Interactive _list_runs should display duration_seconds"""
        from src.cli.interactive_menu import _list_runs

        storage = MagicMock()
        run = WorkflowRun(
            id="r1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=67.8,
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            _list_runs(service)
            output = fake_out.getvalue()
            assert "duration_seconds" in output
            assert "67.8" in output

    def test_detail_run_menu_displays_duration(self):
        """Interactive _detail_run should display duration_seconds"""
        from src.cli.interactive_menu import _detail_run

        storage = MagicMock()
        run = WorkflowRun(
            id="r1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
            duration_seconds=88.9,
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('builtins.input', return_value="r1"):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                _detail_run(service)
                output = fake_out.getvalue()
                assert "duration_seconds" in output
                assert "88.9" in output
