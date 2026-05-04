import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import json

from src.services.github_fetch_service import GitHubFetchService
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


@pytest.fixture
def service():
    return GitHubFetchService()


def test_map_github_status(service):
    """Test GitHub API status to WorkflowStatus mapping."""
    assert service._map_github_status("queued") == WorkflowStatus.QUEUED
    assert service._map_github_status("in_progress") == WorkflowStatus.IN_PROGRESS
    assert service._map_github_status("completed") == WorkflowStatus.COMPLETED
    assert service._map_github_status("unknown") == WorkflowStatus.COMPLETED  # default


def test_map_github_conclusion(service):
    """Test GitHub API conclusion to WorkflowConclusion mapping."""
    assert service._map_github_conclusion("success") == WorkflowConclusion.SUCCESS
    assert service._map_github_conclusion("failure") == WorkflowConclusion.FAILURE
    assert service._map_github_conclusion("cancelled") == WorkflowConclusion.CANCELLED
    assert service._map_github_conclusion("timed_out") == WorkflowConclusion.TIMED_OUT
    assert service._map_github_conclusion(None) is None
    assert service._map_github_conclusion("") is None


def test_parse_iso_datetime(service):
    """Test ISO 8601 datetime parsing."""
    # GitHub format with Z suffix
    dt = service._parse_iso_datetime("2024-01-15T10:30:45Z")
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 10
    assert dt.minute == 30
    assert dt.second == 45
    assert dt.tzinfo is not None

    # Standard ISO format
    dt2 = service._parse_iso_datetime("2024-01-15T10:30:45+00:00")
    assert dt2.year == 2024


def test_convert_github_run_to_workflow_run(service):
    """Test conversion of GitHub API run to WorkflowRun model."""
    github_run = {
        "id": 12345,
        "name": "CI",
        "head_branch": "main",
        "status": "completed",
        "conclusion": "success",
        "run_number": 42,
        "created_at": "2024-01-15T10:30:45Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "head_sha": "abc123def456",
    }

    run = service._convert_github_run_to_workflow_run(github_run, "CI")

    assert run.id == "12345"
    assert run.workflow_name == "CI"
    assert run.branch == "main"
    assert run.status == WorkflowStatus.COMPLETED
    assert run.conclusion == WorkflowConclusion.SUCCESS
    assert run.run_number == 42
    assert run.commit_sha == "abc123def456"
    assert run.created_at.year == 2024


def test_resolve_token_from_env(service):
    """Test token resolution from environment variable."""
    with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test123"}):
        token = service._resolve_token()
        assert token == "ghp_test123"


def test_resolve_token_from_secrets_env_file(service):
    """Test token resolution from secrets/.env file."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = [
                "GITHUB_TOKEN=ghp_fromsecrets789\n"
            ]
            with patch.dict("os.environ", {}, clear=True):
                token = service._resolve_token()
                assert token == "ghp_fromsecrets789"


def test_resolve_token_prompt_on_missing(service):
    """Test token resolution from getpass when env/file not available."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("pathlib.Path.exists", return_value=False):
            with patch("getpass.getpass", return_value="ghp_fromprompt456"):
                token = service._resolve_token()
                assert token == "ghp_fromprompt456"


def test_resolve_token_raises_when_none(service):
    """Test that ValueError is raised when no token found."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("pathlib.Path.exists", return_value=False):
            with patch("getpass.getpass", return_value=""):
                with pytest.raises(ValueError, match="No GitHub token provided"):
                    service._resolve_token()


@patch("subprocess.run")
def test_check_gh_cli_available(mock_run, service):
    """Test detecting gh CLI availability."""
    mock_run.return_value.returncode = 0
    assert service._check_gh_cli() is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_check_gh_cli_not_available(mock_run, service):
    """Test detecting gh CLI is not available."""
    mock_run.side_effect = FileNotFoundError()
    assert service._check_gh_cli() is False


@patch("subprocess.run")
def test_validate_token_with_gh_cli(mock_run, service):
    """Test token validation using gh CLI."""
    service._use_gh_cli = True
    mock_run.return_value.returncode = 0
    assert service._validate_token("ghp_test") is True


@patch("subprocess.run")
def test_validate_token_with_gh_cli_fails(mock_run, service):
    """Test token validation failure with gh CLI."""
    service._use_gh_cli = True
    mock_run.return_value.returncode = 1
    assert service._validate_token("ghp_invalid") is False


@patch("subprocess.run")
def test_fetch_with_gh_cli_success(mock_run, service):
    """Test successful fetch using gh CLI."""
    service._use_gh_cli = True

    github_response = {
        "workflow_runs": [
            {
                "id": 111,
                "name": "Tests",
                "head_branch": "develop",
                "status": "completed",
                "conclusion": "success",
                "run_number": 10,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:05:00Z",
                "head_sha": "sha111",
            },
        ]
    }

    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = json.dumps(github_response)

    runs = service._fetch_with_gh_cli("owner", "repo", token="ghp_test")

    assert len(runs) == 1
    assert runs[0].id == "111"
    assert runs[0].workflow_name == "Tests"
    assert runs[0].status == WorkflowStatus.COMPLETED


@patch("subprocess.run")
def test_fetch_with_gh_cli_unauthorized(mock_run, service):
    """Test fetch with gh CLI when token is invalid."""
    service._use_gh_cli = True
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "401 Unauthorized"

    with pytest.raises(ValueError, match="Invalid GitHub token"):
        service._fetch_with_gh_cli("owner", "repo", token="ghp_invalid")


@patch("src.adapters.github_adapter.requests")
def test_fetch_with_requests_success(mock_requests, service):
    """Test successful fetch using requests library."""
    service._use_gh_cli = False

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_runs": [
            {
                "id": 222,
                "name": "Linter",
                "head_branch": "feature-x",
                "status": "in_progress",
                "conclusion": None,
                "run_number": 5,
                "created_at": "2024-01-15T11:00:00Z",
                "updated_at": "2024-01-15T11:01:00Z",
                "head_sha": "sha222",
            },
        ]
    }
    mock_requests.get.return_value = mock_response

    runs = service._fetch_with_requests("owner", "repo", token="ghp_test")

    assert len(runs) == 1
    assert runs[0].id == "222"
    assert runs[0].status == WorkflowStatus.IN_PROGRESS
    assert runs[0].conclusion is None


@patch("src.adapters.github_adapter.requests")
def test_fetch_with_requests_unauthorized(mock_requests, service):
    """Test fetch with requests when token is invalid."""
    service._use_gh_cli = False

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_requests.get.return_value = mock_response

    with pytest.raises(ValueError, match="Invalid GitHub token"):
        service._fetch_with_requests("owner", "repo", token="ghp_invalid")


@patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_env"})
def test_fetch_workflow_runs_uses_token_from_env(service):
    """Test that fetch_workflow_runs uses token from environment."""
    service._check_gh_cli = MagicMock(return_value=False)
    service._fetch_with_requests = MagicMock(return_value=[])

    service.fetch_workflow_runs("owner", "repo", validate=False)
    service._fetch_with_requests.assert_called()


def test_fetch_incremental_with_no_prior_runs(service):
    """Test incremental fetch returns all runs when no prior runs exist."""
    mock_runs = [
        WorkflowRun(
            id="1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="sha1",
        ),
    ]

    service.fetch_workflow_runs = MagicMock(return_value=mock_runs)

    result = service.fetch_incremental("owner", "repo", latest_run_timestamp=None, token="ghp_test")

    assert len(result) == 1
    assert result[0].id == "1"


def test_fetch_incremental_filters_older_runs(service):
    """Test incremental fetch filters out runs older than latest timestamp."""
    now = datetime.now(timezone.utc)
    old_run = WorkflowRun(
        id="1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="sha1",
    )
    new_run = WorkflowRun(
        id="2",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 20, tzinfo=timezone.utc),
        updated_at=None,
        run_number=2,
        commit_sha="sha2",
    )

    service.fetch_workflow_runs = MagicMock(return_value=[old_run, new_run])

    latest = datetime(2024, 1, 15, tzinfo=timezone.utc)
    result = service.fetch_incremental("owner", "repo", latest_run_timestamp=latest, token="ghp_test")

    assert len(result) == 1
    assert result[0].id == "2"
