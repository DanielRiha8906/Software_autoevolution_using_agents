"""Tests for GitHub API fetcher service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, Mock
import requests

from src.services.github_api_fetcher import GitHubAPIFetcher
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)


class TestGitHubAPIFetcherInitialization:
    """Test GitHubAPIFetcher initialization."""

    def test_init_with_token(self):
        """Fetcher should initialize with provided token."""
        token = "ghp_test_token_12345678901234567890"
        fetcher = GitHubAPIFetcher(token)
        assert fetcher._token == token

    def test_init_sets_headers(self):
        """Fetcher should set authentication headers."""
        token = "ghp_test_token_12345678901234567890"
        fetcher = GitHubAPIFetcher(token)
        assert "Authorization" in fetcher._headers
        assert f"token {token}" == fetcher._headers["Authorization"]
        assert "User-Agent" in fetcher._headers
        assert fetcher._headers["Accept"] == "application/vnd.github.v3+json"

    def test_base_url_constant(self):
        """BASE_URL should be GitHub API endpoint."""
        assert GitHubAPIFetcher.BASE_URL == "https://api.github.com"

    def test_default_per_page_constant(self):
        """DEFAULT_PER_PAGE should be 30."""
        assert GitHubAPIFetcher.DEFAULT_PER_PAGE == 30

    def test_timeout_seconds_constant(self):
        """TIMEOUT_SECONDS should be 10."""
        assert GitHubAPIFetcher.TIMEOUT_SECONDS == 10


class TestGitHubAPIFetcherSuccessfulFetch:
    """Test successful workflow run fetching."""

    @pytest.fixture
    def mock_response_data(self):
        """Sample GitHub API response."""
        return {
            "workflow_runs": [
                {
                    "id": 12345,
                    "name": "Build",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:05:00Z",
                    "run_number": 1,
                    "head_sha": "abc123",
                    "head_branch": "main",
                }
            ]
        }

    def test_fetch_single_run(self, mock_response_data):
        """Should fetch and convert single workflow run."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 1
        assert runs[0].id == "12345"
        assert runs[0].workflow_name == "Build"
        assert runs[0].status == WorkflowStatus.COMPLETED
        assert runs[0].conclusion == WorkflowConclusion.SUCCESS

    def test_fetch_multiple_runs(self):
        """Should fetch multiple workflow runs."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        response_data = {
            "workflow_runs": [
                {
                    "id": 1,
                    "name": "Build 1",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:05:00Z",
                    "run_number": 1,
                    "head_sha": "abc",
                    "head_branch": "main",
                },
                {
                    "id": 2,
                    "name": "Build 2",
                    "status": "completed",
                    "conclusion": "failure",
                    "created_at": "2025-05-03T11:00:00Z",
                    "updated_at": "2025-05-03T11:05:00Z",
                    "run_number": 2,
                    "head_sha": "def",
                    "head_branch": "develop",
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 2
        assert runs[0].conclusion == WorkflowConclusion.SUCCESS
        assert runs[1].conclusion == WorkflowConclusion.FAILURE

    def test_fetch_with_pagination(self):
        """Should handle pagination across multiple pages."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        # First page (30 items = full page)
        page1_data = {
            "workflow_runs": [
                {
                    "id": i,
                    "name": f"Run {i}",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:05:00Z",
                    "run_number": i,
                    "head_sha": f"sha{i}",
                    "head_branch": "main",
                }
                for i in range(1, 31)
            ]
        }

        # Second page (10 items = partial page, triggers stop)
        page2_data = {
            "workflow_runs": [
                {
                    "id": i,
                    "name": f"Run {i}",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:05:00Z",
                    "run_number": i,
                    "head_sha": f"sha{i}",
                    "head_branch": "main",
                }
                for i in range(31, 41)
            ]
        }

        mock_responses = [
            MagicMock(status_code=200, json=MagicMock(return_value=page1_data)),
            MagicMock(status_code=200, json=MagicMock(return_value=page2_data)),
        ]

        with patch("src.services.github_api_fetcher.requests.get", side_effect=mock_responses):
            runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 40

    def test_fetch_with_filters(self):
        """Should apply status, branch, and created_after filters."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        response_data = {"workflow_runs": []}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        created_after = datetime(2025, 5, 1, 0, 0, 0, tzinfo=timezone.utc)

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response) as mock_get:
            fetcher.fetch_runs(
                "owner",
                "repo",
                status="completed",
                branch="main",
                created_after=created_after,
            )

        # Check that request was made with filter parameters
        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        assert params["status"] == "completed"
        assert params["branch"] == "main"
        assert "created" in params
        assert ">=" in params["created"]

    def test_fetch_empty_result(self):
        """Should return empty list when no runs found."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        assert len(runs) == 0


class TestGitHubAPIFetcherErrorHandling:
    """Test error handling in API fetcher."""

    def test_auth_error_on_401_response(self):
        """Should raise GitHubAuthError on 401 Unauthorized."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            with pytest.raises(GitHubAuthError):
                fetcher.fetch_runs("owner", "repo")

    def test_rate_limit_error_on_403_with_zero_remaining(self):
        """Should raise GitHubRateLimitError when rate limit remaining is 0."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_response.text = "Forbidden"

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            with pytest.raises(GitHubRateLimitError):
                fetcher.fetch_runs("owner", "repo")

    def test_api_error_on_403_with_remaining_requests(self):
        """Should raise GitHubAPIError on 403 with remaining requests."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "50"}
        mock_response.text = "Forbidden: insufficient permissions"

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            with pytest.raises(GitHubAPIError) as exc_info:
                fetcher.fetch_runs("owner", "repo")
            assert "403 Forbidden" in str(exc_info.value)

    def test_api_error_on_404_response(self):
        """Should raise GitHubAPIError on 404 Not Found."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            with pytest.raises(GitHubAPIError) as exc_info:
                fetcher.fetch_runs("owner", "repo")
            assert "Repository not found" in str(exc_info.value)

    def test_network_error_on_connection_error(self):
        """Should raise GitHubNetworkError on connection failure."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("src.services.github_api_fetcher.requests.get", side_effect=requests.ConnectionError("Connection failed")):
            with pytest.raises(GitHubNetworkError):
                fetcher.fetch_runs("owner", "repo")

    def test_network_error_on_timeout(self):
        """Should raise GitHubNetworkError on request timeout."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        with patch("src.services.github_api_fetcher.requests.get", side_effect=requests.Timeout("Request timed out")):
            with pytest.raises(GitHubNetworkError):
                fetcher.fetch_runs("owner", "repo")

    def test_skip_malformed_record_and_continue(self):
        """Should skip malformed records and continue with valid ones."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        response_data = {
            "workflow_runs": [
                {
                    "id": 1,
                    "name": "Run 1",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:05:00Z",
                    "run_number": 1,
                    "head_sha": "abc",
                    "head_branch": "main",
                },
                {
                    # Missing required field 'name'
                    "id": 2,
                    "status": "completed",
                    "created_at": "2025-05-03T11:00:00Z",
                    "head_branch": "main",
                },
                {
                    "id": 3,
                    "name": "Run 3",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2025-05-03T12:00:00Z",
                    "updated_at": "2025-05-03T12:05:00Z",
                    "run_number": 3,
                    "head_sha": "def",
                    "head_branch": "main",
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        # Should have 2 valid runs (indices 0 and 2)
        assert len(runs) == 2
        assert runs[0].id == "1"
        assert runs[1].id == "3"


class TestGitHubAPIFetcherRequestConstruction:
    """Test HTTP request construction."""

    def test_correct_url_formed(self):
        """Should form correct GitHub API URL."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response) as mock_get:
            fetcher.fetch_runs("myowner", "myrepo")

        call_args = mock_get.call_args
        assert "https://api.github.com/repos/myowner/myrepo/actions/runs" == call_args[0][0]

    def test_headers_sent_with_request(self):
        """Should send authorization headers."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response) as mock_get:
            fetcher.fetch_runs("owner", "repo")

        call_args = mock_get.call_args
        headers = call_args.kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("token ghp_")

    def test_timeout_applied_to_request(self):
        """Should apply timeout to requests."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response) as mock_get:
            fetcher.fetch_runs("owner", "repo")

        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 10


class TestGitHubAPIFetcherFieldConversion:
    """Test conversion of GitHub API fields to WorkflowRun."""

    def test_all_fields_converted(self):
        """All GitHub API fields should be converted to WorkflowRun attributes."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        response_data = {
            "workflow_runs": [
                {
                    "id": 54321,
                    "name": "Test Workflow",
                    "status": "in_progress",
                    "conclusion": None,
                    "created_at": "2025-05-03T10:00:00Z",
                    "updated_at": "2025-05-03T10:10:00Z",
                    "run_number": 42,
                    "head_sha": "abc123def456",
                    "head_branch": "feature/test",
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        run = runs[0]
        assert run.id == "54321"
        assert run.workflow_name == "Test Workflow"
        assert run.status == WorkflowStatus.IN_PROGRESS
        assert run.conclusion is None
        assert run.run_number == 42
        assert run.commit_sha == "abc123def456"
        assert run.branch == "feature/test"

    def test_missing_optional_fields(self):
        """Should handle missing optional fields gracefully."""
        fetcher = GitHubAPIFetcher("ghp_test_token_12345678901234567890")

        response_data = {
            "workflow_runs": [
                {
                    "id": 1,
                    "name": "Workflow",
                    "status": "completed",
                    # No conclusion
                    "created_at": "2025-05-03T10:00:00Z",
                    # No updated_at
                    # No run_number
                    # No head_sha
                    "head_branch": "main",
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("src.services.github_api_fetcher.requests.get", return_value=mock_response):
            runs = fetcher.fetch_runs("owner", "repo")

        run = runs[0]
        assert run.conclusion is None
        assert run.updated_at is None
        assert run.run_number is None
        assert run.commit_sha is None
