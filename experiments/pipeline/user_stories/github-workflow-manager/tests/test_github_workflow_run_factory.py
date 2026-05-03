"""Tests for GitHub API response to WorkflowRun conversion."""

import pytest
from datetime import datetime, timezone, timedelta

from src.models.github_workflow_run_factory import GitHubWorkflowRunFactory
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


class TestGitHubWorkflowRunFactoryBasicConversion:
    """Test basic conversion of GitHub API response to WorkflowRun."""

    def test_basic_conversion(self):
        """Should convert basic GitHub API response to WorkflowRun."""
        api_response = {
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

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert isinstance(run, WorkflowRun)
        assert run.id == "12345"
        assert run.workflow_name == "Build"
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS
        assert run.run_number == 1
        assert run.commit_sha == "abc123"
        assert run.branch == "main"

    def test_id_converted_to_string(self):
        """GitHub API returns ID as int; should be converted to string."""
        api_response = {
            "id": 999,
            "name": "Test",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": "2025-05-03T10:05:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert isinstance(run.id, str)
        assert run.id == "999"

    def test_required_fields_must_be_present(self):
        """Should raise KeyError when required fields are missing."""
        # Missing 'name'
        api_response = {
            "id": 1,
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        with pytest.raises(KeyError):
            GitHubWorkflowRunFactory.from_github_api_response(api_response)


class TestGitHubWorkflowRunFactoryStatusParsing:
    """Test workflow status enum conversion."""

    @pytest.mark.parametrize("status_str,expected_enum", [
        ("queued", WorkflowStatus.QUEUED),
        ("in_progress", WorkflowStatus.IN_PROGRESS),
        ("completed", WorkflowStatus.COMPLETED),
        ("waiting", WorkflowStatus.WAITING),
        ("requested", WorkflowStatus.REQUESTED),
        ("pending", WorkflowStatus.PENDING),
    ])
    def test_status_conversion_valid(self, status_str, expected_enum):
        """Should convert valid status strings to enum."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": status_str,
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.status == expected_enum

    def test_status_case_insensitive(self):
        """Status conversion should be case-insensitive."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "COMPLETED",  # Uppercase
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.status == WorkflowStatus.COMPLETED

    def test_invalid_status_raises_error(self):
        """Should raise ValueError on invalid status."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "invalid_status",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        with pytest.raises(ValueError) as exc_info:
            GitHubWorkflowRunFactory.from_github_api_response(api_response)
        assert "Unknown workflow status" in str(exc_info.value)


class TestGitHubWorkflowRunFactoryConclusionParsing:
    """Test workflow conclusion enum conversion."""

    @pytest.mark.parametrize("conclusion_str,expected_enum", [
        ("success", WorkflowConclusion.SUCCESS),
        ("failure", WorkflowConclusion.FAILURE),
        ("cancelled", WorkflowConclusion.CANCELLED),
        ("skipped", WorkflowConclusion.SKIPPED),
        ("timed_out", WorkflowConclusion.TIMED_OUT),
        ("action_required", WorkflowConclusion.ACTION_REQUIRED),
        ("neutral", WorkflowConclusion.NEUTRAL),
        ("stale", WorkflowConclusion.STALE),
    ])
    def test_conclusion_conversion_valid(self, conclusion_str, expected_enum):
        """Should convert valid conclusion strings to enum."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "conclusion": conclusion_str,
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.conclusion == expected_enum

    def test_conclusion_none_when_missing(self):
        """Conclusion should be None when not provided."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "in_progress",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.conclusion is None

    def test_conclusion_none_when_null(self):
        """Conclusion should be None when explicitly null."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.conclusion is None

    def test_conclusion_case_insensitive(self):
        """Conclusion conversion should be case-insensitive."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "conclusion": "SUCCESS",  # Uppercase
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.conclusion == WorkflowConclusion.SUCCESS

    def test_invalid_conclusion_raises_error(self):
        """Should raise ValueError on invalid conclusion."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "conclusion": "invalid_conclusion",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        with pytest.raises(ValueError) as exc_info:
            GitHubWorkflowRunFactory.from_github_api_response(api_response)
        assert "Unknown workflow conclusion" in str(exc_info.value)


class TestGitHubWorkflowRunFactoryDatetimeParsing:
    """Test ISO 8601 datetime parsing."""

    def test_datetime_parsing_iso_format_z_suffix(self):
        """Should parse ISO 8601 datetime with Z suffix."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:30:45Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert isinstance(run.created_at, datetime)
        assert run.created_at.year == 2025
        assert run.created_at.month == 5
        assert run.created_at.day == 3
        assert run.created_at.hour == 10
        assert run.created_at.minute == 30
        assert run.created_at.second == 45

    def test_datetime_parsing_preserves_timezone(self):
        """Should preserve timezone info from datetime."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.created_at.tzinfo is not None
        assert run.created_at.tzinfo.utcoffset(run.created_at) == timedelta(0)

    def test_updated_at_parsing(self):
        """Should parse updated_at datetime when present."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": "2025-05-03T10:05:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.updated_at is not None
        assert run.updated_at.hour == 10
        assert run.updated_at.minute == 5

    def test_updated_at_none_when_missing(self):
        """updated_at should be None when not provided."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "in_progress",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.updated_at is None

    def test_invalid_datetime_raises_error(self):
        """Should raise ValueError on invalid datetime format."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "not-a-date",
            "head_branch": "main",
        }

        with pytest.raises(ValueError) as exc_info:
            GitHubWorkflowRunFactory.from_github_api_response(api_response)
        assert "Could not parse datetime" in str(exc_info.value)


class TestGitHubWorkflowRunFactoryDurationCalculation:
    """Test duration calculation from timestamps."""

    def test_duration_calculated_from_timestamps(self):
        """Should calculate duration as (updated_at - created_at)."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": "2025-05-03T10:05:30Z",  # 5 minutes 30 seconds = 330 seconds
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds == 330.0

    def test_duration_zero_when_updated_at_missing(self):
        """Duration should be 0.0 when updated_at is missing."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "in_progress",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds == 0.0

    def test_duration_zero_when_updated_at_none(self):
        """Duration should be 0.0 when updated_at is None."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "in_progress",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": None,
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds == 0.0

    def test_duration_zero_on_negative_duration(self):
        """Duration should be 0.0 if calculated as negative (clock skew)."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": "2025-05-03T09:55:00Z",  # Before created_at (clock skew)
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds == 0.0

    def test_duration_handles_seconds_with_microseconds(self):
        """Should handle datetime with microseconds in calculation."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00.000000Z",
            "updated_at": "2025-05-03T10:01:30.500000Z",  # 1 min 30.5 sec
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds == 90.5


class TestGitHubWorkflowRunFactoryOptionalFields:
    """Test handling of optional fields."""

    def test_optional_run_number(self):
        """run_number should be optional and None when missing."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.run_number is None

    def test_optional_head_sha(self):
        """head_sha (commit_sha) should be optional and None when missing."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.commit_sha is None

    def test_all_optional_fields_present(self):
        """Should include all optional fields when present."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2025-05-03T10:00:00Z",
            "updated_at": "2025-05-03T10:05:00Z",
            "run_number": 42,
            "head_sha": "abc123def456",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.run_number == 42
        assert run.commit_sha == "abc123def456"
        assert run.updated_at is not None
        assert run.conclusion == WorkflowConclusion.SUCCESS


class TestGitHubWorkflowRunFactoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_name_string(self):
        """Should handle empty workflow name."""
        api_response = {
            "id": 1,
            "name": "",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.workflow_name == ""

    def test_special_characters_in_branch_name(self):
        """Should handle special characters in branch name."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "feature/JIRA-123-special_chars",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.branch == "feature/JIRA-123-special_chars"

    def test_very_large_id(self):
        """Should handle very large GitHub API IDs."""
        api_response = {
            "id": 9999999999999999,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.id == "9999999999999999"

    def test_run_number_zero(self):
        """Should handle run_number of 0."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2025-05-03T10:00:00Z",
            "run_number": 0,
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.run_number == 0

    def test_duration_very_large(self):
        """Should handle very large duration (old runs)."""
        api_response = {
            "id": 1,
            "name": "Test",
            "status": "completed",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2025-05-03T10:00:00Z",  # ~2000 days
            "head_branch": "main",
        }

        run = GitHubWorkflowRunFactory.from_github_api_response(api_response)

        assert run.duration_seconds > 0
        assert run.duration_seconds == run.updated_at.timestamp() - run.created_at.timestamp()
