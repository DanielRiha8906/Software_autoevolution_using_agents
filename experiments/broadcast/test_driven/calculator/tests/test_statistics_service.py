import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService, StatisticsReport


@pytest.fixture
def sample_entries():
    """Fixture with 3 entries: 2 adds (success), 1 multiply (failed)."""
    return [
        MemoryEntry(
            operation="add",
            operands=[1, 2],
            result=3,
            success=True,
            execution_time_ms=10,
        ),
        MemoryEntry(
            operation="add",
            operands=[3, 4],
            result=7,
            success=True,
            execution_time_ms=20,
        ),
        MemoryEntry(
            operation="multiply",
            operands=[2, 3],
            result=None,
            success=False,
            execution_time_ms=5,
        ),
    ]


@pytest.fixture
def populated_service(sample_entries):
    """Service with 3 sample entries."""
    service = MemoryService()
    for entry in sample_entries:
        service.store(entry)
    return service


def test_statistics_report_is_dataclass():
    """Verify StatisticsReport is a dataclass."""
    from dataclasses import is_dataclass
    assert is_dataclass(StatisticsReport)


def test_statistics_report_has_required_fields():
    """Verify StatisticsReport has all required fields."""
    report = StatisticsReport(
        count_per_operation={"add": 2},
        total_errors=1,
        error_rate=33.33,
        avg_execution_time_ms=11.67,
    )
    assert hasattr(report, "count_per_operation")
    assert hasattr(report, "total_errors")
    assert hasattr(report, "error_rate")
    assert hasattr(report, "avg_execution_time_ms")


def test_statistics_service_compute_returns_report(populated_service):
    """Verify compute() returns a StatisticsReport."""
    service = StatisticsService(populated_service)
    report = service.compute()
    assert isinstance(report, StatisticsReport)


def test_count_per_operation(populated_service):
    """Verify count_per_operation counts operations correctly."""
    service = StatisticsService(populated_service)
    report = service.compute()
    assert report.count_per_operation["add"] == 2
    assert report.count_per_operation["multiply"] == 1


def test_total_errors(populated_service):
    """Verify total_errors counts failed entries."""
    service = StatisticsService(populated_service)
    report = service.compute()
    assert report.total_errors == 1


def test_error_rate(populated_service):
    """Verify error_rate is percentage (0-100)."""
    service = StatisticsService(populated_service)
    report = service.compute()
    # 1 failed out of 3 = 33.33%
    assert abs(report.error_rate - 33.33) < 0.01


def test_avg_execution_time_ms(populated_service):
    """Verify avg_execution_time_ms is mean of execution times."""
    service = StatisticsService(populated_service)
    report = service.compute()
    # (10 + 20 + 5) / 3 = 11.67
    assert abs(report.avg_execution_time_ms - 11.67) < 0.01


def test_empty_history():
    """Verify handling of empty history."""
    service = MemoryService()
    stats = StatisticsService(service)
    report = stats.compute()
    assert report.count_per_operation == {}
    assert report.total_errors == 0
    assert report.error_rate == 0.0
    assert report.avg_execution_time_ms == 0.0


def test_all_successful_entries():
    """Verify stats when all entries are successful."""
    service = MemoryService()
    service.store(MemoryEntry("add", [1, 2], 3, True, 10.0))
    service.store(MemoryEntry("add", [2, 3], 5, True, 20.0))
    stats = StatisticsService(service)
    report = stats.compute()
    assert report.total_errors == 0
    assert report.error_rate == 0.0
    assert abs(report.avg_execution_time_ms - 15.0) < 0.01


def test_all_failed_entries():
    """Verify stats when all entries failed."""
    service = MemoryService()
    service.store(MemoryEntry("add", [1, 2], None, False, 10.0))
    service.store(MemoryEntry("add", [2, 3], None, False, 20.0))
    stats = StatisticsService(service)
    report = stats.compute()
    assert report.total_errors == 2
    assert report.error_rate == 100.0
    assert abs(report.avg_execution_time_ms - 15.0) < 0.01
