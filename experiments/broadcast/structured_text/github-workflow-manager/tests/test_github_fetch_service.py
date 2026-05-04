"""Tests for GitHub fetch service."""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.services.github_fetch_service import GitHubFetchService
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


@pytest.fixture
def github_service():
    """Create a GitHubFetchService instance for testing."""
    return GitHubFetchService()


class TestGitHubFetchServiceTokenResolution:
    """Tests for GitHub token resolution."""

    def test_resolve_token_direct(self, github_service):
        """Token provided directly should be used."""
        token = github_service._resolve_token("direct-token")
        assert token == "direct-token"

    def test_resolve_token_from_env_variable(self, github_service):
        """Token should be resolved from GITHUB_TOKEN env variable."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env-token"}, clear=True):
            token = github_service._resolve_token()
            assert token == "env-token"

    def test_resolve_token_from_getpass(self, github_service):
        """Token should be prompted from user via getpass."""
        with patch("src.services.github_fetch_service.getpass", return_value="user-token"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("pathlib.Path.exists", return_value=False):
                    token = github_service._resolve_token()
                    assert token == "user-token"

    def test_resolve_token_empty_getpass_raises(self, github_service):
        """Empty getpass input should raise ValueError."""
        with patch("src.services.github_fetch_service.getpass", return_value=""):
            with patch.dict(os.environ, {}, clear=True):
                with patch("pathlib.Path.exists", return_value=False):
                    with pytest.raises(ValueError, match="No GitHub token provided"):
                        github_service._resolve_token()


class TestGitHubFetchServiceEnvFileReading:
    """Tests for reading .env files."""

    def test_read_env_file_success(self, github_service):
        """Successfully read token from .env file."""
        env_content = "GITHUB_TOKEN=test-token\n"
        with patch("builtins.open") as mock_file:
            mock_file.return_value.__enter__.return_value = env_content.split("\n")
            token = github_service._read_env_file(Path(".env"))
            assert token == "test-token"

    def test_read_env_file_with_quotes(self, github_service):
        """Read token from .env file with quotes."""
        env_content = 'GITHUB_TOKEN="quoted-token"\n'
        with patch("builtins.open") as mock_file:
            mock_file.return_value.__enter__.return_value = env_content.split("\n")
            token = github_service._read_env_file(Path(".env"))
            assert token == "quoted-token"

    def test_read_env_file_not_found(self, github_service):
        """Return None if .env file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            token = github_service._read_env_file(Path(".env"))
            assert token is None

    def test_read_env_file_without_token(self, github_service):
        """Return None if token not found in file."""
        env_content = "OTHER_VAR=value\n"
        with patch("builtins.open") as mock_file:
            mock_file.return_value.__enter__.return_value = env_content.split("\n")
            token = github_service._read_env_file(Path(".env"))
            assert token is None


class TestGitHubFetchServiceTokenValidation:
    """Tests for token validation."""

    def test_validate_token_success(self, github_service):
        """Valid token should return True."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = github_service.validate_token("valid-token")
            assert result is True

    def test_validate_token_invalid(self, github_service):
        """Invalid token should return False."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = github_service.validate_token("invalid-token")
            assert result is False

    def test_validate_token_exception_returns_false(self, github_service):
        """Exception during validation should return False."""
        with patch("subprocess.run", side_effect=Exception("Error")):
            result = github_service.validate_token("token")
            assert result is False


class TestGitHubFetchServiceStatusMapping:
    """Tests for status mapping."""

    def test_map_github_status_queued(self, github_service):
        """queued should map to QUEUED."""
        assert github_service._map_github_status("queued") == WorkflowStatus.QUEUED

    def test_map_github_status_in_progress(self, github_service):
        """in_progress should map to IN_PROGRESS."""
        assert github_service._map_github_status("in_progress") == WorkflowStatus.IN_PROGRESS

    def test_map_github_status_completed(self, github_service):
        """completed should map to COMPLETED."""
        assert github_service._map_github_status("completed") == WorkflowStatus.COMPLETED

    def test_map_github_status_unknown_raises(self, github_service):
        """Unknown status should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown GitHub status"):
            github_service._map_github_status("unknown")


class TestGitHubFetchServiceConclusionMapping:
    """Tests for conclusion mapping."""

    def test_map_github_conclusion_success(self, github_service):
        """success should map to SUCCESS."""
        assert github_service._map_github_conclusion("success") == WorkflowConclusion.SUCCESS

    def test_map_github_conclusion_failure(self, github_service):
        """failure should map to FAILURE."""
        assert github_service._map_github_conclusion("failure") == WorkflowConclusion.FAILURE

    def test_map_github_conclusion_cancelled(self, github_service):
        """cancelled should map to CANCELLED."""
        assert github_service._map_github_conclusion("cancelled") == WorkflowConclusion.CANCELLED

    def test_map_github_conclusion_unknown_raises(self, github_service):
        """Unknown conclusion should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown GitHub conclusion"):
            github_service._map_github_conclusion("unknown")


class TestGitHubFetchServiceTimestampParsing:
    """Tests for timestamp parsing."""

    def test_parse_timestamp_z_suffix(self, github_service):
        """Parse ISO timestamp with Z suffix."""
        ts = github_service._parse_timestamp("2026-05-03T10:00:00Z")
        assert ts.year == 2026
        assert ts.month == 5
        assert ts.day == 3

    def test_parse_timestamp_with_timezone(self, github_service):
        """Parse ISO timestamp with timezone offset."""
        ts = github_service._parse_timestamp("2026-05-03T10:00:00+00:00")
        assert ts.year == 2026

    def test_parse_timestamp_invalid_raises(self, github_service):
        """Invalid timestamp should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            github_service._parse_timestamp("invalid")


class TestGitHubFetchServiceRunConversion:
    """Tests for GitHub run object conversion."""

    def test_convert_github_run_minimal(self, github_service):
        """Convert minimal GitHub run object."""
        gh_run = {
            "id": 123,
            "name": "CI",
            "headBranch": "main",
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-05-03T10:00:00Z",
            "updatedAt": "2026-05-03T10:05:00Z",
        }
        run = github_service._convert_github_run(gh_run)
        assert run.id == "123"
        assert run.workflow_name == "CI"
        assert run.branch == "main"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS

    def test_convert_github_run_with_optional_fields(self, github_service):
        """Convert GitHub run with optional fields."""
        gh_run = {
            "id": 456,
            "name": "Test",
            "headBranch": "develop",
            "status": "in_progress",
            "conclusion": None,
            "createdAt": "2026-05-03T10:00:00Z",
            "updatedAt": "2026-05-03T10:05:00Z",
            "number": 42,
            "headSha": "abc123",
        }
        run = github_service._convert_github_run(gh_run)
        assert run.run_number == 42
        assert run.commit_sha == "abc123"
        assert run.conclusion is None

    def test_convert_github_run_invalid_status(self, github_service):
        """Invalid status should raise ValueError."""
        gh_run = {
            "id": 999,
            "name": "CI",
            "headBranch": "main",
            "status": "invalid_status",
            "createdAt": "2026-05-03T10:00:00Z",
            "updatedAt": "2026-05-03T10:05:00Z",
        }
        with pytest.raises(ValueError, match="Unknown GitHub status"):
            github_service._convert_github_run(gh_run)


class TestGitHubFetchServiceFetchWorkflowRuns:
    """Tests for fetching workflow runs."""

    def test_fetch_workflow_runs_success(self, github_service):
        """Successfully fetch workflow runs from GitHub."""
        runs_data = [
            {
                "id": 111,
                "name": "CI",
                "headBranch": "main",
                "status": "completed",
                "conclusion": "success",
                "createdAt": "2026-05-03T10:00:00Z",
                "updatedAt": "2026-05-03T10:05:00Z",
                "number": 1,
                "headSha": "abc123",
            }
        ]

        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 0

            fetch_result = MagicMock()
            fetch_result.returncode = 0
            fetch_result.stdout = json.dumps(runs_data)

            mock_run.side_effect = [auth_result, fetch_result]

            with patch("src.services.github_fetch_service.getpass", return_value="token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        runs = github_service.fetch_workflow_runs("owner", "repo")

            assert len(runs) == 1
            assert runs[0].id == "111"
            assert runs[0].workflow_name == "CI"

    def test_fetch_workflow_runs_with_workflow_id(self, github_service):
        """Fetch with specific workflow ID."""
        runs_data = []

        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 0

            fetch_result = MagicMock()
            fetch_result.returncode = 0
            fetch_result.stdout = json.dumps(runs_data)

            mock_run.side_effect = [auth_result, fetch_result]

            with patch("src.services.github_fetch_service.getpass", return_value="token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        runs = github_service.fetch_workflow_runs("owner", "repo", workflow_id="123")

            call_args = mock_run.call_args_list[1][0][0]
            assert "--workflow" in call_args
            assert "123" in call_args

    def test_fetch_workflow_runs_invalid_token(self, github_service):
        """Invalid token should raise ValueError."""
        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 1
            mock_run.return_value = auth_result

            with patch("src.services.github_fetch_service.getpass", return_value="bad-token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        with pytest.raises(ValueError, match="Invalid or expired GitHub token"):
                            github_service.fetch_workflow_runs("owner", "repo")

    def test_fetch_workflow_runs_api_error(self, github_service):
        """API error should raise ValueError."""
        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 0

            fetch_result = MagicMock()
            fetch_result.returncode = 1
            fetch_result.stderr = "Repository not found"

            mock_run.side_effect = [auth_result, fetch_result]

            with patch("src.services.github_fetch_service.getpass", return_value="token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        with pytest.raises(ValueError, match="Failed to fetch runs"):
                            github_service.fetch_workflow_runs("owner", "repo")

    def test_fetch_workflow_runs_invalid_json(self, github_service):
        """Invalid JSON response should raise ValueError."""
        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 0

            fetch_result = MagicMock()
            fetch_result.returncode = 0
            fetch_result.stdout = "invalid json"

            mock_run.side_effect = [auth_result, fetch_result]

            with patch("src.services.github_fetch_service.getpass", return_value="token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        with pytest.raises(ValueError, match="Failed to parse GitHub API response"):
                            github_service.fetch_workflow_runs("owner", "repo")

    def test_fetch_workflow_runs_multiple_runs(self, github_service):
        """Fetch multiple runs successfully."""
        runs_data = [
            {
                "id": i + 100,  # Start from 100 to avoid id=0
                "name": f"Run{i}",
                "headBranch": "main",
                "status": "completed",
                "conclusion": "success",
                "createdAt": "2026-05-03T10:00:00Z",
                "updatedAt": "2026-05-03T10:05:00Z",
            }
            for i in range(5)
        ]

        with patch("subprocess.run") as mock_run:
            auth_result = MagicMock()
            auth_result.returncode = 0

            fetch_result = MagicMock()
            fetch_result.returncode = 0
            fetch_result.stdout = json.dumps(runs_data)

            mock_run.side_effect = [auth_result, fetch_result]

            with patch("src.services.github_fetch_service.getpass", return_value="token"):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.exists", return_value=False):
                        runs = github_service.fetch_workflow_runs("owner", "repo")

            assert len(runs) == 5
