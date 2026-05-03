"""Comprehensive tests for GitHubIntegrationService."""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, mock_open, call
from io import StringIO

import pytest
import requests

from src.models.workflow_run import WorkflowRun
from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.github_integration_service import GitHubIntegrationService


# ============================================================================
# Fixtures: Sample API Responses
# ============================================================================

@pytest.fixture
def sample_run_api_response():
    """Sample workflow run from GitHub API."""
    return {
        "id": 123456789,
        "name": "CI",
        "status": "completed",
        "conclusion": "success",
        "headBranch": "main",
        "head_branch": None,
        "runNumber": 42,
        "headSha": "abc123def456",
        "head_sha": None,
        "createdAt": "2026-05-03T10:00:00Z",
        "created_at": None,
        "updatedAt": "2026-05-03T10:05:30Z",
        "updated_at": None,
    }


@pytest.fixture
def sample_run_snake_case_response():
    """Sample workflow run with snake_case fields (from gh CLI)."""
    return {
        "id": 987654321,
        "name": "Deploy",
        "status": "in_progress",
        "conclusion": None,
        "head_branch": "feature-branch",
        "run_number": 15,
        "head_sha": "xyz789uvw012",
        "created_at": "2026-05-03T11:00:00Z",
        "updated_at": "2026-05-03T11:02:00Z",
    }


@pytest.fixture
def sample_attempt_api_response():
    """Sample workflow attempt from GitHub API."""
    return {
        "id": 555888777,
        "attemptNumber": 1,
        "status": "completed",
        "conclusion": "success",
        "startedAt": "2026-05-03T10:00:30Z",
        "started_at": None,
        "completedAt": "2026-05-03T10:05:00Z",
        "completed_at": None,
        "logsUrl": "https://api.github.com/repos/owner/repo/actions/runs/123456789/attempts/1/logs",
        "logs_url": None,
    }


@pytest.fixture
def sample_attempt_snake_case_response():
    """Sample workflow attempt with snake_case fields (from gh CLI)."""
    return {
        "id": 444333222,
        "attempt_number": 2,
        "status": "completed",
        "conclusion": "failure",
        "started_at": "2026-05-03T11:00:30Z",
        "completed_at": "2026-05-03T11:10:00Z",
        "logs_url": "https://api.github.com/repos/owner/repo/actions/runs/987654321/attempts/2/logs",
    }


@pytest.fixture
def multiple_runs_response(sample_run_api_response, sample_run_snake_case_response):
    """Response containing multiple workflow runs."""
    return {
        "total_count": 2,
        "workflow_runs": [sample_run_api_response, sample_run_snake_case_response],
    }


@pytest.fixture
def multiple_attempts_response(sample_attempt_api_response, sample_attempt_snake_case_response):
    """Response containing multiple workflow attempts."""
    return {
        "total_count": 2,
        "workflow_runs": [sample_attempt_api_response, sample_attempt_snake_case_response],
    }


# ============================================================================
# Token Resolution Tests
# ============================================================================

class TestTokenResolution:
    """Tests for token resolution from env var, secrets file, and prompt."""

    def test_resolve_token_from_environment_variable(self):
        """Token should be resolved from GITHUB_TOKEN env var."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test123"}):
            service = GitHubIntegrationService()
            token = service._resolve_token()
            assert token == "ghp_test123"

    def test_resolve_token_from_secrets_file(self):
        """Token should be resolved from secrets/.env file."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists") as mock_exists:
                with patch("builtins.open", mock_open(read_data="GITHUB_TOKEN=ghp_secret456\n")):
                    mock_exists.return_value = True
                    service = GitHubIntegrationService()
                    token = service._resolve_token()
                    assert token == "ghp_secret456"

    def test_resolve_token_from_secrets_file_with_whitespace(self):
        """Token should be resolved with whitespace stripped."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists") as mock_exists:
                with patch("builtins.open", mock_open(read_data="GITHUB_TOKEN=  ghp_secret789  \n")):
                    mock_exists.return_value = True
                    service = GitHubIntegrationService()
                    token = service._resolve_token()
                    assert token == "ghp_secret789"

    def test_resolve_token_from_prompt(self):
        """Token should be resolved from user input prompt."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", return_value="ghp_prompted123"):
                    service = GitHubIntegrationService()
                    token = service._resolve_token()
                    assert token == "ghp_prompted123"

    def test_resolve_token_priority_env_over_secrets(self):
        """Environment variable should have priority over secrets file."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_env"}):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="GITHUB_TOKEN=ghp_file\n")):
                    service = GitHubIntegrationService()
                    token = service._resolve_token()
                    assert token == "ghp_env"

    def test_resolve_token_priority_secrets_over_prompt(self):
        """Secrets file should have priority over prompt."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="GITHUB_TOKEN=ghp_file\n")):
                    with patch("builtins.input", return_value="ghp_prompted") as mock_input:
                        service = GitHubIntegrationService()
                        token = service._resolve_token()
                        assert token == "ghp_file"
                        mock_input.assert_not_called()

    def test_resolve_token_prompt_cancelled_raises_error(self):
        """Should raise RuntimeError when user cancels prompt (Ctrl+C)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    service = GitHubIntegrationService()
                    with pytest.raises(RuntimeError, match="Token input cancelled"):
                        service._resolve_token()

    def test_resolve_token_empty_input_raises_error(self):
        """Should raise RuntimeError when user provides empty token."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("builtins.input", return_value=""):
                    service = GitHubIntegrationService()
                    with pytest.raises(RuntimeError, match="No token provided"):
                        service._resolve_token()

    def test_resolve_token_secrets_file_read_error_falls_through(self):
        """Should fall through to prompt if secrets file cannot be read."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=IOError("Permission denied")):
                    with patch("builtins.input", return_value="ghp_fallback"):
                        service = GitHubIntegrationService()
                        token = service._resolve_token()
                        assert token == "ghp_fallback"

    def test_resolve_token_secrets_file_no_github_token_line_falls_through(self):
        """Should fall through to prompt if GITHUB_TOKEN line not in secrets file."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="OTHER_VAR=value\n")):
                    with patch("builtins.input", return_value="ghp_fallback"):
                        service = GitHubIntegrationService()
                        token = service._resolve_token()
                        assert token == "ghp_fallback"


# ============================================================================
# Token Validation Tests
# ============================================================================

class TestTokenValidation:
    """Tests for token validation."""

    def test_validate_token_api_mode_success(self):
        """Token validation should succeed with 200 response in API mode."""
        service = GitHubIntegrationService(fetch_mode="api")
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = service._validate_token("ghp_test123")
            assert result is True

    def test_validate_token_api_mode_unauthorized(self):
        """Token validation should fail with 401 response in API mode."""
        service = GitHubIntegrationService(fetch_mode="api")
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = service._validate_token("ghp_invalid")
            assert result is False

    def test_validate_token_api_mode_other_error(self):
        """Token validation should fail with non-200/401 responses."""
        service = GitHubIntegrationService(fetch_mode="api")
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            result = service._validate_token("ghp_test123")
            assert result is False

    def test_validate_token_api_mode_network_error(self):
        """Token validation should fail with network errors."""
        service = GitHubIntegrationService(fetch_mode="api")
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")

            result = service._validate_token("ghp_test123")
            assert result is False

    def test_validate_token_api_mode_timeout(self):
        """Token validation should fail with timeout."""
        service = GitHubIntegrationService(fetch_mode="api")
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")

            result = service._validate_token("ghp_test123")
            assert result is False

    def test_validate_token_cli_mode_success(self):
        """Token validation should succeed with gh CLI when command returns 0."""
        service = GitHubIntegrationService(fetch_mode="cli")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = service._validate_token("ghp_test123")
            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ["gh", "auth", "status"]

    def test_validate_token_cli_mode_failure(self):
        """Token validation should fail with gh CLI when command returns non-zero."""
        service = GitHubIntegrationService(fetch_mode="cli")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = service._validate_token("ghp_test123")
            assert result is False

    def test_validate_token_cli_mode_timeout(self):
        """Token validation should fail with gh CLI timeout."""
        service = GitHubIntegrationService(fetch_mode="cli")
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gh", timeout=5)

            result = service._validate_token("ghp_test123")
            assert result is False

    def test_validate_token_cli_mode_not_found(self):
        """Token validation should fail when gh CLI is not installed."""
        service = GitHubIntegrationService(fetch_mode="cli")
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")

            result = service._validate_token("ghp_test123")
            assert result is False


# ============================================================================
# Timestamp Parsing Tests
# ============================================================================

class TestTimestampParsing:
    """Tests for GitHub timestamp parsing."""

    def test_parse_github_timestamp_with_z_suffix(self):
        """Should parse timestamp with Z suffix (UTC indicator)."""
        result = GitHubIntegrationService._parse_github_timestamp("2026-05-03T10:00:00Z")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_parse_github_timestamp_without_z_suffix(self):
        """Should parse timestamp without Z suffix."""
        result = GitHubIntegrationService._parse_github_timestamp("2026-05-03T10:00:00")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 3
        assert result.tzinfo == timezone.utc

    def test_parse_github_timestamp_with_microseconds(self):
        """Should parse timestamp with microseconds."""
        result = GitHubIntegrationService._parse_github_timestamp("2026-05-03T10:00:00.123456Z")
        assert result.microsecond == 123456
        assert result.tzinfo == timezone.utc

    def test_parse_github_timestamp_with_timezone_offset(self):
        """Should parse timestamp with timezone offset and convert to UTC."""
        result = GitHubIntegrationService._parse_github_timestamp("2026-05-03T10:00:00+02:00")
        assert result.tzinfo == timezone.utc
        # Time should be adjusted to UTC
        assert result.hour == 8  # 10:00+02:00 = 08:00 UTC

    def test_parse_github_timestamp_invalid_format(self):
        """Should raise ValueError for invalid timestamp format."""
        with pytest.raises(ValueError, match="Failed to parse timestamp"):
            GitHubIntegrationService._parse_github_timestamp("not-a-timestamp")

    def test_parse_github_timestamp_invalid_date(self):
        """Should raise ValueError for invalid date."""
        with pytest.raises(ValueError, match="Failed to parse timestamp"):
            GitHubIntegrationService._parse_github_timestamp("2026-13-40T10:00:00Z")


# ============================================================================
# API Response Conversion Tests
# ============================================================================

class TestConvertApiRun:
    """Tests for converting GitHub API run responses to WorkflowRun."""

    def test_convert_api_run_camel_case(self, sample_run_api_response):
        """Should convert camelCase API response to WorkflowRun."""
        service = GitHubIntegrationService()
        run = service._convert_api_run(sample_run_api_response, "test-repo")

        assert run.id == "123456789"
        assert run.workflow_name == "CI"
        assert run.branch == "main"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS
        assert run.run_number == 42
        assert run.commit_sha == "abc123def456"
        assert isinstance(run.created_at, datetime)
        assert isinstance(run.updated_at, datetime)
        assert run.duration_seconds == (run.updated_at - run.created_at).total_seconds()

    def test_convert_api_run_snake_case(self, sample_run_snake_case_response):
        """Should convert snake_case API response to WorkflowRun."""
        service = GitHubIntegrationService()
        run = service._convert_api_run(sample_run_snake_case_response, "test-repo")

        assert run.id == "987654321"
        assert run.workflow_name == "Deploy"
        assert run.branch == "feature-branch"
        assert run.status == WorkflowStatus.IN_PROGRESS
        assert run.conclusion is None
        assert run.run_number == 15
        assert run.commit_sha == "xyz789uvw012"

    def test_convert_api_run_missing_created_at(self):
        """Should raise ValueError when createdAt is missing."""
        service = GitHubIntegrationService()
        data = {
            "id": 123,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
        }
        with pytest.raises(ValueError, match="Missing createdAt"):
            service._convert_api_run(data, "repo")

    def test_convert_api_run_missing_status(self, sample_run_api_response):
        """Should raise ValueError when status is missing."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["status"] = None
        with pytest.raises(ValueError, match="Missing status"):
            service._convert_api_run(data, "repo")

    def test_convert_api_run_invalid_status(self, sample_run_api_response):
        """Should raise ValueError for invalid status value."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["status"] = "invalid_status"
        with pytest.raises(ValueError, match="Invalid status value"):
            service._convert_api_run(data, "repo")

    def test_convert_api_run_invalid_conclusion_logged(self, sample_run_api_response):
        """Should log warning for invalid conclusion but continue."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["conclusion"] = "invalid_conclusion"

        run = service._convert_api_run(data, "repo")
        assert run.conclusion is None
        assert run.status == WorkflowStatus.COMPLETED

    def test_convert_api_run_without_conclusion(self, sample_run_api_response):
        """Should handle runs without conclusion (in-progress)."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["status"] = "in_progress"
        data["conclusion"] = None

        run = service._convert_api_run(data, "repo")
        assert run.status == WorkflowStatus.IN_PROGRESS
        assert run.conclusion is None

    def test_convert_api_run_missing_optional_fields(self, sample_run_api_response):
        """Should handle missing optional fields gracefully."""
        service = GitHubIntegrationService()
        data = {
            "id": 123,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-05-03T10:00:00Z",
            # Missing: headBranch, runNumber, headSha, updatedAt
        }

        run = service._convert_api_run(data, "repo")
        assert run.id == "123"
        assert run.branch == ""
        assert run.run_number is None
        assert run.commit_sha is None
        assert run.updated_at is None
        assert run.duration_seconds == 0.0

    def test_convert_api_run_duration_calculation(self, sample_run_api_response):
        """Should calculate duration correctly."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        run = service._convert_api_run(data, "repo")

        expected_duration = 330.0  # 5 minutes 30 seconds
        assert abs(run.duration_seconds - expected_duration) < 1.0


class TestConvertApiAttempt:
    """Tests for converting GitHub API attempt responses to WorkflowRunAttempt."""

    def test_convert_api_attempt_camel_case(self, sample_attempt_api_response):
        """Should convert camelCase API response to WorkflowRunAttempt."""
        service = GitHubIntegrationService()
        attempt = service._convert_api_attempt(sample_attempt_api_response, "run-123", "repo")

        assert attempt.id == "555888777"
        assert attempt.run_id == "run-123"
        assert attempt.attempt_number == 1
        assert attempt.status == WorkflowStatus.COMPLETED
        assert attempt.conclusion == WorkflowConclusion.SUCCESS
        assert isinstance(attempt.started_at, datetime)
        assert isinstance(attempt.completed_at, datetime)

    def test_convert_api_attempt_snake_case(self, sample_attempt_snake_case_response):
        """Should convert snake_case API response to WorkflowRunAttempt."""
        service = GitHubIntegrationService()
        attempt = service._convert_api_attempt(
            sample_attempt_snake_case_response, "run-456", "repo"
        )

        assert attempt.id == "444333222"
        assert attempt.run_id == "run-456"
        assert attempt.attempt_number == 2
        assert attempt.status == WorkflowStatus.COMPLETED
        assert attempt.conclusion == WorkflowConclusion.FAILURE

    def test_convert_api_attempt_missing_started_at(self):
        """Should raise ValueError when startedAt is missing."""
        service = GitHubIntegrationService()
        data = {
            "id": 123,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
        }
        with pytest.raises(ValueError, match="Missing startedAt"):
            service._convert_api_attempt(data, "run-123", "repo")

    def test_convert_api_attempt_missing_status(self, sample_attempt_api_response):
        """Should raise ValueError when status is missing."""
        service = GitHubIntegrationService()
        data = sample_attempt_api_response.copy()
        data["status"] = None
        with pytest.raises(ValueError, match="Missing status"):
            service._convert_api_attempt(data, "run-123", "repo")

    def test_convert_api_attempt_invalid_status(self, sample_attempt_api_response):
        """Should raise ValueError for invalid status."""
        service = GitHubIntegrationService()
        data = sample_attempt_api_response.copy()
        data["status"] = "unknown_status"
        with pytest.raises(ValueError, match="Invalid status value"):
            service._convert_api_attempt(data, "run-123", "repo")

    def test_convert_api_attempt_invalid_conclusion_logged(self, sample_attempt_api_response):
        """Should log warning for invalid conclusion but continue."""
        service = GitHubIntegrationService()
        data = sample_attempt_api_response.copy()
        data["conclusion"] = "bad_conclusion"

        attempt = service._convert_api_attempt(data, "run-123", "repo")
        assert attempt.conclusion is None

    def test_convert_api_attempt_without_conclusion(self, sample_attempt_api_response):
        """Should handle attempts without conclusion (in-progress)."""
        service = GitHubIntegrationService()
        data = sample_attempt_api_response.copy()
        data["status"] = "in_progress"
        data["conclusion"] = None

        attempt = service._convert_api_attempt(data, "run-123", "repo")
        assert attempt.conclusion is None
        assert attempt.status == WorkflowStatus.IN_PROGRESS

    def test_convert_api_attempt_missing_optional_fields(self, sample_attempt_api_response):
        """Should handle missing optional fields."""
        service = GitHubIntegrationService()
        data = {
            "id": 123,
            "status": "completed",
            "conclusion": "success",
            "startedAt": "2026-05-03T10:00:00Z",
            # Missing: attempt_number, completed_at, logs_url
        }

        attempt = service._convert_api_attempt(data, "run-123", "repo")
        assert attempt.id == "123"
        assert attempt.attempt_number == 1  # Default
        assert attempt.completed_at is None
        assert attempt.logs_url is None
        assert attempt.duration_seconds == 0.0

    def test_convert_api_attempt_duration_calculation(self, sample_attempt_api_response):
        """Should calculate duration correctly."""
        service = GitHubIntegrationService()
        data = sample_attempt_api_response.copy()
        attempt = service._convert_api_attempt(data, "run-123", "repo")

        expected_duration = 270.0  # 4 minutes 30 seconds
        assert abs(attempt.duration_seconds - expected_duration) < 1.0


# ============================================================================
# Fetch Runs Tests (API Mode)
# ============================================================================

class TestFetchRunsApi:
    """Tests for fetching workflow runs using REST API."""

    def test_fetch_runs_api_success(self, multiple_runs_response):
        """Should fetch and convert multiple runs."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = multiple_runs_response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo")

                    assert len(runs) == 2
                    assert all(isinstance(r, WorkflowRun) for r in runs)
                    assert runs[0].workflow_name == "CI"
                    assert runs[1].workflow_name == "Deploy"

    def test_fetch_runs_api_with_workflow_filter(self, sample_run_api_response, sample_run_snake_case_response):
        """Should filter runs by workflow name."""
        response = {
            "workflow_runs": [sample_run_api_response, sample_run_snake_case_response]
        }
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo", workflow_name="CI")

                    assert len(runs) == 1
                    assert runs[0].workflow_name == "CI"

    def test_fetch_runs_api_with_limit(self, sample_run_api_response):
        """Should respect limit parameter."""
        response = {
            "workflow_runs": [sample_run_api_response] * 5
        }
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo", limit=3)

                    assert len(runs) == 3

    def test_fetch_runs_api_token_validation_failure(self):
        """Should raise RuntimeError when token validation fails."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=False):
                with pytest.raises(RuntimeError, match="token validation failed"):
                    service.fetch_runs("owner", "repo")

    def test_fetch_runs_api_network_error(self):
        """Should raise RuntimeError on network error."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_get.side_effect = requests.RequestException("Connection failed")

                    with pytest.raises(RuntimeError, match="Failed to fetch runs"):
                        service.fetch_runs("owner", "repo")

    def test_fetch_runs_api_invalid_json_response(self):
        """Should raise RuntimeError on invalid JSON response."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                    mock_get.return_value = mock_response

                    with pytest.raises(RuntimeError, match="Invalid JSON response"):
                        service.fetch_runs("owner", "repo")

    def test_fetch_runs_api_skips_invalid_runs(self, sample_run_api_response):
        """Should skip runs that fail to convert."""
        invalid_run = {"id": 999, "name": "Bad", "status": "invalid"}
        response = {
            "workflow_runs": [sample_run_api_response, invalid_run]
        }
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo")

                    assert len(runs) == 1
                    assert runs[0].workflow_name == "CI"

    def test_fetch_runs_api_empty_response(self):
        """Should return empty list for empty response."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"workflow_runs": []}
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo")

                    assert runs == []

    def test_fetch_runs_api_http_error(self):
        """Should raise RuntimeError on HTTP error."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
                    mock_get.return_value = mock_response

                    with pytest.raises(RuntimeError, match="Failed to fetch runs"):
                        service.fetch_runs("owner", "repo")


# ============================================================================
# Fetch Runs Tests (CLI Mode)
# ============================================================================

class TestFetchRunsCli:
    """Tests for fetching workflow runs using gh CLI."""

    def test_fetch_runs_cli_success(self, sample_run_api_response, sample_run_snake_case_response):
        """Should fetch and convert runs from gh CLI output."""
        cli_output = json.dumps([sample_run_api_response, sample_run_snake_case_response])
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value=cli_output):
                    runs = service.fetch_runs("owner", "repo")

                    assert len(runs) == 2
                    assert runs[0].workflow_name == "CI"
                    assert runs[1].workflow_name == "Deploy"

    def test_fetch_runs_cli_with_workflow_filter(self, sample_run_api_response, sample_run_snake_case_response):
        """Should filter runs by workflow name."""
        cli_output = json.dumps([sample_run_api_response, sample_run_snake_case_response])
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value=cli_output):
                    runs = service.fetch_runs("owner", "repo", workflow_name="Deploy")

                    assert len(runs) == 1
                    assert runs[0].workflow_name == "Deploy"

    def test_fetch_runs_cli_invalid_json(self):
        """Should raise RuntimeError on invalid JSON from gh CLI."""
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value="not valid json"):
                    with pytest.raises(RuntimeError, match="Invalid JSON output"):
                        service.fetch_runs("owner", "repo")

    def test_fetch_runs_cli_command_fails(self):
        """Should raise RuntimeError when gh CLI command fails."""
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", side_effect=RuntimeError("gh failed")):
                    with pytest.raises(RuntimeError, match="Failed to fetch runs using gh CLI"):
                        service.fetch_runs("owner", "repo")


# ============================================================================
# Fetch Attempts Tests (API Mode)
# ============================================================================

class TestFetchAttemptsApi:
    """Tests for fetching workflow attempts using REST API."""

    def test_fetch_attempts_api_success(self, multiple_attempts_response):
        """Should fetch and convert multiple attempts."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = multiple_attempts_response
                    mock_get.return_value = mock_response

                    attempts = service.fetch_run_attempts("owner", "repo", "run-123")

                    assert len(attempts) == 2
                    assert all(isinstance(a, WorkflowRunAttempt) for a in attempts)
                    assert attempts[0].attempt_number == 1
                    assert attempts[1].attempt_number == 2

    def test_fetch_attempts_api_single_attempt(self, sample_attempt_api_response):
        """Should fetch single attempt."""
        response = {"workflow_runs": [sample_attempt_api_response]}
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    attempts = service.fetch_run_attempts("owner", "repo", "run-123")

                    assert len(attempts) == 1
                    assert attempts[0].attempt_number == 1

    def test_fetch_attempts_api_token_validation_failure(self):
        """Should raise RuntimeError when token validation fails."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=False):
                with pytest.raises(RuntimeError, match="token validation failed"):
                    service.fetch_run_attempts("owner", "repo", "run-123")

    def test_fetch_attempts_api_network_error(self):
        """Should raise RuntimeError on network error."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_get.side_effect = requests.RequestException("Connection failed")

                    with pytest.raises(RuntimeError, match="Failed to fetch attempts"):
                        service.fetch_run_attempts("owner", "repo", "run-123")

    def test_fetch_attempts_api_invalid_json(self):
        """Should raise RuntimeError on invalid JSON."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                    mock_get.return_value = mock_response

                    with pytest.raises(RuntimeError, match="Invalid JSON response"):
                        service.fetch_run_attempts("owner", "repo", "run-123")

    def test_fetch_attempts_api_skips_invalid(self, sample_attempt_api_response):
        """Should skip attempts that fail to convert."""
        invalid_attempt = {"id": 999, "status": "bad_status"}
        response = {
            "workflow_runs": [sample_attempt_api_response, invalid_attempt]
        }
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    attempts = service.fetch_run_attempts("owner", "repo", "run-123")

                    assert len(attempts) == 1
                    assert attempts[0].attempt_number == 1

    def test_fetch_attempts_api_empty_response(self):
        """Should return empty list for empty response."""
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"workflow_runs": []}
                    mock_get.return_value = mock_response

                    attempts = service.fetch_run_attempts("owner", "repo", "run-123")

                    assert attempts == []


# ============================================================================
# Fetch Attempts Tests (CLI Mode)
# ============================================================================

class TestFetchAttemptsCli:
    """Tests for fetching workflow attempts using gh CLI."""

    def test_fetch_attempts_cli_success(self, sample_attempt_api_response, sample_attempt_snake_case_response):
        """Should fetch and convert attempts from gh CLI output."""
        cli_output = json.dumps({
            "attempts": [sample_attempt_api_response, sample_attempt_snake_case_response]
        })
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value=cli_output):
                    attempts = service.fetch_run_attempts("owner", "repo", "run-123")

                    assert len(attempts) == 2
                    assert attempts[0].attempt_number == 1
                    assert attempts[1].attempt_number == 2

    def test_fetch_attempts_cli_invalid_json(self):
        """Should raise RuntimeError on invalid JSON."""
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value="not json"):
                    with pytest.raises(RuntimeError, match="Invalid JSON output"):
                        service.fetch_run_attempts("owner", "repo", "run-123")

    def test_fetch_attempts_cli_missing_attempts_key(self):
        """Should raise RuntimeError if 'attempts' key missing from JSON."""
        service = GitHubIntegrationService(fetch_mode="cli")
        cli_output = json.dumps({"data": []})

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", return_value=cli_output):
                    with pytest.raises(RuntimeError, match="Invalid gh CLI output: missing 'attempts' key"):
                        service.fetch_run_attempts("owner", "repo", "run-123")

    def test_fetch_attempts_cli_command_fails(self):
        """Should raise RuntimeError when gh CLI command fails."""
        service = GitHubIntegrationService(fetch_mode="cli")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch.object(service, "_call_gh_cli", side_effect=RuntimeError("gh failed")):
                    with pytest.raises(RuntimeError, match="Failed to fetch attempts using gh CLI"):
                        service.fetch_run_attempts("owner", "repo", "run-123")


# ============================================================================
# GH CLI Command Execution Tests
# ============================================================================

class TestCallGhCli:
    """Tests for executing gh CLI commands."""

    def test_call_gh_cli_success(self):
        """Should execute gh CLI command and return stdout."""
        service = GitHubIntegrationService()
        expected_output = '{"id": 123}'

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = expected_output
            mock_run.return_value = mock_result

            output = service._call_gh_cli(["gh", "run", "list"])

            assert output == expected_output

    def test_call_gh_cli_command_failure(self):
        """Should raise RuntimeError when gh CLI returns non-zero."""
        service = GitHubIntegrationService()

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error message"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="gh CLI failed"):
                service._call_gh_cli(["gh", "run", "list"])

    def test_call_gh_cli_timeout(self):
        """Should raise RuntimeError on timeout."""
        service = GitHubIntegrationService()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gh", timeout=30)

            with pytest.raises(RuntimeError, match="timed out"):
                service._call_gh_cli(["gh", "run", "list"])

    def test_call_gh_cli_not_found(self):
        """Should raise RuntimeError when gh CLI not found."""
        service = GitHubIntegrationService()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")

            with pytest.raises(RuntimeError, match="gh CLI not found"):
                service._call_gh_cli(["gh", "run", "list"])


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_fetch_runs_explicit_token_override(self, sample_run_api_response):
        """Should use explicit token parameter over resolved token."""
        response = {"workflow_runs": [sample_run_api_response]}
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token") as mock_resolve:
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo", token="ghp_explicit")

                    mock_resolve.assert_not_called()
                    # Validate was called with explicit token
                    assert len(runs) == 1

    def test_fetch_attempts_explicit_token_override(self, sample_attempt_api_response):
        """Should use explicit token parameter over resolved token."""
        response = {"workflow_runs": [sample_attempt_api_response]}
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token") as mock_resolve:
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    attempts = service.fetch_run_attempts(
                        "owner", "repo", "run-123", token="ghp_explicit"
                    )

                    mock_resolve.assert_not_called()
                    assert len(attempts) == 1


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_convert_api_run_with_zero_duration(self, sample_run_api_response):
        """Should handle run with same created and updated timestamps."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["updatedAt"] = data["createdAt"]

        run = service._convert_api_run(data, "repo")
        assert run.duration_seconds == 0.0

    def test_convert_api_run_id_as_integer(self, sample_run_api_response):
        """Should convert integer run IDs to strings."""
        service = GitHubIntegrationService()
        assert isinstance(service._convert_api_run(sample_run_api_response, "repo").id, str)

    def test_fetch_runs_with_max_limit(self, sample_run_api_response):
        """Should cap limit at 100 (GitHub API max)."""
        response = {"workflow_runs": [sample_run_api_response] * 150}
        service = GitHubIntegrationService(fetch_mode="api")

        with patch.object(service, "_resolve_token", return_value="ghp_test"):
            with patch.object(service, "_validate_token", return_value=True):
                with patch("requests.get") as mock_get:
                    mock_response = MagicMock()
                    mock_response.json.return_value = response
                    mock_get.return_value = mock_response

                    runs = service.fetch_runs("owner", "repo", limit=500)

                    # Should have requested with per_page=100
                    call_args = mock_get.call_args
                    assert call_args[1]["params"]["per_page"] == 100

    def test_workflow_status_enum_variations(self, sample_run_api_response):
        """Should handle all valid workflow status values."""
        service = GitHubIntegrationService()
        valid_statuses = ["queued", "in_progress", "completed", "waiting", "requested", "pending"]

        for status_val in valid_statuses:
            data = sample_run_api_response.copy()
            data["status"] = status_val
            run = service._convert_api_run(data, "repo")
            assert run.status == WorkflowStatus(status_val)

    def test_workflow_conclusion_enum_variations(self, sample_run_api_response):
        """Should handle all valid conclusion values."""
        service = GitHubIntegrationService()
        valid_conclusions = [
            "success", "failure", "cancelled", "skipped", "timed_out",
            "action_required", "neutral", "stale"
        ]

        for conclusion_val in valid_conclusions:
            data = sample_run_api_response.copy()
            data["conclusion"] = conclusion_val
            run = service._convert_api_run(data, "repo")
            assert run.conclusion == WorkflowConclusion(conclusion_val)

    def test_special_characters_in_fields(self, sample_run_api_response):
        """Should handle special characters in workflow names and branches."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        data["name"] = "CI/CD: Test & Deploy"
        data["headBranch"] = "feature/special-chars-!@#"

        run = service._convert_api_run(data, "repo")
        assert run.workflow_name == "CI/CD: Test & Deploy"
        assert run.branch == "feature/special-chars-!@#"

    def test_very_long_run_duration(self, sample_run_api_response):
        """Should handle very long run durations correctly."""
        service = GitHubIntegrationService()
        data = sample_run_api_response.copy()
        # 24 hours later
        data["updatedAt"] = "2026-05-04T10:00:00Z"

        run = service._convert_api_run(data, "repo")
        expected_duration = 86400  # 24 hours in seconds
        assert abs(run.duration_seconds - expected_duration) < 1

    def test_missing_optional_attempt_fields(self, sample_attempt_api_response):
        """Should handle attempts with minimal fields."""
        service = GitHubIntegrationService()
        data = {
            "id": 123,
            "status": "completed",
            "startedAt": "2026-05-03T10:00:00Z",
        }

        attempt = service._convert_api_attempt(data, "run-123", "repo")
        assert attempt.attempt_number == 1
        assert attempt.conclusion is None
        assert attempt.completed_at is None
        assert attempt.logs_url is None
