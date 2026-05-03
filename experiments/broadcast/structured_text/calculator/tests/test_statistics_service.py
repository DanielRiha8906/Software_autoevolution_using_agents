import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService
from src.models.statistics_report import StatisticsReport
from unittest.mock import MagicMock


class TestStatisticsService:
    """Test suite for StatisticsService."""

    def test_empty_entries_returns_zero_stats(self):
        """Test computing statistics with no entries."""
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = []

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert isinstance(report, StatisticsReport)
        assert report.total_operations == 0
        assert report.operation_count == {}
        assert report.total_errors == 0
        assert report.error_frequency == {}
        assert report.error_rate == 0.0
        assert report.average_execution_time_ms == 0.0
        assert report.min_execution_time_ms == 0.0
        assert report.max_execution_time_ms == 0.0

    def test_counts_operations_correctly(self):
        """Test that operation counts are computed correctly."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("add", 2.0, 3.0, 5.0, success=True, execution_time_ms=1.0),
            MemoryEntry("multiply", 2.0, 3.0, 6.0, success=True, execution_time_ms=1.5),
            MemoryEntry("divide", 10.0, 2.0, 5.0, success=True, execution_time_ms=1.2),
        ]
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = entries

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert report.total_operations == 4
        assert report.operation_count == {"add": 2, "multiply": 1, "divide": 1}

    def test_counts_errors_correctly(self):
        """Test that error counts are computed correctly."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("divide", 10.0, 0.0, None, success=False,
                       error_message="Division by zero", execution_time_ms=0.5),
            MemoryEntry("sqrt", -1.0, 0.0, None, success=False,
                       error_message="Cannot take sqrt of negative", execution_time_ms=0.3),
            MemoryEntry("multiply", 2.0, 3.0, 6.0, success=True, execution_time_ms=1.0),
        ]
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = entries

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert report.total_errors == 2
        assert report.error_frequency == {"divide": 1, "sqrt": 1}
        assert report.error_rate == 0.5  # 2 errors out of 4 operations

    def test_computes_execution_time_stats(self):
        """Test that execution time statistics are computed correctly."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("add", 2.0, 3.0, 5.0, success=True, execution_time_ms=3.0),
            MemoryEntry("multiply", 2.0, 3.0, 6.0, success=True, execution_time_ms=2.0),
        ]
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = entries

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert report.min_execution_time_ms == 1.0
        assert report.max_execution_time_ms == 3.0
        assert report.average_execution_time_ms == pytest.approx(2.0)

    def test_returns_statistics_report_dataclass(self):
        """Test that the return value is a StatisticsReport dataclass."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
        ]
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = entries

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert isinstance(report, StatisticsReport)
        assert hasattr(report, 'total_operations')
        assert hasattr(report, 'operation_count')
        assert hasattr(report, 'total_errors')
        assert hasattr(report, 'error_frequency')
        assert hasattr(report, 'error_rate')
        assert hasattr(report, 'average_execution_time_ms')
        assert hasattr(report, 'min_execution_time_ms')
        assert hasattr(report, 'max_execution_time_ms')

    def test_error_rate_precision(self):
        """Test that error rate is computed with proper precision."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("add", 1.0, 2.0, 3.0, success=True, execution_time_ms=1.0),
            MemoryEntry("divide", 10.0, 0.0, None, success=False,
                       error_message="Division by zero", execution_time_ms=0.5),
        ]
        memory_service = MagicMock(spec=MemoryService)
        memory_service.retrieve.return_value = entries

        service = StatisticsService(memory_service)
        report = service.compute_statistics()

        assert report.error_rate == pytest.approx(0.25)  # 1 error out of 4 operations
