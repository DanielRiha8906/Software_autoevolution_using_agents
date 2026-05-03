import pytest
from dataclasses import is_dataclass
from src.models.memory_entry import MemoryEntry
from src.services.statistics_service import StatisticsService, StatisticsReport


@pytest.fixture
def memory_service_with_entries():
    """Fixture with 3 entries: 2 adds (success, 10ms and 20ms), 1 multiply (failed, 5ms)."""
    from src.services.memory_service import MemoryService

    service = MemoryService()
    # Add two successful add operations
    service.store(MemoryEntry(
        operation="add",
        operands=[1, 2],
        result=3,
        success=True,
        execution_time_ms=10.0
    ))
    service.store(MemoryEntry(
        operation="add",
        operands=[5, 10],
        result=15,
        success=True,
        execution_time_ms=20.0
    ))
    # Add one failed multiply operation
    service.store(MemoryEntry(
        operation="multiply",
        operands=[2, 3],
        result=None,
        success=False,
        execution_time_ms=5.0
    ))
    return service


def test_statistics_report_is_dataclass():
    """StatisticsReport should be a dataclass."""
    assert is_dataclass(StatisticsReport)


def test_statistics_report_has_required_fields():
    """StatisticsReport should have all required fields."""
    report = StatisticsReport(
        count_per_operation={"add": 1},
        total_errors=0,
        error_rate=0.0,
        avg_execution_time_ms=10.0
    )
    assert hasattr(report, "count_per_operation")
    assert hasattr(report, "total_errors")
    assert hasattr(report, "error_rate")
    assert hasattr(report, "avg_execution_time_ms")


def test_statistics_service_computes_count_per_operation(memory_service_with_entries):
    """Should count operations by type."""
    service = StatisticsService(memory_service_with_entries)
    report = service.compute()

    assert report.count_per_operation["add"] == 2
    assert report.count_per_operation["multiply"] == 1


def test_statistics_service_computes_total_errors(memory_service_with_entries):
    """Should count total failed entries."""
    service = StatisticsService(memory_service_with_entries)
    report = service.compute()

    assert report.total_errors == 1


def test_statistics_service_computes_error_rate(memory_service_with_entries):
    """Should compute error rate as percentage (0-100)."""
    service = StatisticsService(memory_service_with_entries)
    report = service.compute()

    # 1 error out of 3 entries = 33.33%
    assert abs(report.error_rate - 33.33) < 0.01


def test_statistics_service_computes_avg_execution_time(memory_service_with_entries):
    """Should compute average execution time in milliseconds."""
    service = StatisticsService(memory_service_with_entries)
    report = service.compute()

    # (10 + 20 + 5) / 3 = 11.67ms
    assert abs(report.avg_execution_time_ms - 11.67) < 0.01


def test_statistics_service_handles_empty_history():
    """Should safely handle empty history."""
    from src.services.memory_service import MemoryService

    service = StatisticsService(MemoryService())
    report = service.compute()

    assert report.count_per_operation == {}
    assert report.total_errors == 0
    assert report.error_rate == 0.0
    assert report.avg_execution_time_ms == 0.0


def test_statistics_service_all_successful_operations():
    """Should compute correct statistics when all operations succeed."""
    from src.services.memory_service import MemoryService

    memory_service = MemoryService()
    memory_service.store(MemoryEntry(
        operation="add",
        operands=[1, 2],
        result=3,
        success=True,
        execution_time_ms=10.0
    ))
    memory_service.store(MemoryEntry(
        operation="add",
        operands=[5, 10],
        result=15,
        success=True,
        execution_time_ms=20.0
    ))

    service = StatisticsService(memory_service)
    report = service.compute()

    assert report.total_errors == 0
    assert report.error_rate == 0.0
    assert report.avg_execution_time_ms == 15.0


def test_statistics_service_all_failed_operations():
    """Should compute correct statistics when all operations fail."""
    from src.services.memory_service import MemoryService

    memory_service = MemoryService()
    memory_service.store(MemoryEntry(
        operation="divide",
        operands=[1, 0],
        result=None,
        success=False,
        execution_time_ms=5.0
    ))
    memory_service.store(MemoryEntry(
        operation="divide",
        operands=[2, 0],
        result=None,
        success=False,
        execution_time_ms=3.0
    ))

    service = StatisticsService(memory_service)
    report = service.compute()

    assert report.total_errors == 2
    assert report.error_rate == 100.0
    assert report.avg_execution_time_ms == 4.0
