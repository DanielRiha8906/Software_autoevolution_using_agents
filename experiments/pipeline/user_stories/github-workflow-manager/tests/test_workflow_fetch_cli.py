"""Tests for GitHub fetch CLI command integration."""

import pytest
from unittest.mock import patch, MagicMock

from src.auth.github_auth import GitHubAuthManager
from src.services.github_api_fetcher import GitHubAPIFetcher
from src.services.github_cli_fetcher import GitHubCLIFetcher
from src.exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)


class TestWorkflowFetchCLIArgumentHandling:
    """Test fetch command argument handling."""

    def test_fetch_command_exists(self):
        """Fetch command should be available in CLI."""
        # This is tested implicitly by the existence of fetch_p in workflow_cli.py
        # See workflow_cli.py lines 242-255 for fetch subcommand definition
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        # Parse should succeed with fetch command
        args = parser.parse_args(["fetch", "--owner", "test", "--repo", "test", "--mode", "api", "--token", "ghp_test"])
        assert args.command == "fetch"
        assert args.owner == "test"
        assert args.repo == "test"
        assert args.mode == "api"

    def test_fetch_command_owner_required(self):
        """--owner should be required for fetch command."""
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["fetch", "--repo", "test", "--mode", "api"])

    def test_fetch_command_repo_required(self):
        """--repo should be required for fetch command."""
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["fetch", "--owner", "test", "--mode", "api"])

    def test_fetch_command_mode_required(self):
        """--mode should be required for fetch command."""
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["fetch", "--owner", "test", "--repo", "test"])

    def test_fetch_command_accepts_optional_filters(self):
        """Fetch command should accept optional filter arguments."""
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "fetch",
            "--owner", "test",
            "--repo", "test",
            "--mode", "api",
            "--branch", "main",
            "--status", "completed",
            "--created-after", "2025-05-01",
            "--token", "ghp_test",
        ])
        assert args.branch == "main"
        assert args.status == "completed"
        assert args.created_after == "2025-05-01"
        assert args.token == "ghp_test"

    def test_fetch_command_optional_filters_default_to_none(self):
        """Optional filter arguments should default to None."""
        from src.cli.workflow_cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["fetch", "--owner", "test", "--repo", "test", "--mode", "cli"])
        assert args.branch is None
        assert args.status is None
        assert args.created_after is None
        assert args.token is None


class TestTokenResolutionInFetch:
    """Test token resolution during fetch."""

    def test_explicit_token_takes_precedence(self):
        """Explicit --token flag should override env var."""
        auth = GitHubAuthManager()
        token = auth.get_token(explicit_token="ghp_explicit_token_12345678901234567890")
        assert token == "ghp_explicit_token_12345678901234567890"

    def test_invalid_token_format_detected(self):
        """Invalid token format should be detected."""
        auth = GitHubAuthManager()
        assert auth.validate_token("invalid") is False
        assert auth.validate_token("ghp_short") is False
        # Valid token: ghp_ (4 chars) + at least 36 chars = 40+ chars total
        assert auth.validate_token("ghp_abcdefghijklmnopqrstuvwxyz0123456789") is True


class TestAPIFetcherErrorPropagation:
    """Test error handling through API fetcher."""

    def test_api_fetcher_auth_error_propagates(self):
        """Auth errors from API fetcher should propagate."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            with pytest.raises(GitHubAuthError):
                fetcher.fetch_runs("owner", "repo")

    def test_api_fetcher_rate_limit_error_propagates(self):
        """Rate limit errors should propagate."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {"X-RateLimit-Remaining": "0"}
            mock_get.return_value = mock_response

            with pytest.raises(GitHubRateLimitError):
                fetcher.fetch_runs("owner", "repo")

    def test_api_fetcher_404_error_propagates(self):
        """404 errors should propagate."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with pytest.raises(GitHubAPIError):
                fetcher.fetch_runs("owner", "repo")

    def test_api_fetcher_network_error_propagates(self):
        """Network errors should propagate."""
        import requests

        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("requests.get", side_effect=requests.ConnectionError()):
            with pytest.raises(GitHubNetworkError):
                fetcher.fetch_runs("owner", "repo")


class TestCLIFetcherErrorPropagation:
    """Test error handling through CLI fetcher."""

    def test_cli_fetcher_unavailable_error_propagates(self):
        """Unavailable gh CLI should raise error."""
        fetcher = GitHubCLIFetcher()

        with patch.object(fetcher, "is_available", return_value=False):
            with pytest.raises(GitHubNetworkError):
                fetcher.fetch_runs("owner", "repo")

    def test_cli_fetcher_command_failure_propagates(self):
        """Failed gh command should propagate error."""
        import subprocess

        fetcher = GitHubCLIFetcher()

        with patch.object(fetcher, "is_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "Repository not found"
                mock_run.return_value = mock_result

                with pytest.raises(GitHubNetworkError):
                    fetcher.fetch_runs("owner", "repo")

    def test_cli_fetcher_timeout_propagates(self):
        """Timeout should propagate as network error."""
        import subprocess

        fetcher = GitHubCLIFetcher()

        with patch.object(fetcher, "is_available", return_value=True):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
                with pytest.raises(GitHubNetworkError):
                    fetcher.fetch_runs("owner", "repo")


class TestFetchDataFlow:
    """Test data flow during fetch operations."""

    def test_api_fetcher_returns_workflow_runs(self):
        """API fetcher should return WorkflowRun objects."""
        from src.models.workflow_run import WorkflowRun

        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "workflow_runs": [
                    {
                        "id": 1,
                        "name": "Test",
                        "status": "completed",
                        "created_at": "2025-05-03T10:00:00Z",
                        "head_branch": "main",
                    }
                ]
            }
            mock_get.return_value = mock_response

            runs = fetcher.fetch_runs("owner", "repo")

            assert len(runs) == 1
            assert isinstance(runs[0], WorkflowRun)
            assert runs[0].id == "1"

    def test_cli_fetcher_returns_workflow_runs(self):
        """CLI fetcher should return WorkflowRun objects."""
        from src.models.workflow_run import WorkflowRun
        import json

        fetcher = GitHubCLIFetcher()

        with patch.object(fetcher, "is_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = json.dumps([
                    {
                        "id": "1",
                        "name": "Test",
                        "status": "COMPLETED",
                        "conclusion": "SUCCESS",
                        "createdAt": "2025-05-03T10:00:00Z",
                        "updatedAt": "2025-05-03T10:05:00Z",
                        "databaseId": 1,
                        "headBranch": "main",
                        "headSha": "abc123",
                        "runNumber": 1,
                    }
                ])
                mock_run.return_value = mock_result

                runs = fetcher.fetch_runs("owner", "repo")

                assert len(runs) == 1
                assert isinstance(runs[0], WorkflowRun)
