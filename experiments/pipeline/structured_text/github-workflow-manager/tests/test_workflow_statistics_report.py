"""Tests for WorkflowStatisticsReport dataclass and serialization."""

import pytest
from datetime import datetime
from src.models.workflow_statistics_report import WorkflowStatisticsReport


class TestWorkflowStatisticsReportDataclass:
    """Test WorkflowStatisticsReport dataclass construction and field validation."""

    def test_create_report_with_valid_data(self):
        """Test creating a report with all valid data."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=10,
            conclusion_counts={"success": 5, "failure": 3, None: 2},
            average_duration_seconds=45.5,
            min_duration_seconds=5.0,
            max_duration_seconds=120.0,
            duration_by_conclusion={"success": 40.0, "failure": 55.0, None: 30.0},
            total_attempts=20,
            average_attempts_per_run=2.0,
            runs_with_no_attempts=2,
            runs_with_attempts=8,
            generated_at=now,
        )

        assert report.total_runs == 10
        assert report.average_duration_seconds == 45.5
        assert report.min_duration_seconds == 5.0
        assert report.max_duration_seconds == 120.0
        assert report.total_attempts == 20
        assert report.average_attempts_per_run == 2.0
        assert report.runs_with_no_attempts == 2
        assert report.runs_with_attempts == 8
        assert report.generated_at == now

    def test_create_report_with_zero_runs(self):
        """Test creating a report with zero runs (edge case)."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=0,
            conclusion_counts={},
            average_duration_seconds=0.0,
            min_duration_seconds=None,
            max_duration_seconds=None,
            duration_by_conclusion={},
            total_attempts=0,
            average_attempts_per_run=0.0,
            runs_with_no_attempts=0,
            runs_with_attempts=0,
            generated_at=now,
        )

        assert report.total_runs == 0
        assert report.conclusion_counts == {}
        assert report.average_duration_seconds == 0.0

    def test_create_report_with_none_durations(self):
        """Test creating a report with None min/max durations."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=5,
            conclusion_counts={"success": 5},
            average_duration_seconds=50.0,
            min_duration_seconds=None,
            max_duration_seconds=None,
            duration_by_conclusion={"success": 50.0},
            total_attempts=10,
            average_attempts_per_run=2.0,
            runs_with_no_attempts=0,
            runs_with_attempts=5,
            generated_at=now,
        )

        assert report.min_duration_seconds is None
        assert report.max_duration_seconds is None

    def test_create_report_with_single_run(self):
        """Test creating a report with a single run."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=1,
            conclusion_counts={"success": 1},
            average_duration_seconds=100.0,
            min_duration_seconds=100.0,
            max_duration_seconds=100.0,
            duration_by_conclusion={"success": 100.0},
            total_attempts=1,
            average_attempts_per_run=1.0,
            runs_with_no_attempts=0,
            runs_with_attempts=1,
            generated_at=now,
        )

        assert report.total_runs == 1
        assert report.min_duration_seconds == report.max_duration_seconds

    def test_conclusion_counts_with_none_key(self):
        """Test that conclusion_counts correctly handles None key for incomplete runs."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=3,
            conclusion_counts={"success": 2, None: 1},
            average_duration_seconds=30.0,
            min_duration_seconds=20.0,
            max_duration_seconds=40.0,
            duration_by_conclusion={"success": 35.0, None: 20.0},
            total_attempts=2,
            average_attempts_per_run=0.67,
            runs_with_no_attempts=1,
            runs_with_attempts=2,
            generated_at=now,
        )

        assert None in report.conclusion_counts
        assert report.conclusion_counts[None] == 1


class TestWorkflowStatisticsReportSerialization:
    """Test WorkflowStatisticsReport.to_dict() serialization."""

    def test_to_dict_valid_data(self):
        """Test to_dict() with valid data."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=10,
            conclusion_counts={"success": 5, "failure": 3, None: 2},
            average_duration_seconds=45.5,
            min_duration_seconds=5.0,
            max_duration_seconds=120.0,
            duration_by_conclusion={"success": 40.0, "failure": 55.0, None: 30.0},
            total_attempts=20,
            average_attempts_per_run=2.0,
            runs_with_no_attempts=2,
            runs_with_attempts=8,
            generated_at=now,
        )

        result = report.to_dict()

        assert isinstance(result, dict)
        assert result["total_runs"] == 10
        assert result["average_duration_seconds"] == 45.5
        assert result["min_duration_seconds"] == 5.0
        assert result["max_duration_seconds"] == 120.0
        assert result["total_attempts"] == 20
        assert result["average_attempts_per_run"] == 2.0
        assert result["runs_with_no_attempts"] == 2
        assert result["runs_with_attempts"] == 8

    def test_to_dict_conclusion_counts_serialization(self):
        """Test that conclusion_counts are serialized correctly, with None -> 'incomplete'."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=3,
            conclusion_counts={"success": 2, None: 1},
            average_duration_seconds=50.0,
            min_duration_seconds=40.0,
            max_duration_seconds=60.0,
            duration_by_conclusion={"success": 55.0, None: 40.0},
            total_attempts=3,
            average_attempts_per_run=1.0,
            runs_with_no_attempts=0,
            runs_with_attempts=3,
            generated_at=now,
        )

        result = report.to_dict()
        conclusion_counts = result["conclusion_counts"]

        # None key should be converted to 'incomplete'
        assert "incomplete" in conclusion_counts
        assert conclusion_counts["incomplete"] == 1
        assert conclusion_counts["success"] == 2
        # None should not be present as a string key
        assert None not in conclusion_counts

    def test_to_dict_duration_by_conclusion_serialization(self):
        """Test that duration_by_conclusion are serialized correctly."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=3,
            conclusion_counts={"success": 2, "failure": 1},
            average_duration_seconds=45.0,
            min_duration_seconds=30.0,
            max_duration_seconds=60.0,
            duration_by_conclusion={"success": 40.0, "failure": 60.0},
            total_attempts=3,
            average_attempts_per_run=1.0,
            runs_with_no_attempts=0,
            runs_with_attempts=3,
            generated_at=now,
        )

        result = report.to_dict()
        duration_by_conclusion = result["duration_by_conclusion"]

        assert duration_by_conclusion["success"] == 40.0
        assert duration_by_conclusion["failure"] == 60.0

    def test_to_dict_with_none_durations(self):
        """Test to_dict() with None min/max durations."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=0,
            conclusion_counts={},
            average_duration_seconds=0.0,
            min_duration_seconds=None,
            max_duration_seconds=None,
            duration_by_conclusion={},
            total_attempts=0,
            average_attempts_per_run=0.0,
            runs_with_no_attempts=0,
            runs_with_attempts=0,
            generated_at=now,
        )

        result = report.to_dict()

        assert result["min_duration_seconds"] is None
        assert result["max_duration_seconds"] is None

    def test_to_dict_datetime_formatting(self):
        """Test that generated_at is serialized to ISO format."""
        now = datetime(2026, 5, 3, 12, 30, 45)
        report = WorkflowStatisticsReport(
            total_runs=1,
            conclusion_counts={"success": 1},
            average_duration_seconds=50.0,
            min_duration_seconds=50.0,
            max_duration_seconds=50.0,
            duration_by_conclusion={"success": 50.0},
            total_attempts=1,
            average_attempts_per_run=1.0,
            runs_with_no_attempts=0,
            runs_with_attempts=1,
            generated_at=now,
        )

        result = report.to_dict()

        assert isinstance(result["generated_at"], str)
        assert result["generated_at"] == "2026-05-03T12:30:45"

    def test_to_dict_with_empty_conclusion_counts(self):
        """Test to_dict() with empty conclusion_counts."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=0,
            conclusion_counts={},
            average_duration_seconds=0.0,
            min_duration_seconds=None,
            max_duration_seconds=None,
            duration_by_conclusion={},
            total_attempts=0,
            average_attempts_per_run=0.0,
            runs_with_no_attempts=0,
            runs_with_attempts=0,
            generated_at=now,
        )

        result = report.to_dict()

        assert result["conclusion_counts"] == {}
        assert result["duration_by_conclusion"] == {}

    def test_to_dict_with_multiple_conclusions(self):
        """Test to_dict() with multiple different conclusions."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=8,
            conclusion_counts={
                "success": 3,
                "failure": 2,
                "cancelled": 2,
                "skipped": 1,
            },
            average_duration_seconds=52.5,
            min_duration_seconds=10.0,
            max_duration_seconds=100.0,
            duration_by_conclusion={
                "success": 45.0,
                "failure": 65.0,
                "cancelled": 50.0,
                "skipped": 25.0,
            },
            total_attempts=12,
            average_attempts_per_run=1.5,
            runs_with_no_attempts=2,
            runs_with_attempts=6,
            generated_at=now,
        )

        result = report.to_dict()
        conclusion_counts = result["conclusion_counts"]

        assert conclusion_counts["success"] == 3
        assert conclusion_counts["failure"] == 2
        assert conclusion_counts["cancelled"] == 2
        assert conclusion_counts["skipped"] == 1
        assert len(conclusion_counts) == 4

    def test_to_dict_with_mixed_none_and_values(self):
        """Test to_dict() with None conclusions mixed with actual conclusions."""
        now = datetime.now()
        report = WorkflowStatisticsReport(
            total_runs=5,
            conclusion_counts={"success": 3, "failure": 1, None: 1},
            average_duration_seconds=48.0,
            min_duration_seconds=20.0,
            max_duration_seconds=80.0,
            duration_by_conclusion={"success": 50.0, "failure": 70.0, None: 20.0},
            total_attempts=8,
            average_attempts_per_run=1.6,
            runs_with_no_attempts=1,
            runs_with_attempts=4,
            generated_at=now,
        )

        result = report.to_dict()
        conclusion_counts = result["conclusion_counts"]
        duration_by_conclusion = result["duration_by_conclusion"]

        # Check that all conclusions are serialized
        assert conclusion_counts["success"] == 3
        assert conclusion_counts["failure"] == 1
        assert conclusion_counts["incomplete"] == 1
        assert len(conclusion_counts) == 3

        # Check duration_by_conclusion serialization
        assert duration_by_conclusion["success"] == 50.0
        assert duration_by_conclusion["failure"] == 70.0
        assert duration_by_conclusion["incomplete"] == 20.0
        assert len(duration_by_conclusion) == 3

    def test_to_dict_returns_copy(self):
        """Test that to_dict() returns a copy, not the original data."""
        now = datetime.now()
        conclusion_counts = {"success": 5, None: 2}
        duration_by_conclusion = {"success": 40.0, None: 30.0}

        report = WorkflowStatisticsReport(
            total_runs=7,
            conclusion_counts=conclusion_counts,
            average_duration_seconds=37.5,
            min_duration_seconds=20.0,
            max_duration_seconds=60.0,
            duration_by_conclusion=duration_by_conclusion,
            total_attempts=10,
            average_attempts_per_run=1.43,
            runs_with_no_attempts=1,
            runs_with_attempts=6,
            generated_at=now,
        )

        result = report.to_dict()

        # Modify the returned dict
        result["total_runs"] = 999

        # Original should be unchanged
        assert report.total_runs == 7
