import pytest
from unittest.mock import patch, MagicMock

from src.integrations.github_fetch_service import GitHubFetchService
from src.models.workflow_run import WorkflowRun


def test_service_exists():
    assert GitHubFetchService() is not None


def test_resolves_token_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    svc = GitHubFetchService()
    assert svc.resolve_token() == "test-token"


def test_resolves_token_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("GITHUB_TOKEN=file-token\n")
    svc = GitHubFetchService(secrets_path=str(env_file))
    assert svc.resolve_token() == "file-token"


def test_prompts_user_for_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: "user-token")
    svc = GitHubFetchService()
    assert svc.resolve_token() == "user-token"


def test_user_token_not_persisted(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: "user-token")
    env_file = tmp_path / ".env"
    svc = GitHubFetchService(secrets_path=str(env_file))
    svc.resolve_token()
    if env_file.exists():
        assert "user-token" not in env_file.read_text()


def test_fetch_uses_gh_cli(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    fake_output = '''
    {
        "workflow_runs": [
            {
                "id": 1,
                "name": "CI",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": null,
                "run_number": 1,
                "head_sha": "abc123"
            }
        ]
    }
    '''
    mock_completed = MagicMock()
    mock_completed.stdout = fake_output
    mock_completed.returncode = 0
    with patch("subprocess.run", return_value=mock_completed):
        svc = GitHubFetchService()
        runs = svc.fetch("owner", "repo")
        assert len(runs) == 1
        assert isinstance(runs[0], WorkflowRun)


def test_gh_cli_failure_raises(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    mock_completed = MagicMock()
    mock_completed.returncode = 1
    mock_completed.stderr = "error"
    with patch("subprocess.run", return_value=mock_completed):
        svc = GitHubFetchService()
        with pytest.raises(Exception):
            svc.fetch("owner", "repo")


def test_no_requests_usage():
    from src.integrations import github_fetch_service
    import inspect
    source = inspect.getsource(github_fetch_service)
    assert "requests" not in source
