"""
Tests for CLI status command and interactive menu status option.

Covers:
- CLI status command parsing and execution
- Interactive menu status option
- Status report formatting
- Error handling for nonexistent runs
"""

import pytest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import MagicMock, patch

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.cli.workflow_cli import run_cli, build_parser
from src.cli.interactive_menu import _check_run_status


def _make_run(
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Helper to create WorkflowRun instances."""
    return WorkflowRun(
        id=run_id,
        workflow_name="TestWorkflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )


# ============================================================================
# CLI Status Command Tests
# ============================================================================

class TestCLIStatusCommand:
    """Test the status command in CLI"""

    def test_status_command_parser_exists(self):
        """Parser should have status command"""
        parser = build_parser()
        # Should not raise an error
        args = parser.parse_args(["status", "--id", "run-1"])
        assert args.command == "status"
        assert args.run_id == "run-1"

    def test_status_command_requires_id_argument(self):
        """Status command should require --id argument"""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["status"])

    def test_status_command_id_is_required(self):
        """--id argument should be required for status command"""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["status", "run-1"])  # positional instead of --id

    def test_cli_status_command_successful_run(self):
        """CLI status command should display correct results for successful run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-1",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["status", "--id", "run-1"])
            output = fake_out.getvalue()
            assert "Run Status Report for run-1" in output
            assert "is_terminal: True" in output
            assert "is_running: False" in output
            assert "is_successful: True" in output
            assert "is_failed: False" in output
            assert "is_cancelled: False" in output

    def test_cli_status_command_failed_run(self):
        """CLI status command should display correct results for failed run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-2",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["status", "--id", "run-2"])
            output = fake_out.getvalue()
            assert "Run Status Report for run-2" in output
            assert "is_terminal: True" in output
            assert "is_running: False" in output
            assert "is_successful: False" in output
            assert "is_failed: True" in output
            assert "is_cancelled: False" in output

    def test_cli_status_command_running_run(self):
        """CLI status command should display correct results for running run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-3",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["status", "--id", "run-3"])
            output = fake_out.getvalue()
            assert "Run Status Report for run-3" in output
            assert "is_terminal: False" in output
            assert "is_running: True" in output
            assert "is_successful: False" in output
            assert "is_failed: False" in output
            assert "is_cancelled: False" in output

    def test_cli_status_command_cancelled_run(self):
        """CLI status command should display correct results for cancelled run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-4",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["status", "--id", "run-4"])
            output = fake_out.getvalue()
            assert "Run Status Report for run-4" in output
            assert "is_terminal: True" in output
            assert "is_running: False" in output
            assert "is_successful: False" in output
            assert "is_failed: False" in output
            assert "is_cancelled: True" in output

    def test_cli_status_command_nonexistent_run(self):
        """CLI status command should error for nonexistent run"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.stderr', new=StringIO()):
                run_cli(service, args=["status", "--id", "nonexistent"])
        assert exc_info.value.code == 1

    def test_cli_status_command_nonexistent_run_error_message(self):
        """CLI status command should display error message for nonexistent run"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with pytest.raises(SystemExit):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                run_cli(service, args=["status", "--id", "nonexistent"])
                error = fake_err.getvalue()
                assert "No run found" in error
                assert "nonexistent" in error

    @pytest.mark.parametrize("status,conclusion,terminal,running,successful,failed,cancelled", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS, True, False, True, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED, True, False, False, False, True),
        (WorkflowStatus.IN_PROGRESS, None, False, True, False, False, False),
        (WorkflowStatus.QUEUED, None, False, False, False, False, False),
    ])
    def test_cli_status_command_all_combinations(
        self,
        status,
        conclusion,
        terminal,
        running,
        successful,
        failed,
        cancelled
    ):
        """CLI status command should correctly report all status/conclusion combinations"""
        storage = MagicMock()
        run = _make_run(run_id="test-run", status=status, conclusion=conclusion)
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            run_cli(service, args=["status", "--id", "test-run"])
            output = fake_out.getvalue()
            assert f"is_terminal: {terminal}" in output
            assert f"is_running: {running}" in output
            assert f"is_successful: {successful}" in output
            assert f"is_failed: {failed}" in output
            assert f"is_cancelled: {cancelled}" in output


# ============================================================================
# Interactive Menu Status Option Tests
# ============================================================================

class TestInteractiveMenuStatus:
    """Test the status option in interactive menu"""

    def test_check_run_status_successful(self):
        """_check_run_status should display status for successful run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-1",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('builtins.input', return_value="run-1"):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                _check_run_status(service)
                output = fake_out.getvalue()
                assert "Run Status Report for run-1" in output
                assert "is_terminal: True" in output
                assert "is_successful: True" in output
                assert "is_failed: False" in output

    def test_check_run_status_failed(self):
        """_check_run_status should display status for failed run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-2",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('builtins.input', return_value="run-2"):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                _check_run_status(service)
                output = fake_out.getvalue()
                assert "Run Status Report for run-2" in output
                assert "is_terminal: True" in output
                assert "is_failed: True" in output
                assert "is_successful: False" in output

    def test_check_run_status_running(self):
        """_check_run_status should display status for running run"""
        storage = MagicMock()
        run = _make_run(
            run_id="run-3",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None
        )
        storage.load.return_value = [run]
        service = WorkflowRunService(storage)

        with patch('builtins.input', return_value="run-3"):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                _check_run_status(service)
                output = fake_out.getvalue()
                assert "Run Status Report for run-3" in output
                assert "is_terminal: False" in output
                assert "is_running: True" in output

    def test_check_run_status_nonexistent(self):
        """_check_run_status should handle nonexistent run"""
        storage = MagicMock()
        storage.load.return_value = []
        service = WorkflowRunService(storage)

        with patch('builtins.input', return_value="nonexistent"):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                _check_run_status(service)
                output = fake_out.getvalue()
                assert "No run found" in output
                assert "nonexistent" in output

    def test_check_run_status_all_statuses(self):
        """_check_run_status should work for all status values"""
        statuses = [
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.IN_PROGRESS, None),
            (WorkflowStatus.QUEUED, None),
            (WorkflowStatus.WAITING, None),
        ]
        for status, conclusion in statuses:
            storage = MagicMock()
            run = _make_run(run_id="test-run", status=status, conclusion=conclusion)
            storage.load.return_value = [run]
            service = WorkflowRunService(storage)

            with patch('builtins.input', return_value="test-run"):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    _check_run_status(service)
                    output = fake_out.getvalue()
                    assert "Run Status Report for test-run" in output
                    # Verify all five methods are shown
                    assert "is_terminal:" in output
                    assert "is_running:" in output
                    assert "is_successful:" in output
                    assert "is_failed:" in output
                    assert "is_cancelled:" in output
