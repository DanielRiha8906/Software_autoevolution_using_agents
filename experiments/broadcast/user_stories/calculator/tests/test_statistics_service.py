import pytest
from unittest.mock import MagicMock
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.models.statistics import Statistics
from src.services.statistics_service import StatisticsService


class TestStatisticsService:
    def setup_method(self):
        _reset_id_counter()
        self.memory_service = MagicMock()
        self.service = StatisticsService(self.memory_service)

    def test_compute_statistics_empty_entries(self):
        """Test statistics computation with no entries."""
        self.memory_service.retrieve.return_value = []
        stats = self.service.compute_statistics()

        assert isinstance(stats, Statistics)
        assert stats.operation_counts == {}
        assert stats.total_errors == 0
        assert stats.error_rate_percentage == 0.0
        assert stats.average_execution_time_ms == 0.0

    def test_compute_statistics_single_success_entry(self):
        """Test statistics with a single successful entry."""
        entry = ResultEntry(
            operation="add",
            operands=[3, 5],
            result=8,
            execution_time_ms=1.5,
        )
        self.memory_service.retrieve.return_value = [entry]
        stats = self.service.compute_statistics()

        assert stats.operation_counts == {"add": 1}
        assert stats.total_errors == 0
        assert stats.error_rate_percentage == 0.0
        assert stats.average_execution_time_ms == 1.5

    def test_compute_statistics_single_error_entry(self):
        """Test statistics with a single error entry."""
        entry = ErrorEntry(
            operation="divide",
            operands=[5, 0],
            error_message="Division by zero",
            execution_time_ms=0.8,
        )
        self.memory_service.retrieve.return_value = [entry]
        stats = self.service.compute_statistics()

        assert stats.operation_counts == {"divide": 1}
        assert stats.total_errors == 1
        assert stats.error_rate_percentage == 100.0
        assert stats.average_execution_time_ms == 0.8

    def test_compute_statistics_mixed_entries(self):
        """Test statistics with mix of successes and errors."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0),
            ResultEntry(operation="add", operands=[5, 5], result=10, execution_time_ms=1.0),
            ErrorEntry(operation="divide", operands=[10, 0], error_message="error", execution_time_ms=0.5),
            ResultEntry(operation="multiply", operands=[3, 4], result=12, execution_time_ms=1.5),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        assert stats.operation_counts == {"add": 2, "divide": 1, "multiply": 1}
        assert stats.total_errors == 1
        assert stats.error_rate_percentage == 25.0
        assert stats.average_execution_time_ms == 1.0  # (1.0 + 1.0 + 0.5 + 1.5) / 4

    def test_compute_statistics_multiple_same_operation(self):
        """Test operation count accuracy with repeated operations."""
        entries = [
            ResultEntry(operation="sqrt", operands=[4], result=2.0, execution_time_ms=0.5),
            ResultEntry(operation="sqrt", operands=[9], result=3.0, execution_time_ms=0.5),
            ResultEntry(operation="sqrt", operands=[16], result=4.0, execution_time_ms=0.5),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        assert stats.operation_counts == {"sqrt": 3}
        assert stats.total_errors == 0
        assert stats.error_rate_percentage == 0.0
        assert stats.average_execution_time_ms == 0.5

    def test_compute_statistics_error_rate_calculation(self):
        """Test error rate percentage calculation."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0),
            ErrorEntry(operation="add", operands=[1, 2], error_message="error", execution_time_ms=1.0),
            ErrorEntry(operation="add", operands=[1, 2], error_message="error", execution_time_ms=1.0),
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        assert stats.total_errors == 2
        assert stats.error_rate_percentage == 50.0

    def test_compute_statistics_average_execution_time(self):
        """Test average execution time calculation."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=2.0),
            ResultEntry(operation="add", operands=[3, 4], result=7, execution_time_ms=3.0),
            ResultEntry(operation="add", operands=[5, 6], result=11, execution_time_ms=4.0),
            ErrorEntry(operation="divide", operands=[10, 0], error_message="error", execution_time_ms=1.0),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        expected_avg = (2.0 + 3.0 + 4.0 + 1.0) / 4
        assert stats.average_execution_time_ms == expected_avg

    def test_statistics_returns_structured_object(self):
        """Verify that result is a structured Statistics object, not a dict."""
        self.memory_service.retrieve.return_value = []
        stats = self.service.compute_statistics()

        assert isinstance(stats, Statistics)
        assert hasattr(stats, "operation_counts")
        assert hasattr(stats, "total_errors")
        assert hasattr(stats, "error_rate_percentage")
        assert hasattr(stats, "average_execution_time_ms")

    def test_statistics_consistency_across_calls(self):
        """Test that multiple calls with same data produce same result."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="error", execution_time_ms=0.5),
        ]
        self.memory_service.retrieve.return_value = entries

        stats1 = self.service.compute_statistics()
        stats2 = self.service.compute_statistics()

        assert stats1.operation_counts == stats2.operation_counts
        assert stats1.total_errors == stats2.total_errors
        assert stats1.error_rate_percentage == stats2.error_rate_percentage
        assert stats1.average_execution_time_ms == stats2.average_execution_time_ms

    def test_operation_counts_includes_all_operations(self):
        """Test that operation_counts includes every unique operation."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0),
            ResultEntry(operation="subtract", operands=[5, 3], result=2, execution_time_ms=1.0),
            ResultEntry(operation="multiply", operands=[2, 3], result=6, execution_time_ms=1.0),
            ResultEntry(operation="divide", operands=[6, 2], result=3.0, execution_time_ms=1.0),
            ResultEntry(operation="sqrt", operands=[4], result=2.0, execution_time_ms=1.0),
            ResultEntry(operation="power", operands=[2, 3], result=8, execution_time_ms=1.0),
            ResultEntry(operation="square", operands=[5], result=25, execution_time_ms=1.0),
            ResultEntry(operation="modulo", operands=[7, 3], result=1, execution_time_ms=1.0),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        assert len(stats.operation_counts) == 8
        assert set(stats.operation_counts.keys()) == {
            "add", "subtract", "multiply", "divide", "sqrt", "power", "square", "modulo"
        }

    def test_compute_statistics_with_zero_execution_times(self):
        """Test statistics computation with zero execution times."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=0.0),
            ResultEntry(operation="add", operands=[3, 4], result=7, execution_time_ms=0.0),
        ]
        self.memory_service.retrieve.return_value = entries
        stats = self.service.compute_statistics()

        assert stats.average_execution_time_ms == 0.0
