import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_statistics_service import WorkflowStatisticsService


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    run_number: int = 1,
    commit_sha: str = "abc123",
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=run_number,
        commit_sha=commit_sha,
    )


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    return WorkflowStatisticsService()


class TestCountByConclusion:
    def test_empty_runs(self, service):
        stats = service.compute_statistics([], [])
        assert stats.count_by_conclusion == {}

    def test_single_run_with_conclusion(self, service):
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
        stats = service.compute_statistics([run], [])
        assert stats.count_by_conclusion == {"success": 1}

    def test_multiple_runs_same_conclusion(self, service):
        run1 = _make_run(run_id="run-1", conclusion=WorkflowConclusion.SUCCESS)
        run2 = _make_run(run_id="run-2", conclusion=WorkflowConclusion.SUCCESS)
        stats = service.compute_statistics([run1, run2], [])
        assert stats.count_by_conclusion == {"success": 2}

    def test_multiple_runs_different_conclusions(self, service):
        run1 = _make_run(run_id="run-1", conclusion=WorkflowConclusion.SUCCESS)
        run2 = _make_run(run_id="run-2", conclusion=WorkflowConclusion.FAILURE)
        run3 = _make_run(run_id="run-3", conclusion=WorkflowConclusion.CANCELLED)
        stats = service.compute_statistics([run1, run2, run3], [])
        assert stats.count_by_conclusion == {
            "success": 1,
            "failure": 1,
            "cancelled": 1,
        }

    def test_runs_without_conclusion(self, service):
        run = _make_run(conclusion=None)
        stats = service.compute_statistics([run], [])
        assert stats.count_by_conclusion == {}


class TestDurationStatistics:
    def test_no_runs_with_duration(self, service):
        run = _make_run(updated_at=None)
        stats = service.compute_statistics([run], [])
        assert stats.average_duration_seconds == 0.0
        assert stats.min_duration_seconds is None
        assert stats.max_duration_seconds is None

    def test_single_run_with_duration(self, service):
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
        run = _make_run(created_at=created, updated_at=updated)
        stats = service.compute_statistics([run], [])
        assert stats.average_duration_seconds == 60.0
        assert stats.min_duration_seconds == 60.0
        assert stats.max_duration_seconds == 60.0

    def test_multiple_runs_with_different_durations(self, service):
        created1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated1 = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)  # 60 seconds
        run1 = _make_run(run_id="run-1", created_at=created1, updated_at=updated1)

        created2 = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        updated2 = datetime(2024, 1, 1, 13, 2, 0, tzinfo=timezone.utc)  # 120 seconds
        run2 = _make_run(run_id="run-2", created_at=created2, updated_at=updated2)

        stats = service.compute_statistics([run1, run2], [])
        assert stats.average_duration_seconds == 90.0
        assert stats.min_duration_seconds == 60.0
        assert stats.max_duration_seconds == 120.0

    def test_mixed_runs_with_and_without_duration(self, service):
        created1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated1 = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)  # 60 seconds
        run1 = _make_run(run_id="run-1", created_at=created1, updated_at=updated1)

        run2 = _make_run(run_id="run-2", updated_at=None)  # no duration

        stats = service.compute_statistics([run1, run2], [])
        assert stats.average_duration_seconds == 60.0
        assert stats.min_duration_seconds == 60.0
        assert stats.max_duration_seconds == 60.0


class TestAverageAttemptsPerRun:
    def test_no_runs_no_attempts(self, service):
        stats = service.compute_statistics([], [])
        assert stats.average_attempts_per_run == 0.0

    def test_runs_with_no_attempts(self, service):
        run1 = _make_run(run_id="run-1")
        run2 = _make_run(run_id="run-2")
        stats = service.compute_statistics([run1, run2], [])
        assert stats.average_attempts_per_run == 0.0

    def test_runs_with_one_attempt_each(self, service):
        run1 = _make_run(run_id="1")
        run2 = _make_run(run_id="2")
        attempt1 = _make_attempt(attempt_id=1, run_id=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=2)
        stats = service.compute_statistics([run1, run2], [attempt1, attempt2])
        assert stats.average_attempts_per_run == 1.0

    def test_runs_with_multiple_attempts(self, service):
        run1 = _make_run(run_id="1")
        run2 = _make_run(run_id="2")
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=1, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=2, attempt_number=1)
        stats = service.compute_statistics([run1, run2], [attempt1, attempt2, attempt3])
        # Total attempts: 3, total runs: 2, average: 1.5
        assert stats.average_attempts_per_run == 1.5

    def test_mixed_runs_with_different_attempt_counts(self, service):
        run1 = _make_run(run_id="1")
        run2 = _make_run(run_id="2")
        run3 = _make_run(run_id="3")
        # run-1: 3 attempts
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=1, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=1, attempt_number=3)
        # run-2: 1 attempt
        attempt4 = _make_attempt(attempt_id=4, run_id=2, attempt_number=1)
        # run-3: 0 attempts
        stats = service.compute_statistics(
            [run1, run2, run3],
            [attempt1, attempt2, attempt3, attempt4]
        )
        # Total attempts: 4, total runs: 3, average: 1.333...
        assert stats.average_attempts_per_run == pytest.approx(4.0 / 3.0, rel=1e-2)


class TestPerStatusBreakdown:
    def test_no_runs_with_duration(self, service):
        run = _make_run(status=WorkflowStatus.COMPLETED, updated_at=None)
        stats = service.compute_statistics([run], [])
        assert stats.per_status_breakdown == {}

    def test_single_status_single_run(self, service):
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
        run = _make_run(status=WorkflowStatus.COMPLETED, created_at=created, updated_at=updated)
        stats = service.compute_statistics([run], [])
        assert stats.per_status_breakdown == {"completed": 60.0}

    def test_multiple_statuses_with_different_durations(self, service):
        created1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated1 = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)  # 60 seconds
        run1 = _make_run(
            run_id="run-1",
            status=WorkflowStatus.COMPLETED,
            created_at=created1,
            updated_at=updated1
        )

        created2 = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        updated2 = datetime(2024, 1, 1, 13, 2, 0, tzinfo=timezone.utc)  # 120 seconds
        run2 = _make_run(
            run_id="run-2",
            status=WorkflowStatus.IN_PROGRESS,
            created_at=created2,
            updated_at=updated2
        )

        stats = service.compute_statistics([run1, run2], [])
        assert stats.per_status_breakdown == {
            "completed": 60.0,
            "in_progress": 120.0,
        }

    def test_same_status_multiple_runs(self, service):
        created1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated1 = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)  # 60 seconds
        run1 = _make_run(
            run_id="run-1",
            status=WorkflowStatus.COMPLETED,
            created_at=created1,
            updated_at=updated1
        )

        created2 = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        updated2 = datetime(2024, 1, 1, 13, 3, 0, tzinfo=timezone.utc)  # 180 seconds
        run2 = _make_run(
            run_id="run-2",
            status=WorkflowStatus.COMPLETED,
            created_at=created2,
            updated_at=updated2
        )

        stats = service.compute_statistics([run1, run2], [])
        # Average of 60 and 180 is 120
        assert stats.per_status_breakdown == {"completed": 120.0}


class TestWorkflowRunStatisticsDataclass:
    def test_to_dict(self, service):
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
        stats = service.compute_statistics([run], [])
        stats_dict = stats.to_dict()
        assert isinstance(stats_dict, dict)
        assert "count_by_conclusion" in stats_dict
        assert "average_duration_seconds" in stats_dict
        assert "min_duration_seconds" in stats_dict
        assert "max_duration_seconds" in stats_dict
        assert "average_attempts_per_run" in stats_dict
        assert "per_status_breakdown" in stats_dict

    def test_dataclass_fields(self, service):
        stats = service.compute_statistics([], [])
        assert hasattr(stats, "count_by_conclusion")
        assert hasattr(stats, "average_duration_seconds")
        assert hasattr(stats, "min_duration_seconds")
        assert hasattr(stats, "max_duration_seconds")
        assert hasattr(stats, "average_attempts_per_run")
        assert hasattr(stats, "per_status_breakdown")
