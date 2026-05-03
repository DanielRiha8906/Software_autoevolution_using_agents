import pytest
from dataclasses import is_dataclass

from src.services.statistics_service import StatisticsService
from src.services.memory_service import MemoryService
from src.models.memory_entry import MemoryEntry
from src.models.statistics_result import StatisticsResult


@pytest.fixture
def memory_service_with_entries():
    """Creates MemoryService with 3 entries: 2 'add' (success), 1 'multiply' (failed).

    Times: 10ms, 20ms, 5ms respectively
    Expected values:
    - count_per_operation = {"add": 2, "multiply": 1}
    - total_errors = 1
    - error_rate ≈ 33.33% (1/3)
    - avg_execution_time_ms ≈ 11.67ms (35/3)
    """
    service = MemoryService()

    # Entry 1: add, success, 10ms
    entry1 = MemoryEntry(
        operation="add",
        operands=[2, 3],
        result=5.0,
        success=True,
        execution_time_ms=10.0
    )
    service.store(entry1)

    # Entry 2: add, success, 20ms
    entry2 = MemoryEntry(
        operation="add",
        operands=[5, 10],
        result=15.0,
        success=True,
        execution_time_ms=20.0
    )
    service.store(entry2)

    # Entry 3: multiply, failed, 5ms
    entry3 = MemoryEntry(
        operation="multiply",
        operands=[2, 3],
        result=None,
        success=False,
        execution_time_ms=5.0
    )
    service.store(entry3)

    return service


class TestStatisticsServiceConstructor:
    """Test StatisticsService initialization."""

    def test_constructor_accepts_memory_service(self, memory_service_with_entries):
        """Constructor should accept a MemoryService instance."""
        service = StatisticsService(memory_service_with_entries)
        assert service is not None

    def test_constructor_stores_memory_service_reference(self, memory_service_with_entries):
        """Constructor should store the MemoryService for later use."""
        service = StatisticsService(memory_service_with_entries)
        # Verify by calling compute - it should work
        result = service.compute()
        assert result is not None


class TestComputeReturnType:
    """Test that compute() returns a StatisticsResult dataclass."""

    def test_compute_returns_dataclass(self, memory_service_with_entries):
        """compute() should return a StatisticsResult dataclass instance."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert is_dataclass(result)

    def test_compute_returns_statistics_result_instance(self, memory_service_with_entries):
        """compute() should return a StatisticsResult instance."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert isinstance(result, StatisticsResult)

    def test_compute_result_has_all_fields(self, memory_service_with_entries):
        """Returned StatisticsResult should have all required fields."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert hasattr(result, "count_per_operation")
        assert hasattr(result, "total_errors")
        assert hasattr(result, "error_rate")
        assert hasattr(result, "avg_execution_time_ms")


class TestCountPerOperationCalculation:
    """Test count_per_operation calculation."""

    def test_count_per_operation_correct_values(self, memory_service_with_entries):
        """count_per_operation should correctly count operations."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert result.count_per_operation == {"add": 2, "multiply": 1}

    def test_count_per_operation_is_dict(self, memory_service_with_entries):
        """count_per_operation should be a dictionary."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert isinstance(result.count_per_operation, dict)

    def test_count_per_operation_keys_are_strings(self, memory_service_with_entries):
        """count_per_operation keys should be operation names (strings)."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        for key in result.count_per_operation.keys():
            assert isinstance(key, str)

    def test_count_per_operation_values_are_ints(self, memory_service_with_entries):
        """count_per_operation values should be integers."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        for value in result.count_per_operation.values():
            assert isinstance(value, int)


class TestTotalErrorsCalculation:
    """Test total_errors calculation."""

    def test_total_errors_correct_value(self, memory_service_with_entries):
        """total_errors should count entries where success=False."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert result.total_errors == 1

    def test_total_errors_is_int(self, memory_service_with_entries):
        """total_errors should be an integer."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert isinstance(result.total_errors, int)

    def test_total_errors_non_negative(self, memory_service_with_entries):
        """total_errors should never be negative."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert result.total_errors >= 0


class TestErrorRateCalculation:
    """Test error_rate calculation (percentage 0-100)."""

    def test_error_rate_correct_percentage(self, memory_service_with_entries):
        """error_rate should be (total_errors / total_entries) * 100."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        expected = (1 / 3) * 100  # ≈ 33.33%
        assert abs(result.error_rate - expected) < 0.01

    def test_error_rate_is_float(self, memory_service_with_entries):
        """error_rate should be a float."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert isinstance(result.error_rate, float)

    def test_error_rate_in_valid_range(self, memory_service_with_entries):
        """error_rate should be between 0.0 and 100.0."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert 0.0 <= result.error_rate <= 100.0

    def test_error_rate_zero_when_no_errors(self):
        """error_rate should be 0.0 when all operations succeed."""
        memory_service = MemoryService()
        entry1 = MemoryEntry(
            operation="add",
            operands=[1, 2],
            result=3.0,
            success=True,
            execution_time_ms=10.0
        )
        memory_service.store(entry1)

        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.error_rate == 0.0

    def test_error_rate_hundred_when_all_errors(self):
        """error_rate should be 100.0 when all operations fail."""
        memory_service = MemoryService()
        entry1 = MemoryEntry(
            operation="divide",
            operands=[1, 0],
            result=None,
            success=False,
            execution_time_ms=5.0
        )
        memory_service.store(entry1)

        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.error_rate == 100.0


class TestAvgExecutionTimeCalculation:
    """Test avg_execution_time_ms calculation."""

    def test_avg_execution_time_correct_value(self, memory_service_with_entries):
        """avg_execution_time_ms should be mean of all execution times."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        expected = (10.0 + 20.0 + 5.0) / 3  # ≈ 11.67ms
        assert abs(result.avg_execution_time_ms - expected) < 0.01

    def test_avg_execution_time_is_float(self, memory_service_with_entries):
        """avg_execution_time_ms should be a float."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert isinstance(result.avg_execution_time_ms, float)

    def test_avg_execution_time_non_negative(self, memory_service_with_entries):
        """avg_execution_time_ms should never be negative."""
        service = StatisticsService(memory_service_with_entries)
        result = service.compute()
        assert result.avg_execution_time_ms >= 0.0


class TestEmptyHistoryEdgeCase:
    """Test behavior when MemoryService is empty."""

    def test_empty_history_returns_zero_counts(self):
        """Empty MemoryService should return 0 counts."""
        memory_service = MemoryService()
        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.total_errors == 0

    def test_empty_history_returns_empty_operation_dict(self):
        """Empty MemoryService should return empty count_per_operation dict."""
        memory_service = MemoryService()
        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.count_per_operation == {}

    def test_empty_history_returns_zero_error_rate(self):
        """Empty MemoryService should return 0.0 error_rate."""
        memory_service = MemoryService()
        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.error_rate == 0.0

    def test_empty_history_returns_zero_avg_time(self):
        """Empty MemoryService should return 0.0 avg_execution_time_ms."""
        memory_service = MemoryService()
        service = StatisticsService(memory_service)
        result = service.compute()
        assert result.avg_execution_time_ms == 0.0

    def test_empty_history_returns_complete_result(self):
        """Empty MemoryService should return a complete StatisticsResult."""
        memory_service = MemoryService()
        service = StatisticsService(memory_service)
        result = service.compute()
        assert isinstance(result, StatisticsResult)
        assert hasattr(result, "count_per_operation")
        assert hasattr(result, "total_errors")
        assert hasattr(result, "error_rate")
        assert hasattr(result, "avg_execution_time_ms")


class TestConsistencyAcrossMultipleCalls:
    """Test that compute() returns consistent results across multiple calls."""

    def test_multiple_calls_return_same_results(self, memory_service_with_entries):
        """Multiple calls to compute() should return identical results."""
        service = StatisticsService(memory_service_with_entries)
        result1 = service.compute()
        result2 = service.compute()
        result3 = service.compute()

        assert result1.count_per_operation == result2.count_per_operation
        assert result2.count_per_operation == result3.count_per_operation
        assert result1.total_errors == result2.total_errors == result3.total_errors
        assert result1.error_rate == result2.error_rate == result3.error_rate
        assert result1.avg_execution_time_ms == result2.avg_execution_time_ms == result3.avg_execution_time_ms

    def test_compute_does_not_modify_memory_service(self, memory_service_with_entries):
        """compute() should not modify the MemoryService state."""
        service = StatisticsService(memory_service_with_entries)
        initial_entries = memory_service_with_entries.retrieve()
        initial_count = len(initial_entries)

        service.compute()
        service.compute()
        service.compute()

        final_entries = memory_service_with_entries.retrieve()
        final_count = len(final_entries)

        assert initial_count == final_count
        assert len(initial_entries) == len(final_entries)
