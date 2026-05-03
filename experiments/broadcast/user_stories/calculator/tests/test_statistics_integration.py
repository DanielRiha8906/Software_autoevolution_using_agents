"""Integration tests for StatisticsService with real storage."""

import pytest
import tempfile
from pathlib import Path
from src.cli.calculator_cli import CalculatorCLI
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.services.statistics_service import StatisticsService
from src.services.calculator import Calculator
from src.storage.json_storage import JsonStorage
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter


@pytest.fixture
def temp_storage_path():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


class TestStatisticsIntegration:
    """Test StatisticsService with real data flow."""

    def test_statistics_from_stored_entries(self, temp_storage_path):
        """Test statistics computation with actual stored entries."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        memory_service = MemoryService(storage)
        stats_service = StatisticsService(memory_service)

        # Store test data
        memory_service.store(ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0))
        memory_service.store(ResultEntry(operation="add", operands=[5, 5], result=10, execution_time_ms=1.5))
        memory_service.store(ErrorEntry(operation="divide", operands=[10, 0], error_message="Division by zero", execution_time_ms=0.5))
        memory_service.store(ResultEntry(operation="multiply", operands=[3, 4], result=12, execution_time_ms=2.0))

        stats = stats_service.compute_statistics()

        assert stats.operation_counts == {"add": 2, "divide": 1, "multiply": 1}
        assert stats.total_errors == 1
        assert stats.error_rate_percentage == 25.0
        assert stats.average_execution_time_ms == 1.25  # (1.0 + 1.5 + 0.5 + 2.0) / 4

    def test_statistics_via_calculator_service(self, temp_storage_path):
        """Test statistics from entries created by CalculatorService."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        calc_service = CalculatorService(Calculator(), storage)
        memory_service = MemoryService(storage)
        stats_service = StatisticsService(memory_service)

        # Perform some calculations (stores in both places)
        from src.models.operation import Operation
        calc_service.perform_with_memory(Operation.ADD, 10, 5)
        calc_service.perform_with_memory(Operation.SUBTRACT, 20, 8)

        stats = stats_service.compute_statistics()

        assert len(stats.operation_counts) == 2
        assert stats.operation_counts.get("add", 0) == 1
        assert stats.operation_counts.get("subtract", 0) == 1
        assert stats.total_errors == 0
        assert stats.error_rate_percentage == 0.0

    def test_statistics_via_cli(self, temp_storage_path, capsys):
        """Test statistics display through CLI."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        calc_service = CalculatorService(Calculator(), storage)
        memory_service = MemoryService(storage)
        cli = CalculatorCLI(calc_service, memory_service)

        # Add some data
        memory_service.store(ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0))
        memory_service.store(ErrorEntry(operation="divide", operands=[10, 0], error_message="error", execution_time_ms=0.5))

        # Call statistics command
        cli.statistics_command()
        captured = capsys.readouterr()

        output = captured.out
        assert "Statistics" in output
        assert "add: 1" in output
        assert "divide: 1" in output
        assert "Total errors: 1" in output
        assert "Error rate: 50.00%" in output
        assert "Average execution time: 0.75ms" in output

    def test_statistics_empty_memory(self, temp_storage_path):
        """Test statistics with empty storage."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        memory_service = MemoryService(storage)
        stats_service = StatisticsService(memory_service)

        stats = stats_service.compute_statistics()

        assert isinstance(stats.operation_counts, dict)
        assert len(stats.operation_counts) == 0
        assert stats.total_errors == 0
        assert stats.error_rate_percentage == 0.0
        assert stats.average_execution_time_ms == 0.0

    def test_statistics_reflects_latest_state(self, temp_storage_path):
        """Test that statistics reflect current storage state."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        memory_service = MemoryService(storage)
        stats_service = StatisticsService(memory_service)

        # Initially empty
        stats = stats_service.compute_statistics()
        assert stats.total_errors == 0

        # Add one entry
        memory_service.store(ResultEntry(operation="add", operands=[1, 2], result=3, execution_time_ms=1.0))
        stats = stats_service.compute_statistics()
        assert stats.operation_counts.get("add") == 1

        # Add error
        memory_service.store(ErrorEntry(operation="add", operands=[1, 2], error_message="error", execution_time_ms=0.5))
        stats = stats_service.compute_statistics()
        assert stats.operation_counts.get("add") == 2
        assert stats.total_errors == 1
        assert stats.error_rate_percentage == 50.0

    def test_statistics_with_many_operations(self, temp_storage_path):
        """Test statistics accuracy with many different operations."""
        _reset_id_counter()
        storage = JsonStorage(temp_storage_path)
        memory_service = MemoryService(storage)
        stats_service = StatisticsService(memory_service)

        # Store diverse data (all 8 operation types)
        operations = [
            ("add", 1.0),
            ("add", 1.2),
            ("subtract", 0.9),
            ("multiply", 1.1),
            ("divide", 0.8),
            ("square", 1.5),
            ("sqrt", 1.3),
            ("power", 1.4),
            ("modulo", 1.0),
        ]

        for op, time_ms in operations:
            memory_service.store(
                ResultEntry(
                    operation=op,
                    operands=[1.0, 2.0],
                    result=0.0,
                    execution_time_ms=time_ms,
                )
            )

        # Add some errors
        memory_service.store(
            ErrorEntry(
                operation="divide",
                operands=[1.0, 0.0],
                error_message="error",
                execution_time_ms=0.5,
            )
        )
        memory_service.store(
            ErrorEntry(
                operation="sqrt",
                operands=[-1.0],
                error_message="error",
                execution_time_ms=0.6,
            )
        )

        stats = stats_service.compute_statistics()

        assert len(stats.operation_counts) == 8  # All 8 operation types have entries
        assert stats.operation_counts["add"] == 2
        assert stats.operation_counts["divide"] == 2  # 1 success + 1 error
        assert stats.operation_counts["sqrt"] == 2  # 1 success + 1 error
        assert stats.operation_counts["subtract"] == 1
        assert stats.operation_counts["multiply"] == 1
        assert stats.operation_counts["square"] == 1
        assert stats.operation_counts["power"] == 1
        assert stats.operation_counts["modulo"] == 1
        assert stats.total_errors == 2
        # 9 successes + 2 errors = 11 total entries, so 2/11 = 18.18%
        assert stats.error_rate_percentage == pytest.approx(18.18, abs=0.01)
