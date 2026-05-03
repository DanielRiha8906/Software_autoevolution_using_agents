import dataclasses
import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService


def _entry(operation="add", success=True, execution_time_ms=10.0):
    return MemoryEntry(operation=operation, operands=[1, 2], result=3,
                       success=success, execution_time_ms=execution_time_ms)


@pytest.fixture
def stats_svc():
    memory = MemoryService()
    memory.store(_entry("add", success=True, execution_time_ms=10))
    memory.store(_entry("add", success=True, execution_time_ms=20))
    memory.store(_entry("multiply", success=False, execution_time_ms=5))
    return StatisticsService(memory)


def test_report_is_dataclass(stats_svc):
    assert dataclasses.is_dataclass(stats_svc.compute())


def test_count_per_operation(stats_svc):
    report = stats_svc.compute()
    assert report.count_per_operation["add"] == 2
    assert report.count_per_operation["multiply"] == 1


def test_total_errors(stats_svc):
    report = stats_svc.compute()
    assert report.total_errors == 1


def test_error_rate(stats_svc):
    report = stats_svc.compute()
    assert report.error_rate == pytest.approx(100 / 3, rel=1e-3)


def test_average_execution_time(stats_svc):
    report = stats_svc.compute()
    assert report.avg_execution_time_ms == pytest.approx(35 / 3, rel=1e-3)


def test_report_structure_is_consistent(stats_svc):
    r1 = stats_svc.compute()
    r2 = stats_svc.compute()
    assert r1.total_errors == r2.total_errors
    assert r1.avg_execution_time_ms == r2.avg_execution_time_ms
