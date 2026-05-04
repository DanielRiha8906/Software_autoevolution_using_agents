"""Tests for WorkflowFetcher protocol."""

import pytest
from typing import Optional, List
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.adapters.github.base import WorkflowFetcher


def _make_run(run_id: str = "run-1") -> WorkflowRun:
    """Create a test WorkflowRun."""
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


class TestWorkflowFetcherProtocol:
    """Tests for WorkflowFetcher protocol implementation."""

    def test_protocol_is_protocol(self):
        """WorkflowFetcher is a Protocol."""
        from typing import Protocol
        assert hasattr(WorkflowFetcher, "__protocol_attrs__") or hasattr(WorkflowFetcher, "_is_protocol")

    def test_protocol_has_fetch_runs_method(self):
        """WorkflowFetcher protocol requires fetch_runs method."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        fetcher.fetch_runs.return_value = []
        result = fetcher.fetch_runs("owner", "repo")
        assert result == []

    def test_fetch_runs_with_owner_and_repo(self):
        """fetch_runs accepts owner and repo as positional arguments."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("myorg", "myrepo")
        fetcher.fetch_runs.assert_called_once_with("myorg", "myrepo")
        assert len(result) == 1

    def test_fetch_runs_with_status_filter(self):
        """fetch_runs accepts optional status parameter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", status="completed")
        fetcher.fetch_runs.assert_called_once_with("owner", "repo", status="completed")
        assert len(result) == 1

    def test_fetch_runs_with_branch_filter(self):
        """fetch_runs accepts optional branch parameter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", branch="main")
        fetcher.fetch_runs.assert_called_once_with("owner", "repo", branch="main")
        assert len(result) == 1

    def test_fetch_runs_with_created_after_filter(self):
        """fetch_runs accepts optional created_after parameter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        now = datetime.now(timezone.utc)
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", created_after=now)
        fetcher.fetch_runs.assert_called_once_with("owner", "repo", created_after=now)
        assert len(result) == 1

    def test_fetch_runs_with_all_parameters(self):
        """fetch_runs accepts all optional parameters together."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        now = datetime.now(timezone.utc)
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs(
            "owner",
            "repo",
            status="completed",
            branch="main",
            created_after=now
        )
        fetcher.fetch_runs.assert_called_once_with(
            "owner",
            "repo",
            status="completed",
            branch="main",
            created_after=now
        )
        assert len(result) == 1

    def test_fetch_runs_returns_empty_list(self):
        """fetch_runs can return an empty list."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        fetcher.fetch_runs.return_value = []
        result = fetcher.fetch_runs("owner", "repo")
        assert result == []
        assert isinstance(result, list)

    def test_fetch_runs_returns_multiple_runs(self):
        """fetch_runs can return multiple runs."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        runs = [_make_run(f"run-{i}") for i in range(5)]
        fetcher.fetch_runs.return_value = runs
        result = fetcher.fetch_runs("owner", "repo")
        assert len(result) == 5
        assert all(isinstance(r, WorkflowRun) for r in result)

    def test_fetch_runs_with_none_status(self):
        """fetch_runs with status=None is equivalent to no status filter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", status=None)
        assert len(result) == 1

    def test_fetch_runs_with_none_branch(self):
        """fetch_runs with branch=None is equivalent to no branch filter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", branch=None)
        assert len(result) == 1

    def test_fetch_runs_with_none_created_after(self):
        """fetch_runs with created_after=None is equivalent to no date filter."""
        fetcher = MagicMock(spec=WorkflowFetcher)
        run = _make_run()
        fetcher.fetch_runs.return_value = [run]
        result = fetcher.fetch_runs("owner", "repo", created_after=None)
        assert len(result) == 1


class TestWorkflowFetcherDuckTyping:
    """Tests for duck typing with WorkflowFetcher protocol."""

    def test_workflow_fetcher_duck_typing(self):
        """Any object with fetch_runs method satisfies WorkflowFetcher protocol."""
        class CustomFetcher:
            def fetch_runs(
                self,
                owner: str,
                repo: str,
                status: Optional[str] = None,
                branch: Optional[str] = None,
                created_after: Optional[datetime] = None,
            ) -> List[WorkflowRun]:
                return []

        fetcher = CustomFetcher()
        # Duck typing: if it has the method with right signature, it works
        assert hasattr(fetcher, "fetch_runs")
        result = fetcher.fetch_runs("owner", "repo")
        assert result == []

    def test_custom_fetcher_with_all_params(self):
        """Custom fetcher implementation can use all parameters."""
        class CustomFetcher:
            def fetch_runs(
                self,
                owner: str,
                repo: str,
                status: Optional[str] = None,
                branch: Optional[str] = None,
                created_after: Optional[datetime] = None,
            ) -> List[WorkflowRun]:
                runs = [_make_run("run-1")]
                if status:
                    runs = [r for r in runs if str(r.status.value) == status]
                if branch:
                    runs = [r for r in runs if r.branch == branch]
                return runs

        fetcher = CustomFetcher()
        result = fetcher.fetch_runs("owner", "repo", status="completed", branch="main")
        assert len(result) == 1
        assert result[0].id == "run-1"
