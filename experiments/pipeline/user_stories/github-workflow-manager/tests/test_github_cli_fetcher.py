"""Tests for GitHub CLI fetcher service."""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import subprocess

from src.services.github_cli_fetcher import GitHubCLIFetcher
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.exceptions import GitHubAPIError, GitHubNetworkError


class TestGitHubCLIFetcherAvailability:
    """Test gh CLI availability checking."""

    def test_is_available_when_installed(self):
        """Should return True when gh CLI is installed."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            assert fetcher.is_available() is True

    def test_is_not_available_when_not_installed(self):
        """Should return False when gh CLI is not found."""
        fetcher = GitHubCLIFetcher()

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            assert fetcher.is_available() is False

    def test_is_not_available_on_timeout(self):
        """Should return False when gh CLI check times out."""
        fetcher = GitHubCLIFetcher()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 5)):
            assert fetcher.is_available() is False

    def test_is_not_available_on_nonzero_exit(self):
        """Should return False when gh CLI returns non-zero exit code."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            assert fetcher.is_available() is False

    def test_availability_check_uses_version_command(self):
        """Should use 'gh --version' to check availability."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            fetcher.is_available()

        call_args = mock_run.call_args
        assert call_args[0][0] == ["gh", "--version"]
        assert call_args.kwargs["timeout"] == 5


class TestGitHubCLIFetcherSuccessfulFetch:
    """Test successful workflow run fetching via gh CLI."""

    @pytest.fixture
    def sample_gh_output(self):
        """Sample gh CLI JSON output."""
        return [
            {
                "id": "12345",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": "2025-05-03T10:05:00Z",
                "databaseId": 54321,
                "headBranch": "main",
                "headSha": "abc123",
                "runNumber": 1,
            }
        ]

    def test_fetch_single_run(self, sample_gh_output):
        """Should fetch and convert single workflow run."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 1
        assert runs[0].id == "54321"
        assert runs[0].workflow_name == "Build"
        assert runs[0].status == WorkflowStatus.COMPLETED
        assert runs[0].conclusion == WorkflowConclusion.SUCCESS

    def test_fetch_multiple_runs(self):
        """Should fetch multiple workflow runs."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "1",
                "name": "Build 1",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": "2025-05-03T10:05:00Z",
                "databaseId": 101,
                "headBranch": "main",
                "headSha": "abc",
                "runNumber": 1,
            },
            {
                "id": "2",
                "name": "Build 2",
                "status": "COMPLETED",
                "conclusion": "FAILURE",
                "createdAt": "2025-05-03T11:00:00Z",
                "updatedAt": "2025-05-03T11:05:00Z",
                "databaseId": 102,
                "headBranch": "develop",
                "headSha": "def",
                "runNumber": 2,
            },
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 2
        assert runs[0].conclusion == WorkflowConclusion.SUCCESS
        assert runs[1].conclusion == WorkflowConclusion.FAILURE

    def test_fetch_with_status_filter(self):
        """Should apply status filter to gh CLI command."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                fetcher.fetch_runs("owner", "repo", status="completed")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--status" in cmd
        assert "completed" in cmd

    def test_fetch_with_branch_filter(self):
        """Should apply branch filter via post-fetch filtering."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "1",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": "2025-05-03T10:05:00Z",
                "databaseId": 1,
                "headBranch": "main",
                "headSha": "abc",
                "runNumber": 1,
            },
            {
                "id": "2",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T11:00:00Z",
                "updatedAt": "2025-05-03T11:05:00Z",
                "databaseId": 2,
                "headBranch": "develop",
                "headSha": "def",
                "runNumber": 2,
            },
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo", branch="main")

        # Should only return run from 'main' branch
        assert len(runs) == 1
        assert runs[0].branch == "main"

    def test_fetch_with_created_after_filter(self):
        """Should apply created_after filter via post-fetch filtering."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "1",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-01T10:00:00Z",
                "updatedAt": "2025-05-01T10:05:00Z",
                "databaseId": 1,
                "headBranch": "main",
                "headSha": "abc",
                "runNumber": 1,
            },
            {
                "id": "2",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-05T11:00:00Z",
                "updatedAt": "2025-05-05T11:05:00Z",
                "databaseId": 2,
                "headBranch": "main",
                "headSha": "def",
                "runNumber": 2,
            },
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        created_after = datetime(2025, 5, 3, 0, 0, 0, tzinfo=timezone.utc)

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo", created_after=created_after)

        # Should only return run created on or after 2025-05-03
        assert len(runs) == 1
        assert runs[0].id == "2"

    def test_fetch_empty_result(self):
        """Should return empty list when no runs found."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 0


class TestGitHubCLIFetcherErrorHandling:
    """Test error handling in CLI fetcher."""

    def test_error_when_gh_not_available(self):
        """Should raise GitHubNetworkError if gh CLI not available."""
        fetcher = GitHubCLIFetcher()

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=False):
            with pytest.raises(GitHubNetworkError) as exc_info:
                fetcher.fetch_runs("owner", "repo")
            assert "GitHub CLI" in str(exc_info.value)

    def test_error_on_command_failure(self):
        """Should raise GitHubNetworkError when gh command fails."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Repository not found"
        mock_result.stdout = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(GitHubNetworkError):
                    fetcher.fetch_runs("owner", "repo")

    def test_error_on_json_decode_failure(self):
        """Should raise GitHubNetworkError on malformed JSON output."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json {"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(GitHubNetworkError) as exc_info:
                    fetcher.fetch_runs("owner", "repo")
                assert "JSON" in str(exc_info.value) or "gh CLI" in str(exc_info.value)

    def test_error_on_timeout(self):
        """Should raise GitHubNetworkError on subprocess timeout."""
        fetcher = GitHubCLIFetcher()

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
                with pytest.raises(GitHubNetworkError):
                    fetcher.fetch_runs("owner", "repo")

    def test_skip_malformed_record_and_continue(self):
        """Should skip malformed records and continue with valid ones."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "1",
                "name": "Build 1",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": "2025-05-03T10:05:00Z",
                "databaseId": 1,
                "headBranch": "main",
                "headSha": "abc",
                "runNumber": 1,
            },
            {
                "id": "2",
                "name": "Build 2",
                "status": "INVALID_STATUS",  # Invalid status enum
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T11:00:00Z",
                "updatedAt": "2025-05-03T11:05:00Z",
                "databaseId": 2,
                "headBranch": "main",
                "headSha": "def2",
                "runNumber": 2,
            },
            {
                "id": "3",
                "name": "Build 3",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T12:00:00Z",
                "updatedAt": "2025-05-03T12:05:00Z",
                "databaseId": 3,
                "headBranch": "main",
                "headSha": "def",
                "runNumber": 3,
            },
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        # Should have 2 valid runs (indices 0 and 2 - skipping the invalid status)
        assert len(runs) == 2
        assert runs[0].id == "1"
        assert runs[1].id == "3"


class TestGitHubCLIFetcherCommandConstruction:
    """Test gh CLI command construction."""

    def test_correct_command_formed(self):
        """Should form correct gh run list command."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                fetcher.fetch_runs("myowner", "myrepo")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "gh"
        assert cmd[1] == "run"
        assert cmd[2] == "list"
        assert "--repo" in cmd
        assert "myowner/myrepo" in cmd
        assert "--json" in cmd

    def test_json_fields_requested(self):
        """Should request correct JSON fields from gh CLI."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                fetcher.fetch_runs("owner", "repo")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        json_idx = cmd.index("--json")
        fields = cmd[json_idx + 1]
        assert "id" in fields
        assert "name" in fields
        assert "status" in fields
        assert "createdAt" in fields
        assert "databaseId" in fields

    def test_limit_parameter_set(self):
        """Should set --limit parameter."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                fetcher.fetch_runs("owner", "repo")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--limit" in cmd
        assert "1000" in cmd

    def test_timeout_applied(self):
        """Should apply timeout to subprocess call."""
        fetcher = GitHubCLIFetcher()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                fetcher.fetch_runs("owner", "repo")

        call_args = mock_run.call_args
        assert call_args.kwargs["timeout"] == 30


class TestGitHubCLIFetcherFieldMapping:
    """Test field mapping from gh CLI to WorkflowRun."""

    def test_gh_field_names_mapped_correctly(self):
        """Should map gh CLI field names to API field names."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "gh_id_value",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": "2025-05-03T10:05:00Z",
                "databaseId": 999,
                "headBranch": "feature",
                "headSha": "sha123",
                "runNumber": 55,
            }
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        run = runs[0]
        assert run.id == "999"  # Uses databaseId
        assert run.workflow_name == "Build"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS
        assert run.branch == "feature"
        assert run.commit_sha == "sha123"
        assert run.run_number == 55

    def test_missing_optional_fields_handled(self):
        """Should handle missing optional fields gracefully."""
        fetcher = GitHubCLIFetcher()

        gh_output = [
            {
                "id": "1",
                "name": "Build",
                "status": "COMPLETED",
                "conclusion": None,
                "createdAt": "2025-05-03T10:00:00Z",
                "updatedAt": None,
                "databaseId": 1,
                "headBranch": "main",
                "headSha": None,
                "runNumber": None,
            }
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(gh_output)
        mock_result.stderr = ""

        with patch("src.services.github_cli_fetcher.GitHubCLIFetcher.is_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                runs = fetcher.fetch_runs("owner", "repo")

        run = runs[0]
        assert run.conclusion is None
        assert run.updated_at is None
        assert run.commit_sha is None
        assert run.run_number is None
