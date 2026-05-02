"""
Tests for the duration_seconds feature implementation.

Covers:
- WorkflowRun.__post_init__() validation
- WorkflowRun.to_dict() serialization
- WorkflowRun.from_dict() deserialization with backward compatibility
- WorkflowRunTracker.track() with duration_seconds parameter
- CLI formatting and flag parsing
- Interactive menu prompt handling
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
from src.services.workflow_run_tracker import WorkflowRunTracker
from src.services.workflow_run_service import WorkflowRunService
from src.storage.workflow_json_storage import WorkflowJsonStorage
from src.cli.workflow_cli import build_parser, run_cli, _fmt_run
from src.cli.interactive_menu import _add_run, _fmt_run as menu_fmt_run


# ============================================================================
# TEST HELPERS
# ============================================================================

def _make_run_with_duration(
    run_id: str = "run-1",
    branch: str = "main",
    duration_seconds: float = 0.0
) -> WorkflowRun:
    """Create a test WorkflowRun with duration_seconds."""
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
        duration_seconds=duration_seconds,
    )


# ============================================================================
# WORKFLOWRUN.__post_init__() VALIDATION
# ============================================================================

class TestWorkflowRunDurationValidation:
    """Test WorkflowRun.__post_init__() duration_seconds validation."""

    def test_negative_duration_raises_value_error(self):
        """duration_seconds < 0 raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRun(
                id="r1",
                workflow_name="Test",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                conclusion=WorkflowConclusion.SUCCESS,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                run_number=None,
                commit_sha=None,
                duration_seconds=-1.0,
            )

    def test_zero_duration_allowed(self):
        """duration_seconds = 0.0 is valid."""
        run = _make_run_with_duration(duration_seconds=0.0)
        assert run.duration_seconds == 0.0

    def test_positive_duration_allowed(self):
        """duration_seconds > 0 is valid."""
        run = _make_run_with_duration(duration_seconds=123.45)
        assert run.duration_seconds == 123.45

    def test_large_duration_allowed(self):
        """Large duration values are accepted."""
        run = _make_run_with_duration(duration_seconds=999999.99)
        assert run.duration_seconds == 999999.99

    def test_small_positive_duration_allowed(self):
        """Very small positive durations are allowed."""
        run = _make_run_with_duration(duration_seconds=0.001)
        assert run.duration_seconds == 0.001

    def test_default_duration_is_zero(self):
        """Default duration_seconds is 0.0 when omitted."""
        run = WorkflowRun(
            id="r1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=None,
            commit_sha=None,
        )
        assert run.duration_seconds == 0.0


# ============================================================================
# WORKFLOWRUN SERIALIZATION TESTS
# ============================================================================

class TestWorkflowRunSerialization:
    """Test WorkflowRun.to_dict() and from_dict() with duration_seconds."""

    def test_to_dict_includes_duration_seconds(self):
        """to_dict() includes duration_seconds field."""
        run = _make_run_with_duration(duration_seconds=42.5)
        result = run.to_dict()
        assert "duration_seconds" in result
        assert result["duration_seconds"] == 42.5

    def test_to_dict_zero_duration(self):
        """to_dict() correctly serializes zero duration."""
        run = _make_run_with_duration(duration_seconds=0.0)
        result = run.to_dict()
        assert result["duration_seconds"] == 0.0

    def test_from_dict_with_duration_seconds(self):
        """from_dict() deserializes duration_seconds field."""
        data = {
            "id": "r1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            "duration_seconds": 37.8,
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 37.8

    def test_from_dict_backward_compatible_missing_duration(self):
        """from_dict() defaults to 0.0 if duration_seconds is missing (backward compat)."""
        data = {
            "id": "r1",
            "workflow_name": "CI",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 1,
            "commit_sha": "abc123",
            # duration_seconds is intentionally omitted
        }
        run = WorkflowRun.from_dict(data)
        assert run.duration_seconds == 0.0

    def test_roundtrip_serialization_with_duration(self):
        """Serialize and deserialize maintains duration_seconds value."""
        original = _make_run_with_duration(duration_seconds=99.9)
        data = original.to_dict()
        restored = WorkflowRun.from_dict(data)
        assert restored.duration_seconds == original.duration_seconds

    def test_roundtrip_serialization_all_fields_with_duration(self):
        """Full round-trip preserves all fields including duration_seconds."""
        original = _make_run_with_duration(
            run_id="test-run",
            branch="feature",
            duration_seconds=123.456
        )
        data = original.to_dict()
        restored = WorkflowRun.from_dict(data)
        assert restored.id == original.id
        assert restored.duration_seconds == original.duration_seconds
        assert restored.branch == original.branch
        assert restored.status == original.status


# ============================================================================
# STORAGE LAYER INTEGRATION TESTS
# ============================================================================

class TestStorageWithDuration:
    """Test WorkflowJsonStorage persistence with duration_seconds."""

    @pytest.fixture
    def tmp_storage(self, tmp_path):
        return WorkflowJsonStorage(str(tmp_path / "runs.json"))

    def test_save_and_load_preserves_duration(self, tmp_storage):
        """Storage round-trip preserves duration_seconds."""
        run = _make_run_with_duration(duration_seconds=55.5)
        tmp_storage.save([run])
        loaded = tmp_storage.load()
        assert loaded[0].duration_seconds == 55.5

    def test_json_file_contains_duration_field(self, tmp_storage):
        """Persisted JSON contains duration_seconds field."""
        run = _make_run_with_duration(duration_seconds=12.34)
        tmp_storage.save([run])
        raw = json.loads(Path(tmp_storage.filepath).read_text())
        assert raw[0]["duration_seconds"] == 12.34

    def test_backward_compat_load_old_json_without_duration(self, tmp_storage):
        """Can load JSON files created before duration_seconds was added."""
        # Manually write old-format JSON without duration_seconds
        old_json = [
            {
                "id": "r1",
                "workflow_name": "CI",
                "branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": None,
                "run_number": 1,
                "commit_sha": "abc123",
            }
        ]
        Path(tmp_storage.filepath).write_text(json.dumps(old_json))
        loaded = tmp_storage.load()
        assert loaded[0].duration_seconds == 0.0

    def test_multiple_runs_with_varying_durations(self, tmp_storage):
        """Storage handles multiple runs with different durations."""
        r1 = _make_run_with_duration("r1", duration_seconds=10.0)
        r2 = _make_run_with_duration("r2", duration_seconds=20.5)
        r3 = _make_run_with_duration("r3", duration_seconds=0.0)
        tmp_storage.save([r1, r2, r3])
        loaded = tmp_storage.load()
        assert len(loaded) == 3
        assert loaded[0].duration_seconds == 10.0
        assert loaded[1].duration_seconds == 20.5
        assert loaded[2].duration_seconds == 0.0


# ============================================================================
# TRACKER LAYER TESTS
# ============================================================================

class TestWorkflowRunTrackerWithDuration:
    """Test WorkflowRunTracker.track() with duration_seconds."""

    @pytest.fixture
    def service(self):
        storage = MagicMock()
        storage.load.return_value = []
        return WorkflowRunService(storage)

    def test_track_accepts_duration_seconds(self, service):
        """tracker.track() accepts duration_seconds parameter."""
        tracker = WorkflowRunTracker(service)
        run = tracker.track(
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            duration_seconds=50.5,
        )
        assert run.duration_seconds == 50.5

    def test_track_default_duration_is_zero(self, service):
        """tracker.track() defaults to 0.0 when duration_seconds omitted."""
        tracker = WorkflowRunTracker(service)
        run = tracker.track(
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
        )
        assert run.duration_seconds == 0.0

    def test_track_with_all_parameters_including_duration(self, service):
        """tracker.track() works with duration_seconds and other parameters."""
        tracker = WorkflowRunTracker(service)
        run = tracker.track(
            workflow_name="Deploy",
            branch="release",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            run_number=42,
            commit_sha="deadbeef",
            duration_seconds=123.45,
        )
        assert run.duration_seconds == 123.45
        assert run.workflow_name == "Deploy"
        assert run.branch == "release"

    def test_track_validates_negative_duration(self, service):
        """tracker.track() raises ValueError for negative duration."""
        tracker = WorkflowRunTracker(service)
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            tracker.track(
                workflow_name="CI",
                branch="main",
                status=WorkflowStatus.COMPLETED,
                duration_seconds=-5.0,
            )


# ============================================================================
# CLI TESTS
# ============================================================================

class TestCLIWithDuration:
    """Test CLI argument parsing and display of duration_seconds."""

    def test_argparse_duration_seconds_flag_exists(self):
        """CLI has --duration-seconds flag in add command."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "add",
                "--name", "CI",
                "--branch", "main",
                "--status", "completed",
                "--duration-seconds", "42.5",
            ]
        )
        assert hasattr(args, "duration_seconds")
        assert args.duration_seconds == 42.5

    def test_argparse_duration_seconds_default(self):
        """CLI --duration-seconds defaults to 0.0."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "add",
                "--name", "CI",
                "--branch", "main",
                "--status", "completed",
            ]
        )
        assert args.duration_seconds == 0.0

    def test_argparse_duration_seconds_float_type(self):
        """CLI --duration-seconds accepts float values."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "add",
                "--name", "CI",
                "--branch", "main",
                "--status", "completed",
                "--duration-seconds", "123.456",
            ]
        )
        assert isinstance(args.duration_seconds, float)
        assert args.duration_seconds == 123.456

    def test_fmt_run_displays_duration_seconds(self):
        """_fmt_run() outputs duration_seconds field."""
        run = _make_run_with_duration(duration_seconds=75.5)
        output = _fmt_run(run)
        assert "duration_seconds" in output
        assert "75.5" in output

    def test_fmt_run_displays_zero_duration(self):
        """_fmt_run() correctly displays 0.0 duration."""
        run = _make_run_with_duration(duration_seconds=0.0)
        output = _fmt_run(run)
        assert "duration_seconds" in output
        assert "0.0" in output

    def test_run_cli_add_with_duration_seconds(self):
        """run_cli() add command with --duration-seconds works."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with patch("sys.stdout", new_callable=StringIO):
            run_cli(
                service,
                [
                    "add",
                    "--name", "TestWorkflow",
                    "--branch", "main",
                    "--status", "completed",
                    "--duration-seconds", "88.8",
                ],
            )

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 88.8

    def test_run_cli_add_without_duration_seconds_defaults_to_zero(self):
        """run_cli() add command without --duration-seconds defaults to 0.0."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with patch("sys.stdout", new_callable=StringIO):
            run_cli(
                service,
                [
                    "add",
                    "--name", "TestWorkflow",
                    "--branch", "main",
                    "--status", "completed",
                ],
            )

        runs = service.list_runs()
        assert runs[0].duration_seconds == 0.0


# ============================================================================
# INTERACTIVE MENU TESTS
# ============================================================================

class TestInteractiveMenuWithDuration:
    """Test interactive menu duration_seconds handling."""

    def test_menu_fmt_run_displays_duration(self):
        """Interactive menu _fmt_run() displays duration_seconds."""
        run = _make_run_with_duration(duration_seconds=99.99)
        output = menu_fmt_run(run)
        assert "duration_seconds" in output
        assert "99.99" in output

    def test_menu_fmt_run_zero_duration(self):
        """Interactive menu _fmt_run() displays 0.0 duration."""
        run = _make_run_with_duration(duration_seconds=0.0)
        output = menu_fmt_run(run)
        assert "duration_seconds" in output
        assert "0.0" in output

    @patch("builtins.input")
    def test_add_run_with_duration_input(self, mock_input):
        """_add_run() prompts for and uses duration_seconds input."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        # Mock input sequence: name, branch, status, conclusion, run_number, commit_sha, duration
        mock_input.side_effect = [
            "CI",  # workflow name
            "main",  # branch
            "1",  # status choice
            "0",  # conclusion choice (none)
            "",  # run_number (blank)
            "",  # commit_sha (blank)
            "45.5",  # duration_seconds
        ]

        with patch("builtins.print"):  # suppress menu output
            _add_run(service)

        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0].duration_seconds == 45.5

    @patch("builtins.input")
    def test_add_run_default_duration_from_prompt(self, mock_input):
        """_add_run() uses default 0.0 if user leaves duration blank."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        mock_input.side_effect = [
            "CI",  # workflow name
            "main",  # branch
            "1",  # status
            "0",  # conclusion (none)
            "",  # run_number
            "",  # commit_sha
            "",  # duration (blank, use default)
        ]

        with patch("builtins.print"):
            _add_run(service)

        runs = service.list_runs()
        assert runs[0].duration_seconds == 0.0

    @patch("builtins.input")
    def test_add_run_duration_conversion_from_string(self, mock_input):
        """_add_run() correctly converts duration string to float."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        mock_input.side_effect = [
            "CI",
            "main",
            "1",
            "0",
            "",
            "",
            "123",  # integer input for duration
        ]

        with patch("builtins.print"):
            _add_run(service)

        runs = service.list_runs()
        assert runs[0].duration_seconds == 123.0
        assert isinstance(runs[0].duration_seconds, float)


# ============================================================================
# EDGE CASES AND INTEGRATION
# ============================================================================

class TestDurationEdgeCases:
    """Test edge cases for duration_seconds feature."""

    def test_duration_negative_zero(self):
        """Negative zero (-0.0) is treated as 0.0."""
        run = _make_run_with_duration(duration_seconds=-0.0)
        assert run.duration_seconds == 0.0

    def test_duration_with_very_large_number(self):
        """Very large duration values are accepted."""
        run = _make_run_with_duration(duration_seconds=1e10)
        assert run.duration_seconds == 1e10

    def test_duration_with_scientific_notation(self):
        """Scientific notation in CLI is parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "add",
                "--name", "CI",
                "--branch", "main",
                "--status", "completed",
                "--duration-seconds", "1.5e3",
            ]
        )
        assert args.duration_seconds == 1500.0

    def test_multiple_runs_different_durations_in_service(self):
        """Service handles multiple runs with different durations."""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        r1 = _make_run_with_duration("r1", duration_seconds=10.0)
        r2 = _make_run_with_duration("r2", duration_seconds=20.5)
        r3 = _make_run_with_duration("r3", duration_seconds=0.0)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        runs = service.list_runs()
        assert len(runs) == 3
        assert runs[0].duration_seconds == 10.0
        assert runs[1].duration_seconds == 20.5
        assert runs[2].duration_seconds == 0.0
