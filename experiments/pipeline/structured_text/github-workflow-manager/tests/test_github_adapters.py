"""
Comprehensive tests for GitHub adapters.

Tests cover:
- GitHubTokenResolver: env var, secrets file, prompt; validation with API and CLI modes
- GitHubApiClient: successful fetch_runs, fetch_run_attempts; error handling; timestamp parsing
- GitHubCliAdapter: successful fetch_runs, fetch_run_attempts; JSON parsing; command execution
- GitHubToWorkflowConverter: convert_run, convert_attempt with various API formats; enum validation
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, mock_open, MagicMock
import subprocess

from src.adapters.github.token_resolver import GitHubTokenResolver
from src.adapters.github.api_client import GitHubApiClient
from src.adapters.github.cli_adapter import GitHubCliAdapter
from src.adapters.github.converter import GitHubToWorkflowConverter
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


# ============================================================================
# GitHubTokenResolver Tests
# ============================================================================

class TestGitHubTokenResolverEnvironment:
    """Tests for GitHubTokenResolver environment variable resolution."""

    def test_resolve_from_env_var(self):
        """Token should be resolved from GITHUB_TOKEN environment variable."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token-123"}):
            resolver = GitHubTokenResolver()
            token = resolver.resolve()
            assert token == "test-token-123"

    def test_resolve_prefers_env_var_over_secrets_file(self):
        """Environment variable should take priority over secrets file."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"}):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="GITHUB_TOKEN=file-token")):
                    resolver = GitHubTokenResolver()
                    token = resolver.resolve()
                    assert token == "env-token"

    def test_resolve_from_secrets_file(self):
        """Token should be resolved from secrets/.env file."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                secrets_content = "GITHUB_TOKEN=secret-token-456\n"
                with patch("builtins.open", mock_open(read_data=secrets_content)):
                    resolver = GitHubTokenResolver()
                    token = resolver.resolve()
                    assert token == "secret-token-456"

    def test_resolve_from_secrets_file_with_whitespace(self):
        """Token should be resolved and whitespace stripped from secrets file."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                secrets_content = "GITHUB_TOKEN=  secret-token-with-spaces  \n"
                with patch("builtins.open", mock_open(read_data=secrets_content)):
                    resolver = GitHubTokenResolver()
                    token = resolver.resolve()
                    assert token == "secret-token-with-spaces"

    def test_resolve_from_prompt_when_no_env_or_file(self):
        """Token should be resolved from user prompt if env var and file missing."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", return_value="prompt-token-789"):
                    resolver = GitHubTokenResolver()
                    token = resolver.resolve()
                    assert token == "prompt-token-789"

    def test_resolve_fails_on_empty_prompt_input(self):
        """resolve() should raise RuntimeError if user provides empty input via prompt."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", return_value=""):
                    resolver = GitHubTokenResolver()
                    with pytest.raises(RuntimeError, match="No token provided"):
                        resolver.resolve()

    def test_resolve_fails_on_keyboard_interrupt(self):
        """resolve() should raise RuntimeError if user cancels via Ctrl+C."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", side_effect=KeyboardInterrupt()):
                    resolver = GitHubTokenResolver()
                    with pytest.raises(RuntimeError, match="Token input cancelled by user"):
                        resolver.resolve()

    def test_resolve_ignores_secrets_file_read_error(self):
        """resolve() should fall back to prompt if secrets file cannot be read."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=IOError("Permission denied")):
                    with patch("builtins.input", return_value="fallback-token"):
                        resolver = GitHubTokenResolver()
                        token = resolver.resolve()
                        assert token == "fallback-token"

    def test_resolve_handles_secrets_file_without_github_token(self):
        """resolve() should fall back to prompt if secrets file has no GITHUB_TOKEN line."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                secrets_content = "OTHER_VAR=value\nANOTHER_VAR=another\n"
                with patch("builtins.open", mock_open(read_data=secrets_content)):
                    with patch("builtins.input", return_value="prompt-token"):
                        resolver = GitHubTokenResolver()
                        token = resolver.resolve()
                        assert token == "prompt-token"


class TestGitHubTokenResolverValidation:
    """Tests for GitHubTokenResolver validation with API and CLI modes."""

    def test_validate_with_api_success(self):
        """validate() should return True for valid token via API."""
        resolver = GitHubTokenResolver()
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = resolver.validate("test-token", fetch_mode="api")
            assert result is True
            mock_get.assert_called_once()

    def test_validate_with_api_unauthorized(self):
        """validate() should return False for invalid token via API (401)."""
        resolver = GitHubTokenResolver()
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = resolver.validate("bad-token", fetch_mode="api")
            assert result is False

    def test_validate_with_api_other_error(self):
        """validate() should return False for non-200, non-401 API responses."""
        resolver = GitHubTokenResolver()
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            result = resolver.validate("test-token", fetch_mode="api")
            assert result is False

    def test_validate_with_api_request_exception(self):
        """validate() should return False if API request fails."""
        resolver = GitHubTokenResolver()
        with patch("requests.get", side_effect=Exception("Connection refused")):
            result = resolver.validate("test-token", fetch_mode="api")
            assert result is False

    def test_validate_with_cli_success(self):
        """validate() should return True for successful gh CLI status check."""
        resolver = GitHubTokenResolver()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = resolver.validate("test-token", fetch_mode="cli")
            assert result is True
            mock_run.assert_called_once()

    def test_validate_with_cli_failure(self):
        """validate() should return False for failed gh CLI status check."""
        resolver = GitHubTokenResolver()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = resolver.validate("test-token", fetch_mode="cli")
            assert result is False

    def test_validate_with_cli_timeout(self):
        """validate() should return False if gh CLI times out."""
        resolver = GitHubTokenResolver()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 5)):
            result = resolver.validate("test-token", fetch_mode="cli")
            assert result is False

    def test_validate_with_cli_not_found(self):
        """validate() should return False if gh CLI is not installed."""
        resolver = GitHubTokenResolver()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = resolver.validate("test-token", fetch_mode="cli")
            assert result is False

    def test_validate_defaults_to_api_mode(self):
        """validate() should default to API mode if fetch_mode not specified."""
        resolver = GitHubTokenResolver()
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = resolver.validate("test-token")
            assert result is True
            # Verify API was called, not CLI
            mock_get.assert_called_once()


# ============================================================================
# GitHubApiClient Tests
# ============================================================================

class TestGitHubApiClientGetRuns:
    """Tests for GitHubApiClient.get_runs() method."""

    def test_get_runs_success(self):
        """get_runs() should return list of runs from API."""
        client = GitHubApiClient("test-token")
        mock_runs = [
            {
                "id": 1,
                "name": "Test Workflow",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": mock_runs}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.get_runs("owner", "repo")
            assert result == mock_runs

    def test_get_runs_respects_limit(self):
        """get_runs() should limit results to specified count."""
        client = GitHubApiClient("test-token")
        mock_runs = [{"id": i} for i in range(100)]
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": mock_runs}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.get_runs("owner", "repo", limit=10)
            assert len(result) == 10
            assert result == mock_runs[:10]

    def test_get_runs_caps_limit_at_100(self):
        """get_runs() should cap per_page at 100."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client.get_runs("owner", "repo", limit=200)

            # Check the per_page parameter was capped
            call_args = mock_get.call_args
            assert call_args[1]["params"]["per_page"] == 100

    def test_get_runs_constructs_correct_url(self):
        """get_runs() should construct correct GitHub API URL."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client.get_runs("myowner", "myrepo")

            call_args = mock_get.call_args
            assert call_args[0][0] == "https://api.github.com/repos/myowner/myrepo/actions/runs"

    def test_get_runs_includes_auth_header(self):
        """get_runs() should include Authorization header with token."""
        client = GitHubApiClient("my-secret-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client.get_runs("owner", "repo")

            call_args = mock_get.call_args
            assert call_args[1]["headers"]["Authorization"] == "token my-secret-token"

    def test_get_runs_request_exception(self):
        """get_runs() should raise RuntimeError on request failure."""
        import requests
        client = GitHubApiClient("test-token")
        with patch("requests.get", side_effect=requests.RequestException("Network error")):
            with pytest.raises(RuntimeError, match="Failed to fetch runs from GitHub API"):
                client.get_runs("owner", "repo")

    def test_get_runs_invalid_json(self):
        """get_runs() should raise RuntimeError on invalid JSON response."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="Invalid JSON response"):
                client.get_runs("owner", "repo")

    def test_get_runs_empty_response(self):
        """get_runs() should handle empty workflow_runs list."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.get_runs("owner", "repo")
            assert result == []


class TestGitHubApiClientGetRunAttempts:
    """Tests for GitHubApiClient.get_run_attempts() method."""

    def test_get_run_attempts_success(self):
        """get_run_attempts() should return list of attempts from API."""
        client = GitHubApiClient("test-token")
        mock_attempts = [
            {
                "id": 100,
                "attempt_number": 1,
                "status": "completed",
                "conclusion": "success",
            }
        ]
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": mock_attempts}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.get_run_attempts("owner", "repo", "run-123")
            assert result == mock_attempts

    def test_get_run_attempts_constructs_correct_url(self):
        """get_run_attempts() should construct correct GitHub API URL."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client.get_run_attempts("myowner", "myrepo", "run-xyz")

            call_args = mock_get.call_args
            expected_url = "https://api.github.com/repos/myowner/myrepo/actions/runs/run-xyz/attempts"
            assert call_args[0][0] == expected_url

    def test_get_run_attempts_includes_auth_header(self):
        """get_run_attempts() should include Authorization header with token."""
        client = GitHubApiClient("my-secret-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"workflow_runs": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client.get_run_attempts("owner", "repo", "run-123")

            call_args = mock_get.call_args
            assert call_args[1]["headers"]["Authorization"] == "token my-secret-token"

    def test_get_run_attempts_request_exception(self):
        """get_run_attempts() should raise RuntimeError on request failure."""
        import requests
        client = GitHubApiClient("test-token")
        with patch("requests.get", side_effect=requests.RequestException("Network error")):
            with pytest.raises(RuntimeError, match="Failed to fetch attempts from GitHub API"):
                client.get_run_attempts("owner", "repo", "run-123")

    def test_get_run_attempts_invalid_json(self):
        """get_run_attempts() should raise RuntimeError on invalid JSON."""
        client = GitHubApiClient("test-token")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="Invalid JSON response"):
                client.get_run_attempts("owner", "repo", "run-123")


# ============================================================================
# GitHubCliAdapter Tests
# ============================================================================

class TestGitHubCliAdapterGetRuns:
    """Tests for GitHubCliAdapter.get_runs() method."""

    def test_get_runs_success(self):
        """get_runs() should execute gh CLI and return parsed JSON."""
        adapter = GitHubCliAdapter()
        mock_output = json.dumps([
            {"id": 1, "name": "Test Workflow", "status": "completed"}
        ])
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            result = adapter.get_runs("owner", "repo")
            assert result == [{"id": 1, "name": "Test Workflow", "status": "completed"}]

    def test_get_runs_constructs_correct_command(self):
        """get_runs() should construct correct gh CLI command."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "[]"
            mock_run.return_value = mock_result

            adapter.get_runs("owner", "repo", limit=50)

            call_args = mock_run.call_args
            args = call_args[0][0]
            assert args[0] == "gh"
            assert args[1] == "run"
            assert args[2] == "list"
            assert "-R" in args
            assert "owner/repo" in args
            assert "-L" in args
            assert "50" in args
            assert "--json" in args

    def test_get_runs_respects_limit(self):
        """get_runs() should pass limit to gh CLI."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "[]"
            mock_run.return_value = mock_result

            adapter.get_runs("owner", "repo", limit=20)

            call_args = mock_run.call_args
            args = call_args[0][0]
            limit_index = args.index("-L")
            assert args[limit_index + 1] == "20"

    def test_get_runs_command_timeout(self):
        """get_runs() should raise RuntimeError on command timeout."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
            with pytest.raises(RuntimeError, match="gh CLI command timed out"):
                adapter.get_runs("owner", "repo")

    def test_get_runs_command_not_found(self):
        """get_runs() should raise RuntimeError if gh CLI not installed."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError, match="gh CLI not found in PATH"):
                adapter.get_runs("owner", "repo")

    def test_get_runs_command_failure(self):
        """get_runs() should raise RuntimeError if command fails."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Error: repository not found"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="gh CLI failed"):
                adapter.get_runs("owner", "repo")

    def test_get_runs_invalid_json(self):
        """get_runs() should raise RuntimeError on invalid JSON output."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "invalid json output"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="Invalid JSON output from gh CLI"):
                adapter.get_runs("owner", "repo")


class TestGitHubCliAdapterGetRunAttempts:
    """Tests for GitHubCliAdapter.get_run_attempts() method."""

    def test_get_run_attempts_success(self):
        """get_run_attempts() should execute gh CLI and return parsed attempts."""
        adapter = GitHubCliAdapter()
        mock_output = json.dumps({
            "attempts": [
                {"attemptNumber": 1, "status": "completed", "conclusion": "success"}
            ]
        })
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            result = adapter.get_run_attempts("owner", "repo", "run-123")
            assert result == [{"attemptNumber": 1, "status": "completed", "conclusion": "success"}]

    def test_get_run_attempts_constructs_correct_command(self):
        """get_run_attempts() should construct correct gh CLI command."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '{"attempts": []}'
            mock_run.return_value = mock_result

            adapter.get_run_attempts("owner", "repo", "run-xyz")

            call_args = mock_run.call_args
            args = call_args[0][0]
            assert args[0] == "gh"
            assert args[1] == "run"
            assert args[2] == "view"
            assert "run-xyz" in args
            assert "-R" in args
            assert "owner/repo" in args

    def test_get_run_attempts_missing_attempts_key(self):
        """get_run_attempts() should raise RuntimeError if 'attempts' key missing."""
        adapter = GitHubCliAdapter()
        mock_output = json.dumps({"status": "completed"})
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="missing 'attempts' key"):
                adapter.get_run_attempts("owner", "repo", "run-123")

    def test_get_run_attempts_invalid_json(self):
        """get_run_attempts() should raise RuntimeError on invalid JSON."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "not valid json"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="Invalid JSON output from gh CLI"):
                adapter.get_run_attempts("owner", "repo", "run-123")

    def test_get_run_attempts_command_timeout(self):
        """get_run_attempts() should raise RuntimeError on timeout."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
            with pytest.raises(RuntimeError, match="gh CLI command timed out"):
                adapter.get_run_attempts("owner", "repo", "run-123")

    def test_get_run_attempts_command_not_found(self):
        """get_run_attempts() should raise RuntimeError if gh CLI not found."""
        adapter = GitHubCliAdapter()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError, match="gh CLI not found in PATH"):
                adapter.get_run_attempts("owner", "repo", "run-123")


# ============================================================================
# GitHubToWorkflowConverter Tests
# ============================================================================

class TestGitHubToWorkflowConverterConvertRun:
    """Tests for GitHubToWorkflowConverter.convert_run() method."""

    def test_convert_run_basic_api_format(self):
        """convert_run() should convert basic API response to WorkflowRun."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 123,
            "name": "Test Workflow",
            "headBranch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z",
            "runNumber": 1,
            "headSha": "abc123",
        }

        run = converter.convert_run(api_data)

        assert run.id == "123"
        assert run.workflow_name == "Test Workflow"
        assert run.branch == "main"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS
        assert run.run_number == 1
        assert run.commit_sha == "abc123"

    def test_convert_run_snake_case_field_names(self):
        """convert_run() should handle snake_case field names."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 456,
            "name": "Snake Case Workflow",
            "head_branch": "develop",
            "status": "in_progress",
            "created_at": "2024-01-01T10:00:00Z",
            "head_sha": "def456",
        }

        run = converter.convert_run(api_data)

        assert run.branch == "develop"
        assert run.commit_sha == "def456"

    def test_convert_run_missing_created_at(self):
        """convert_run() should raise ValueError if createdAt missing."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 789,
            "name": "No Timestamp",
            "status": "completed",
        }

        with pytest.raises(ValueError, match="Missing createdAt field"):
            converter.convert_run(api_data)

    def test_convert_run_missing_status(self):
        """convert_run() should raise ValueError if status missing."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 789,
            "name": "No Status",
            "created_at": "2024-01-01T00:00:00Z",
        }

        with pytest.raises(ValueError, match="Missing status field"):
            converter.convert_run(api_data)

    def test_convert_run_invalid_status(self):
        """convert_run() should raise ValueError for invalid status."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 789,
            "name": "Bad Status",
            "status": "invalid_status",
            "created_at": "2024-01-01T00:00:00Z",
        }

        with pytest.raises(ValueError, match="Invalid status value"):
            converter.convert_run(api_data)

    def test_convert_run_invalid_conclusion(self):
        """convert_run() should log warning for invalid conclusion but continue."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 789,
            "name": "Bad Conclusion",
            "status": "completed",
            "conclusion": "invalid_conclusion",
            "created_at": "2024-01-01T00:00:00Z",
        }

        run = converter.convert_run(api_data)

        # Invalid conclusion should result in None but conversion succeeds
        assert run.conclusion is None

    def test_convert_run_calculates_duration(self):
        """convert_run() should calculate duration from timestamps."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 999,
            "name": "Duration Test",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:10:00Z",
        }

        run = converter.convert_run(api_data)

        # 10 minutes = 600 seconds
        assert run.duration_seconds == 600.0

    def test_convert_run_no_updated_at(self):
        """convert_run() should handle missing updated_at timestamp."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 111,
            "name": "No Update Time",
            "status": "in_progress",
            "created_at": "2024-01-01T00:00:00Z",
        }

        run = converter.convert_run(api_data)

        assert run.updated_at is None
        assert run.duration_seconds == 0.0

    def test_convert_run_no_conclusion(self):
        """convert_run() should handle missing conclusion."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 222,
            "name": "No Conclusion",
            "status": "in_progress",
            "created_at": "2024-01-01T00:00:00Z",
        }

        run = converter.convert_run(api_data)

        assert run.conclusion is None

    @pytest.mark.parametrize("status_val", [
        "queued", "in_progress", "completed", "waiting", "requested", "pending"
    ])
    def test_convert_run_all_valid_statuses(self, status_val):
        """convert_run() should accept all valid status values."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 333,
            "name": "Status Test",
            "status": status_val,
            "created_at": "2024-01-01T00:00:00Z",
        }

        run = converter.convert_run(api_data)
        assert run.status == WorkflowStatus(status_val)

    @pytest.mark.parametrize("conclusion_val", [
        "success", "failure", "cancelled", "skipped", "timed_out", "action_required", "neutral", "stale"
    ])
    def test_convert_run_all_valid_conclusions(self, conclusion_val):
        """convert_run() should accept all valid conclusion values."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 444,
            "name": "Conclusion Test",
            "status": "completed",
            "conclusion": conclusion_val,
            "created_at": "2024-01-01T00:00:00Z",
        }

        run = converter.convert_run(api_data)
        assert run.conclusion == WorkflowConclusion(conclusion_val)


class TestGitHubToWorkflowConverterConvertAttempt:
    """Tests for GitHubToWorkflowConverter.convert_attempt() method."""

    def test_convert_attempt_basic_api_format(self):
        """convert_attempt() should convert basic API response to WorkflowRunAttempt."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 100,
            "attemptNumber": 1,
            "status": "completed",
            "conclusion": "success",
            "startedAt": "2024-01-01T00:00:00Z",
            "completedAt": "2024-01-01T00:05:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-123")

        assert attempt.id == "100"
        assert attempt.run_id == "run-123"
        assert attempt.attempt_number == 1
        assert attempt.status == WorkflowStatus.COMPLETED
        assert attempt.conclusion == WorkflowConclusion.SUCCESS

    def test_convert_attempt_snake_case_field_names(self):
        """convert_attempt() should handle snake_case field names."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 200,
            "attempt_number": 2,
            "status": "in_progress",
            "started_at": "2024-01-01T10:00:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-456")

        assert attempt.attempt_number == 2

    def test_convert_attempt_missing_started_at(self):
        """convert_attempt() should raise ValueError if startedAt missing."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 300,
            "status": "completed",
        }

        with pytest.raises(ValueError, match="Missing startedAt field"):
            converter.convert_attempt(api_data, "run-789")

    def test_convert_attempt_missing_status(self):
        """convert_attempt() should raise ValueError if status missing."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 300,
            "started_at": "2024-01-01T00:00:00Z",
        }

        with pytest.raises(ValueError, match="Missing status field"):
            converter.convert_attempt(api_data, "run-789")

    def test_convert_attempt_invalid_status(self):
        """convert_attempt() should raise ValueError for invalid status."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 300,
            "status": "not_a_valid_status",
            "started_at": "2024-01-01T00:00:00Z",
        }

        with pytest.raises(ValueError, match="Invalid status value"):
            converter.convert_attempt(api_data, "run-789")

    def test_convert_attempt_calculates_duration(self):
        """convert_attempt() should calculate duration from timestamps."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 400,
            "status": "completed",
            "started_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:15:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-999")

        # 15 minutes = 900 seconds
        assert attempt.duration_seconds == 900.0

    def test_convert_attempt_no_completed_at(self):
        """convert_attempt() should handle missing completed_at timestamp."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 500,
            "status": "in_progress",
            "started_at": "2024-01-01T00:00:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-111")

        assert attempt.completed_at is None
        assert attempt.duration_seconds == 0.0

    def test_convert_attempt_with_logs_url(self):
        """convert_attempt() should capture logs_url if provided."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 600,
            "status": "completed",
            "started_at": "2024-01-01T00:00:00Z",
            "logsUrl": "https://github.com/owner/repo/runs/123/logs",
        }

        attempt = converter.convert_attempt(api_data, "run-222")

        assert attempt.logs_url == "https://github.com/owner/repo/runs/123/logs"

    def test_convert_attempt_snake_case_logs_url(self):
        """convert_attempt() should handle snake_case logs_url."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 700,
            "status": "completed",
            "started_at": "2024-01-01T00:00:00Z",
            "logs_url": "https://example.com/logs",
        }

        attempt = converter.convert_attempt(api_data, "run-333")

        assert attempt.logs_url == "https://example.com/logs"

    def test_convert_attempt_invalid_conclusion(self):
        """convert_attempt() should log warning for invalid conclusion."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 800,
            "status": "completed",
            "conclusion": "not_valid",
            "started_at": "2024-01-01T00:00:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-444")

        assert attempt.conclusion is None

    @pytest.mark.parametrize("status_val", [
        "queued", "in_progress", "completed", "waiting", "requested", "pending"
    ])
    def test_convert_attempt_all_valid_statuses(self, status_val):
        """convert_attempt() should accept all valid status values."""
        converter = GitHubToWorkflowConverter()
        api_data = {
            "id": 900,
            "status": status_val,
            "started_at": "2024-01-01T00:00:00Z",
        }

        attempt = converter.convert_attempt(api_data, "run-555")
        assert attempt.status == WorkflowStatus(status_val)


class TestGitHubToWorkflowConverterTimestampParsing:
    """Tests for GitHubToWorkflowConverter timestamp parsing."""

    def test_parse_github_timestamp_with_z_suffix(self):
        """_parse_github_timestamp() should handle Z-suffixed ISO 8601."""
        converter = GitHubToWorkflowConverter()
        dt = converter._parse_github_timestamp("2024-01-01T12:34:56Z")

        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 12
        assert dt.minute == 34
        assert dt.second == 56
        assert dt.tzinfo == timezone.utc

    def test_parse_github_timestamp_without_z_suffix(self):
        """_parse_github_timestamp() should handle ISO 8601 without Z."""
        converter = GitHubToWorkflowConverter()
        dt = converter._parse_github_timestamp("2024-06-15T18:30:45")

        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 18
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.tzinfo == timezone.utc

    def test_parse_github_timestamp_with_microseconds(self):
        """_parse_github_timestamp() should handle timestamps with microseconds."""
        converter = GitHubToWorkflowConverter()
        dt = converter._parse_github_timestamp("2024-01-01T00:00:00.123456Z")

        assert dt.microsecond == 123456

    def test_parse_github_timestamp_invalid_format(self):
        """_parse_github_timestamp() should raise ValueError for invalid format."""
        converter = GitHubToWorkflowConverter()

        with pytest.raises(ValueError, match="Failed to parse timestamp"):
            converter._parse_github_timestamp("not-a-timestamp")

    def test_parse_github_timestamp_ensures_utc(self):
        """_parse_github_timestamp() should ensure all timestamps are UTC."""
        converter = GitHubToWorkflowConverter()
        dt = converter._parse_github_timestamp("2024-01-01T12:00:00Z")

        assert dt.tzinfo == timezone.utc


# ============================================================================
# Integration-like tests (combining multiple components)
# ============================================================================

class TestGitHubAdaptersIntegration:
    """Integration-like tests combining adapters and converters."""

    def test_api_client_output_with_converter(self):
        """Converter should handle output from APIClient.get_runs()."""
        converter = GitHubToWorkflowConverter()
        api_response = {
            "id": 1,
            "name": "Build Workflow",
            "headBranch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:30:00Z",
            "runNumber": 42,
            "headSha": "abc123def456",
        }

        run = converter.convert_run(api_response)

        assert run.workflow_name == "Build Workflow"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.duration_seconds == 1800.0  # 30 minutes

    def test_cli_adapter_output_with_converter(self):
        """Converter should handle output from CliAdapter.get_runs()."""
        converter = GitHubToWorkflowConverter()
        cli_response = {
            "id": 2,
            "name": "Test Workflow",
            "headBranch": "develop",
            "status": "in_progress",
            "created_at": "2024-01-02T10:00:00Z",
        }

        run = converter.convert_run(cli_response)

        assert run.workflow_name == "Test Workflow"
        assert run.branch == "develop"
        assert run.status == WorkflowStatus.IN_PROGRESS
