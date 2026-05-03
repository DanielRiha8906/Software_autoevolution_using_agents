import pytest
from unittest.mock import MagicMock
from src.models.memory_entry import MemoryEntry
from src.models.calculation_statistics import CalculationStatistics
from src.services.statistics_service import StatisticsService


class TestStatisticsServiceInitialization:
    """Test StatisticsService initialization."""

    def test_initialization_with_memory_service(self):
        """Test StatisticsService initialization with MemoryService."""
        memory_service = MagicMock()
        stats_service = StatisticsService(memory_service)
        assert stats_service.memory_service is memory_service


class TestStatisticsServiceGenerate:
    """Test StatisticsService.generate() method."""

    def test_generate_empty_history(self):
        """Test generate() with no entries."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert isinstance(stats, CalculationStatistics)
        assert stats.operation_counts == {
            "add": 0,
            "subtract": 0,
            "multiply": 0,
            "divide": 0,
            "square": 0,
            "sqrt": 0,
            "power": 0,
            "modulo": 0,
            "sin": 0,
            "cos": 0,
            "tan": 0,
            "log": 0,
            "ln": 0,
            "exp": 0,
        }
        assert stats.total_errors == 0
        assert stats.error_rate == 0.0
        assert stats.avg_execution_time_ms == 0.0

    def test_generate_single_successful_operation(self):
        """Test generate() with single successful operation."""
        memory_service = MagicMock()
        entry = MemoryEntry(
            operation_name="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            execution_time_ms=1.5,
        )
        memory_service.get_all_entries.return_value = [entry]
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert stats.operation_counts["add"] == 1
        assert stats.operation_counts["subtract"] == 0
        assert stats.total_errors == 0
        assert stats.error_rate == 0.0
        assert stats.avg_execution_time_ms == 1.5

    def test_generate_multiple_operations_different_types(self):
        """Test generate() with multiple different operation types."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("add", 5.0, 3.0, 8.0, True, execution_time_ms=1.0),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, execution_time_ms=1.0),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, execution_time_ms=2.0),
            MemoryEntry("divide", 9.0, 3.0, 3.0, True, execution_time_ms=1.5),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert stats.operation_counts["add"] == 2
        assert stats.operation_counts["subtract"] == 1
        assert stats.operation_counts["multiply"] == 1
        assert stats.operation_counts["divide"] == 1
        assert stats.operation_counts["square"] == 0
        assert stats.operation_counts["sqrt"] == 0
        assert stats.operation_counts["power"] == 0
        assert stats.operation_counts["modulo"] == 0
        assert stats.total_errors == 0
        assert stats.error_rate == 0.0
        # (1 + 1 + 1 + 2 + 1.5) / 5 = 6.5 / 5 = 1.3
        assert stats.avg_execution_time_ms == 1.3

    def test_generate_with_errors(self):
        """Test generate() with failed operations."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero", execution_time_ms=1.0),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, error_message="negative", execution_time_ms=1.0),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert stats.operation_counts["add"] == 1
        assert stats.operation_counts["divide"] == 1
        assert stats.operation_counts["sqrt"] == 1
        assert stats.total_errors == 2
        # 2 errors out of 3 operations = 66.67%
        assert stats.error_rate == pytest.approx(66.66666666666666, rel=1e-5)

    def test_generate_error_rate_calculation(self):
        """Test generate() error rate calculation."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("add", 3.0, 4.0, 7.0, True, execution_time_ms=1.0),
            MemoryEntry("add", 5.0, 0.0, None, False, error_message="error", execution_time_ms=1.0),
            MemoryEntry("add", 6.0, 0.0, None, False, error_message="error", execution_time_ms=1.0),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        # 2 errors out of 4 operations = 50%
        assert stats.error_rate == 50.0
        assert stats.total_errors == 2

    def test_generate_average_execution_time(self):
        """Test generate() average execution time calculation."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=2.0),
            MemoryEntry("add", 3.0, 4.0, 7.0, True, execution_time_ms=4.0),
            MemoryEntry("add", 5.0, 6.0, 11.0, True, execution_time_ms=6.0),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        # (2 + 4 + 6) / 3 = 12 / 3 = 4.0
        assert stats.avg_execution_time_ms == 4.0

    def test_generate_all_operations_initialized(self):
        """Test generate() initializes all operation types even if not present."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        # All operations should be in the counts dict, even if 0
        assert "add" in stats.operation_counts
        assert "subtract" in stats.operation_counts
        assert "multiply" in stats.operation_counts
        assert "divide" in stats.operation_counts
        assert "square" in stats.operation_counts
        assert "sqrt" in stats.operation_counts
        assert "power" in stats.operation_counts
        assert "modulo" in stats.operation_counts

    def test_generate_returns_frozen_dataclass(self):
        """Test that generate() returns a frozen CalculationStatistics."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        # Try to modify the frozen dataclass - should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError is raised as Exception
            stats.total_errors = 10

    def test_generate_with_mixed_success_and_failure(self):
        """Test generate() with mixed successful and failed operations."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("subtract", 5.0, 3.0, 2.0, True, execution_time_ms=1.5),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, execution_time_ms=2.0),
            MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero", execution_time_ms=1.0),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, error_message="negative", execution_time_ms=0.5),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert stats.operation_counts["add"] == 1
        assert stats.operation_counts["subtract"] == 1
        assert stats.operation_counts["multiply"] == 1
        assert stats.operation_counts["divide"] == 1
        assert stats.operation_counts["sqrt"] == 1
        assert stats.total_errors == 2
        # 2 errors out of 5 = 40%
        assert stats.error_rate == 40.0
        # (1 + 1.5 + 2 + 1 + 0.5) / 5 = 6 / 5 = 1.2
        assert stats.avg_execution_time_ms == 1.2

    def test_generate_calls_get_all_entries(self):
        """Test that generate() calls memory_service.get_all_entries()."""
        memory_service = MagicMock()
        memory_service.get_all_entries.return_value = []
        stats_service = StatisticsService(memory_service)

        stats_service.generate()

        memory_service.get_all_entries.assert_called_once()

    def test_generate_with_all_operation_types(self):
        """Test generate() with all 8 operation types."""
        memory_service = MagicMock()
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("subtract", 5.0, 3.0, 2.0, True, execution_time_ms=1.0),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, execution_time_ms=1.0),
            MemoryEntry("divide", 9.0, 3.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("square", 5.0, 0.0, 25.0, True, execution_time_ms=1.0),
            MemoryEntry("sqrt", 9.0, 0.0, 3.0, True, execution_time_ms=1.0),
            MemoryEntry("power", 2.0, 3.0, 8.0, True, execution_time_ms=1.0),
            MemoryEntry("modulo", 10.0, 3.0, 1.0, True, execution_time_ms=1.0),
        ]
        memory_service.get_all_entries.return_value = entries
        stats_service = StatisticsService(memory_service)

        stats = stats_service.generate()

        assert stats.operation_counts["add"] == 1
        assert stats.operation_counts["subtract"] == 1
        assert stats.operation_counts["multiply"] == 1
        assert stats.operation_counts["divide"] == 1
        assert stats.operation_counts["square"] == 1
        assert stats.operation_counts["sqrt"] == 1
        assert stats.operation_counts["power"] == 1
        assert stats.operation_counts["modulo"] == 1
        assert stats.total_errors == 0
        assert stats.error_rate == 0.0
        assert stats.avg_execution_time_ms == 1.0
