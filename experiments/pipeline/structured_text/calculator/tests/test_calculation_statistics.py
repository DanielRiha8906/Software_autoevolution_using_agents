"""Tests for CalculationStatistics model and MemoryService.compute_statistics()."""

import pytest
from src.models.calculation_statistics import CalculationStatistics
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_json_storage import MemoryJsonStorage


class TestCalculationStatisticsDataclass:
    """Test CalculationStatistics dataclass instantiation and fields."""

    def test_instantiation_with_all_fields(self):
        """Test 1: Instantiate CalculationStatistics with all required fields."""
        stats = CalculationStatistics(
            operation_counts={"add": 5, "subtract": 3},
            total_calculations=8,
            error_count=1,
            error_percentage=12.5,
            average_execution_time_ms=2.3,
            min_execution_time_ms=0.5,
            max_execution_time_ms=5.0,
            per_operation_stats={
                "add": {"count": 5, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 2.0, "min_time_ms": 0.5, "max_time_ms": 3.5},
                "subtract": {"count": 3, "error_count": 1, "error_rate": 33.33, "avg_time_ms": 2.8, "min_time_ms": 1.0, "max_time_ms": 5.0},
            },
        )
        assert stats.operation_counts == {"add": 5, "subtract": 3}
        assert stats.total_calculations == 8
        assert stats.error_count == 1
        assert stats.error_percentage == 12.5
        assert stats.average_execution_time_ms == 2.3
        assert stats.min_execution_time_ms == 0.5
        assert stats.max_execution_time_ms == 5.0
        assert len(stats.per_operation_stats) == 2

    def test_empty_statistics_fields(self):
        """Test 2: Instantiate with zero values (empty storage scenario)."""
        stats = CalculationStatistics(
            operation_counts={},
            total_calculations=0,
            error_count=0,
            error_percentage=0.0,
            average_execution_time_ms=0.0,
            min_execution_time_ms=0.0,
            max_execution_time_ms=0.0,
            per_operation_stats={},
        )
        assert stats.total_calculations == 0
        assert stats.error_count == 0
        assert stats.error_percentage == 0.0
        assert stats.operation_counts == {}
        assert stats.per_operation_stats == {}

    def test_field_types_preserved(self):
        """Test 3: Field types are correctly preserved."""
        stats = CalculationStatistics(
            operation_counts={"add": 1},
            total_calculations=1,
            error_count=0,
            error_percentage=0.0,
            average_execution_time_ms=1.5,
            min_execution_time_ms=1.5,
            max_execution_time_ms=1.5,
            per_operation_stats={"add": {"count": 1, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 1.5, "min_time_ms": 1.5, "max_time_ms": 1.5}},
        )
        assert isinstance(stats.operation_counts, dict)
        assert isinstance(stats.total_calculations, int)
        assert isinstance(stats.error_count, int)
        assert isinstance(stats.error_percentage, float)
        assert isinstance(stats.average_execution_time_ms, float)
        assert isinstance(stats.min_execution_time_ms, float)
        assert isinstance(stats.max_execution_time_ms, float)
        assert isinstance(stats.per_operation_stats, dict)

    def test_to_dict_method(self):
        """Test 4: to_dict() returns JSON-compatible dictionary."""
        stats = CalculationStatistics(
            operation_counts={"add": 5},
            total_calculations=5,
            error_count=0,
            error_percentage=0.0,
            average_execution_time_ms=2.0,
            min_execution_time_ms=1.0,
            max_execution_time_ms=3.0,
            per_operation_stats={"add": {"count": 5, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 2.0, "min_time_ms": 1.0, "max_time_ms": 3.0}},
        )
        result = stats.to_dict()
        assert isinstance(result, dict)
        assert result["operation_counts"] == {"add": 5}
        assert result["total_calculations"] == 5
        assert result["error_count"] == 0
        assert result["error_percentage"] == 0.0

    def test_from_dict_method(self):
        """Test 5: from_dict() reconstructs CalculationStatistics from dict."""
        data = {
            "operation_counts": {"add": 5, "multiply": 2},
            "total_calculations": 7,
            "error_count": 0,
            "error_percentage": 0.0,
            "average_execution_time_ms": 1.5,
            "min_execution_time_ms": 1.0,
            "max_execution_time_ms": 2.0,
            "per_operation_stats": {
                "add": {"count": 5, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 1.5, "min_time_ms": 1.0, "max_time_ms": 2.0},
                "multiply": {"count": 2, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 1.5, "min_time_ms": 1.0, "max_time_ms": 2.0},
            },
        }
        stats = CalculationStatistics.from_dict(data)
        assert stats.operation_counts == {"add": 5, "multiply": 2}
        assert stats.total_calculations == 7
        assert stats.error_count == 0

    def test_round_trip_dict_conversion(self):
        """Test 6: to_dict() -> from_dict() preserves all data."""
        original = CalculationStatistics(
            operation_counts={"add": 3, "divide": 1},
            total_calculations=4,
            error_count=1,
            error_percentage=25.0,
            average_execution_time_ms=1.75,
            min_execution_time_ms=0.5,
            max_execution_time_ms=3.0,
            per_operation_stats={
                "add": {"count": 3, "error_count": 0, "error_rate": 0.0, "avg_time_ms": 1.5, "min_time_ms": 1.0, "max_time_ms": 2.0},
                "divide": {"count": 1, "error_count": 1, "error_rate": 100.0, "avg_time_ms": 3.0, "min_time_ms": 3.0, "max_time_ms": 3.0},
            },
        )
        reconstructed = CalculationStatistics.from_dict(original.to_dict())
        assert reconstructed.operation_counts == original.operation_counts
        assert reconstructed.total_calculations == original.total_calculations
        assert reconstructed.error_count == original.error_count
        assert reconstructed.error_percentage == original.error_percentage
        assert reconstructed.average_execution_time_ms == original.average_execution_time_ms


class TestMemoryServiceComputeStatisticsEmptyStorage:
    """Test compute_statistics() with empty storage."""

    def test_empty_storage_returns_zero_counts(self, tmp_path):
        """Test 1: Empty storage returns all-zero statistics."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        stats = service.compute_statistics()

        assert stats.total_calculations == 0
        assert stats.error_count == 0
        assert stats.error_percentage == 0.0
        assert stats.average_execution_time_ms == 0.0
        assert stats.operation_counts == {}
        assert stats.per_operation_stats == {}

    def test_empty_storage_min_max_times(self, tmp_path):
        """Test 2: Empty storage has zero min/max times."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 0.0
        assert stats.max_execution_time_ms == 0.0


class TestMemoryServiceComputeStatisticsSingleEntry:
    """Test compute_statistics() with single entry."""

    def test_single_successful_entry(self, tmp_path):
        """Test 1: Single successful entry statistics."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.5, "id-1")
        service.store(entry)

        stats = service.compute_statistics()

        assert stats.total_calculations == 1
        assert stats.error_count == 0
        assert stats.error_percentage == 0.0
        assert stats.operation_counts == {"add": 1}
        assert stats.average_execution_time_ms == 1.5
        assert stats.min_execution_time_ms == 1.5
        assert stats.max_execution_time_ms == 1.5

    def test_single_failed_entry(self, tmp_path):
        """Test 2: Single failed entry statistics."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entry = MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:00:00", 0.5, "id-1")
        service.store(entry)

        stats = service.compute_statistics()

        assert stats.total_calculations == 1
        assert stats.error_count == 1
        assert stats.error_percentage == 100.0
        assert stats.operation_counts == {"divide": 1}
        assert stats.average_execution_time_ms == 0.5


class TestMemoryServiceComputeStatisticsMultipleEntries:
    """Test compute_statistics() with multiple diverse entries."""

    def test_multiple_mixed_entries(self, tmp_path):
        """Test 1: Multiple entries with different operations and outcomes."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:03:00", 0.5, "id-4"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:04:00", 2.5, "id-5"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.total_calculations == 5
        assert stats.error_count == 1
        assert stats.error_percentage == 20.0
        assert stats.operation_counts == {"add": 2, "subtract": 1, "divide": 1, "multiply": 1}
        assert stats.average_execution_time_ms == (1.0 + 2.0 + 1.5 + 0.5 + 2.5) / 5

    def test_multiple_entries_all_success(self, tmp_path):
        """Test 2: Multiple entries, all successful."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("add", 100.0, 50.0, 150.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.error_count == 0
        assert stats.error_percentage == 0.0
        assert stats.operation_counts == {"add": 2, "multiply": 1}

    def test_multiple_entries_all_failed(self, tmp_path):
        """Test 3: Multiple entries, all failed."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, "Cannot take sqrt of negative", "2026-05-03T10:01:00", 0.8, "id-2"),
            MemoryEntry("divide", 5.0, 0.0, None, False, "Division by zero", "2026-05-03T10:02:00", 0.6, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.error_count == 3
        assert stats.error_percentage == 100.0
        assert stats.operation_counts == {"divide": 2, "sqrt": 1}


class TestMemoryServiceComputeStatisticsMinMaxTime:
    """Test min and max execution time calculation."""

    def test_min_max_execution_times(self, tmp_path):
        """Test 1: Min and max execution times are calculated correctly."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
            MemoryEntry("divide", 20.0, 4.0, 5.0, True, None, "2026-05-03T10:03:00", 3.5, "id-4"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 0.5
        assert stats.max_execution_time_ms == 3.5

    def test_min_max_same_value(self, tmp_path):
        """Test 2: Min and max are equal for single execution time."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 2.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 2.0, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 2.0
        assert stats.max_execution_time_ms == 2.0

    def test_min_max_with_zero_time(self, tmp_path):
        """Test 3: Min can be zero when entry has 0.0 execution time."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 1.5, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 0.0
        assert stats.max_execution_time_ms == 1.5


class TestMemoryServiceComputeStatisticsAverageTime:
    """Test average execution time calculation."""

    def test_average_execution_time(self, tmp_path):
        """Test 1: Average execution time is calculated correctly."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 3.0, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        expected_avg = (1.0 + 2.0 + 3.0) / 3
        assert stats.average_execution_time_ms == expected_avg

    def test_average_with_failed_entries(self, tmp_path):
        """Test 2: Average includes failed entries' execution times."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 2.0, "id-1"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 1.0, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 3.0, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        expected_avg = (2.0 + 1.0 + 3.0) / 3
        assert stats.average_execution_time_ms == expected_avg


class TestMemoryServiceComputeStatisticsOperationCounts:
    """Test operation usage count calculation."""

    def test_operation_counts_single_operation(self, tmp_path):
        """Test 1: Count multiple uses of single operation."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 1.5, "id-2"),
            MemoryEntry("add", 100.0, 50.0, 150.0, True, None, "2026-05-03T10:02:00", 0.8, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.operation_counts == {"add": 3}

    def test_operation_counts_multiple_operations(self, tmp_path):
        """Test 2: Count multiple operations with varying frequencies."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:03:00", 2.5, "id-4"),
            MemoryEntry("add", 100.0, 50.0, 150.0, True, None, "2026-05-03T10:04:00", 0.8, "id-5"),
            MemoryEntry("divide", 20.0, 4.0, 5.0, True, None, "2026-05-03T10:05:00", 1.2, "id-6"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.operation_counts == {
            "add": 3,
            "subtract": 1,
            "multiply": 1,
            "divide": 1,
        }


class TestMemoryServiceComputeStatisticsErrorRate:
    """Test error percentage calculation."""

    def test_error_percentage_zero(self, tmp_path):
        """Test 1: 0% error rate when all successful."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.error_percentage == 0.0
        assert stats.error_count == 0

    def test_error_percentage_100(self, tmp_path):
        """Test 2: 100% error rate when all failed."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, "Cannot take sqrt of negative", "2026-05-03T10:01:00", 0.8, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.error_percentage == 100.0
        assert stats.error_count == 2

    def test_error_percentage_partial(self, tmp_path):
        """Test 3: Partial error rate (e.g., 40%)."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:02:00", 0.5, "id-3"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:03:00", 2.5, "id-4"),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, "Cannot take sqrt of negative", "2026-05-03T10:04:00", 0.8, "id-5"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        expected_error_percentage = (2 / 5) * 100
        assert stats.error_percentage == expected_error_percentage
        assert stats.error_count == 2


class TestMemoryServiceComputeStatisticsPerOperation:
    """Test per-operation statistics breakdown."""

    def test_per_operation_stats_structure(self, tmp_path):
        """Test 1: per_operation_stats has correct structure for each operation."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert "add" in stats.per_operation_stats
        op_stats = stats.per_operation_stats["add"]
        assert "count" in op_stats
        assert "error_count" in op_stats
        assert "error_rate" in op_stats
        assert "avg_time_ms" in op_stats
        assert "min_time_ms" in op_stats
        assert "max_time_ms" in op_stats

    def test_per_operation_all_successful(self, tmp_path):
        """Test 2: Per-operation with all successful operations."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        op_stats = stats.per_operation_stats["add"]
        assert op_stats["count"] == 2
        assert op_stats["error_count"] == 0
        assert op_stats["error_rate"] == 0.0
        assert op_stats["avg_time_ms"] == 1.5
        assert op_stats["min_time_ms"] == 1.0
        assert op_stats["max_time_ms"] == 2.0

    def test_per_operation_with_errors(self, tmp_path):
        """Test 3: Per-operation with mixed success/failure."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("divide", 10.0, 2.0, 5.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"),
            MemoryEntry("divide", 20.0, 4.0, 5.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        op_stats = stats.per_operation_stats["divide"]
        assert op_stats["count"] == 3
        assert op_stats["error_count"] == 1
        assert op_stats["error_rate"] == pytest.approx((1/3) * 100, rel=0.01)
        assert op_stats["avg_time_ms"] == pytest.approx((1.0 + 0.5 + 1.5) / 3, rel=0.01)
        assert op_stats["min_time_ms"] == 0.5
        assert op_stats["max_time_ms"] == 1.5

    def test_per_operation_multiple_operations(self, tmp_path):
        """Test 4: Per-operation stats for multiple different operations."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:03:00", 2.5, "id-4"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert len(stats.per_operation_stats) == 3
        assert stats.per_operation_stats["add"]["count"] == 2
        assert stats.per_operation_stats["subtract"]["count"] == 1
        assert stats.per_operation_stats["multiply"]["count"] == 1

    def test_per_operation_error_rate_100_percent(self, tmp_path):
        """Test 5: Per-operation error rate at 100% for all-failed operation."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("divide", 5.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.6, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        op_stats = stats.per_operation_stats["divide"]
        assert op_stats["count"] == 2
        assert op_stats["error_count"] == 2
        assert op_stats["error_rate"] == 100.0


class TestMemoryServiceComputeStatisticsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_execution_times(self, tmp_path):
        """Test 1: Very small execution times are handled correctly."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.001, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 0.0001, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 0.0001
        assert stats.max_execution_time_ms == 0.001

    def test_large_execution_times(self, tmp_path):
        """Test 2: Large execution times are handled correctly."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 10000.5, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 20000.75, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.min_execution_time_ms == 10000.5
        assert stats.max_execution_time_ms == 20000.75

    def test_many_entries_same_operation(self, tmp_path):
        """Test 3: Many entries of the same operation."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        # Create 100 add entries
        for i in range(100):
            entry = MemoryEntry("add", float(i), float(i+1), float(2*i+1), True, None, "2026-05-03T10:00:00", 1.0, f"id-{i}")
            service.store(entry)

        stats = service.compute_statistics()

        assert stats.operation_counts == {"add": 100}
        assert stats.total_calculations == 100
        assert stats.error_count == 0
        assert stats.error_percentage == 0.0

    def test_decimal_precision_preservation(self, tmp_path):
        """Test 4: Decimal precision is preserved in calculations."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.1, 2.2, 3.3, True, None, "2026-05-03T10:00:00", 1.111, "id-1"),
            MemoryEntry("subtract", 10.5, 3.7, 6.8, True, None, "2026-05-03T10:01:00", 2.222, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats = service.compute_statistics()

        # Verify precision is maintained (not rounded too early)
        expected_avg = (1.111 + 2.222) / 2
        assert abs(stats.average_execution_time_ms - expected_avg) < 0.001


class TestMemoryServiceComputeStatisticsConsistency:
    """Test consistency of statistics across multiple calls."""

    def test_repeated_calls_return_same_stats(self, tmp_path):
        """Test 1: Multiple calls to compute_statistics return same values."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        stats1 = service.compute_statistics()
        stats2 = service.compute_statistics()

        assert stats1.total_calculations == stats2.total_calculations
        assert stats1.error_count == stats2.error_count
        assert stats1.operation_counts == stats2.operation_counts
        assert stats1.average_execution_time_ms == stats2.average_execution_time_ms

    def test_stats_reflect_stored_data(self, tmp_path):
        """Test 2: Statistics accurately reflect what's actually stored."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        # Store some entries
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1")
        entry2 = MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2")
        service.store(entry1)
        service.store(entry2)

        # Get stats
        stats = service.compute_statistics()

        # Verify against retrieved data
        retrieved = service.retrieve_all()
        assert stats.total_calculations == len(retrieved)
        assert stats.error_count == sum(1 for e in retrieved if not e.success)
