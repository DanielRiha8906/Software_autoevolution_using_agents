import pytest
from unittest.mock import MagicMock
from src.models.statistics import CalculationStatistics
from src.models.memory_entry import MemoryEntry
from src.services.statistics_service import StatisticsService
from src.cli.calculator_cli import CalculatorCLI


class TestCalculationStatistics:
    """Test the CalculationStatistics dataclass."""

    def test_valid_construction_all_zeros(self):
        """Can construct with zero values."""
        stats = CalculationStatistics(
            total_calculations=0,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={},
            average_execution_time_ms=0.0,
        )
        assert stats.total_calculations == 0
        assert stats.total_errors == 0
        assert stats.error_rate_percent == 0.0
        assert stats.operations_count == {}
        assert stats.average_execution_time_ms == 0.0

    def test_valid_construction_partial_errors(self):
        """Can construct with partial error rate."""
        stats = CalculationStatistics(
            total_calculations=10,
            total_errors=3,
            error_rate_percent=30.0,
            operations_count={"add": 5, "divide": 5},
            average_execution_time_ms=1.5,
        )
        assert stats.total_calculations == 10
        assert stats.total_errors == 3
        assert stats.error_rate_percent == 30.0
        assert stats.operations_count == {"add": 5, "divide": 5}
        assert stats.average_execution_time_ms == 1.5

    def test_valid_construction_all_errors(self):
        """Can construct with error_rate_percent = 100.0."""
        stats = CalculationStatistics(
            total_calculations=5,
            total_errors=5,
            error_rate_percent=100.0,
            operations_count={"divide": 5},
            average_execution_time_ms=2.0,
        )
        assert stats.error_rate_percent == 100.0

    def test_valid_construction_no_errors(self):
        """Can construct with error_rate_percent = 0.0."""
        stats = CalculationStatistics(
            total_calculations=5,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={"add": 5},
            average_execution_time_ms=1.0,
        )
        assert stats.error_rate_percent == 0.0

    def test_valid_construction_boundary_low(self):
        """Boundary case: error_rate_percent at 0."""
        stats = CalculationStatistics(
            total_calculations=1,
            total_errors=0,
            error_rate_percent=0,
            operations_count={},
            average_execution_time_ms=0.0,
        )
        assert stats.error_rate_percent == 0

    def test_valid_construction_boundary_high(self):
        """Boundary case: error_rate_percent at 100."""
        stats = CalculationStatistics(
            total_calculations=1,
            total_errors=1,
            error_rate_percent=100,
            operations_count={},
            average_execution_time_ms=0.0,
        )
        assert stats.error_rate_percent == 100

    def test_error_rate_validation_negative(self):
        """Raises ValueError when error_rate_percent < 0."""
        with pytest.raises(ValueError) as exc_info:
            CalculationStatistics(
                total_calculations=1,
                total_errors=0,
                error_rate_percent=-0.1,
                operations_count={},
                average_execution_time_ms=0.0,
            )
        assert "error_rate_percent must be between 0 and 100" in str(exc_info.value)

    def test_error_rate_validation_too_high(self):
        """Raises ValueError when error_rate_percent > 100."""
        with pytest.raises(ValueError) as exc_info:
            CalculationStatistics(
                total_calculations=1,
                total_errors=1,
                error_rate_percent=100.1,
                operations_count={},
                average_execution_time_ms=0.0,
            )
        assert "error_rate_percent must be between 0 and 100" in str(exc_info.value)

    def test_error_rate_validation_way_too_high(self):
        """Raises ValueError for significantly out-of-range error_rate_percent."""
        with pytest.raises(ValueError):
            CalculationStatistics(
                total_calculations=10,
                total_errors=10,
                error_rate_percent=150.0,
                operations_count={},
                average_execution_time_ms=0.0,
            )

    def test_valid_construction_with_multiple_operations(self):
        """Can construct with complex operations_count dict."""
        ops = {"add": 3, "subtract": 2, "divide": 4, "multiply": 1}
        stats = CalculationStatistics(
            total_calculations=10,
            total_errors=1,
            error_rate_percent=10.0,
            operations_count=ops,
            average_execution_time_ms=2.5,
        )
        assert stats.operations_count == ops

    def test_valid_construction_high_precision_execution_time(self):
        """Can construct with high-precision execution time."""
        stats = CalculationStatistics(
            total_calculations=1,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={},
            average_execution_time_ms=1.234567,
        )
        assert stats.average_execution_time_ms == 1.234567


class TestStatisticsService:
    """Test StatisticsService.calculate_statistics() method."""

    @pytest.fixture
    def mock_memory_service(self):
        """Create a mock memory service."""
        return MagicMock()

    def test_empty_history_returns_all_zeros(self, mock_memory_service):
        """Empty entry list returns all-zero statistics."""
        mock_memory_service.retrieve.return_value = []
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 0
        assert stats.total_errors == 0
        assert stats.error_rate_percent == 0.0
        assert stats.operations_count == {}
        assert stats.average_execution_time_ms == 0.0

    def test_single_success_entry(self, mock_memory_service):
        """Single successful entry: total=1, errors=0, rate=0.0."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
            execution_time_ms=1.5,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        mock_memory_service.retrieve.return_value = [entry]
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 1
        assert stats.total_errors == 0
        assert stats.error_rate_percent == 0.0
        assert stats.operations_count == {"add": 1}
        assert stats.average_execution_time_ms == 1.5

    def test_single_error_entry(self, mock_memory_service):
        """Single error entry: total=1, errors=1, rate=100.0."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero is not allowed",
            error_type="ValueError",
            execution_time_ms=0.8,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        mock_memory_service.retrieve.return_value = [entry]
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 1
        assert stats.total_errors == 1
        assert stats.error_rate_percent == 100.0
        assert stats.operations_count == {"divide": 1}
        assert stats.average_execution_time_ms == 0.8

    def test_multiple_entries_mixed_success_error(self, mock_memory_service):
        """Multiple entries with mixed success/error."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                result=8,
                error=None,
                error_type=None,
                execution_time_ms=1.0,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="divide",
                operand_a=5,
                operand_b=0,
                result=None,
                error="Division by zero",
                error_type="ValueError",
                execution_time_ms=0.5,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
            MemoryEntry(
                operation="add",
                operand_a=10,
                operand_b=20,
                result=30,
                error=None,
                error_type=None,
                execution_time_ms=1.5,
                timestamp="2026-05-03T14:32:00",
                uuid="550e8400-e29b-41d4-a716-446655440003",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 3
        assert stats.total_errors == 1
        # (1 / 3) * 100 = 33.333... rounded to 2 decimals = 33.33
        assert stats.error_rate_percent == 33.33
        assert stats.operations_count == {"add": 2, "divide": 1}
        # (1.0 + 0.5 + 1.5) / 3 = 3.0 / 3 = 1.0
        assert stats.average_execution_time_ms == 1.0

    def test_error_rate_rounding_to_two_decimals(self, mock_memory_service):
        """error_rate_percent is rounded to 2 decimals."""
        entries = [
            MemoryEntry(
                operation="divide",
                operand_a=1,
                operand_b=3,
                result=None,
                error="Division error",
                error_type="ValueError",
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
        ] * 3  # 3 error entries
        entries.extend([
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
        ] * 7)  # 7 success entries
        # Total = 10, errors = 3, rate = 30.0
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.error_rate_percent == 30.0

    def test_error_rate_complex_rounding(self, mock_memory_service):
        """error_rate_percent with values requiring rounding."""
        # 1 error, 2 success = 33.333...% should round to 33.33
        entries = [
            MemoryEntry(
                operation="divide",
                operand_a=1,
                operand_b=0,
                result=None,
                error="error",
                error_type="ValueError",
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
            MemoryEntry(
                operation="add",
                operand_a=2,
                operand_b=2,
                result=4,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:32:00",
                uuid="550e8400-e29b-41d4-a716-446655440003",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        # 1/3 * 100 = 33.333..., rounded to 2 decimals = 33.33
        assert stats.error_rate_percent == 33.33

    def test_average_execution_time_rounding_to_six_decimals(self, mock_memory_service):
        """average_execution_time_ms is rounded to 6 decimals."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.1111115,  # Will be averaged
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="add",
                operand_a=2,
                operand_b=2,
                result=4,
                error=None,
                error_type=None,
                execution_time_ms=0.2222225,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
        ]
        # (0.1111115 + 0.2222225) / 2 = 0.333334 / 2 = 0.166667
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        # Should be rounded to 6 decimals
        assert stats.average_execution_time_ms == round((0.1111115 + 0.2222225) / 2, 6)

    def test_operations_count_with_single_operation(self, mock_memory_service):
        """operations_count tracks counts of each operation type."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="add",
                operand_a=2,
                operand_b=2,
                result=4,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.operations_count == {"add": 2}

    def test_operations_count_with_multiple_operations(self, mock_memory_service):
        """operations_count with multiple operation types."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="divide",
                operand_a=10,
                operand_b=2,
                result=5,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=3,
                result=6,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:32:00",
                uuid="550e8400-e29b-41d4-a716-446655440003",
            ),
            MemoryEntry(
                operation="multiply",
                operand_a=5,
                operand_b=5,
                result=25,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:33:00",
                uuid="550e8400-e29b-41d4-a716-446655440004",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.operations_count == {"add": 2, "divide": 1, "multiply": 1}

    def test_all_error_entries(self, mock_memory_service):
        """All entries are errors."""
        entries = [
            MemoryEntry(
                operation="divide",
                operand_a=1,
                operand_b=0,
                result=None,
                error="Division by zero",
                error_type="ValueError",
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="sqrt",
                operand_a=-1,
                operand_b=0,
                result=None,
                error="Cannot take sqrt of negative",
                error_type="ValueError",
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
            MemoryEntry(
                operation="divide",
                operand_a=5,
                operand_b=0,
                result=None,
                error="Division by zero",
                error_type="ValueError",
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:32:00",
                uuid="550e8400-e29b-41d4-a716-446655440003",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 3
        assert stats.total_errors == 3
        assert stats.error_rate_percent == 100.0
        assert stats.operations_count == {"divide": 2, "sqrt": 1}

    def test_all_success_entries(self, mock_memory_service):
        """All entries are successful."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=i,
                operand_b=i,
                result=i * 2,
                error=None,
                error_type=None,
                execution_time_ms=0.1,
                timestamp="2026-05-03T14:30:00",
                uuid=f"550e8400-e29b-41d4-a716-44665544000{i}",
            )
            for i in range(5)
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 5
        assert stats.total_errors == 0
        assert stats.error_rate_percent == 0.0
        assert stats.operations_count == {"add": 5}

    def test_execution_time_zero_values(self, mock_memory_service):
        """Handles execution times of 0.0."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.0,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="add",
                operand_a=2,
                operand_b=2,
                result=4,
                error=None,
                error_type=None,
                execution_time_ms=0.0,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.average_execution_time_ms == 0.0

    def test_execution_time_mixed_values(self, mock_memory_service):
        """Handles mix of zero and non-zero execution times."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
                execution_time_ms=0.0,
                timestamp="2026-05-03T14:30:00",
                uuid="550e8400-e29b-41d4-a716-446655440001",
            ),
            MemoryEntry(
                operation="add",
                operand_a=2,
                operand_b=2,
                result=4,
                error=None,
                error_type=None,
                execution_time_ms=2.0,
                timestamp="2026-05-03T14:31:00",
                uuid="550e8400-e29b-41d4-a716-446655440002",
            ),
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        # (0.0 + 2.0) / 2 = 1.0
        assert stats.average_execution_time_ms == 1.0

    def test_large_number_of_entries(self, mock_memory_service):
        """Handles large number of entries."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=i,
                operand_b=i,
                result=i * 2,
                error=None,
                error_type=None,
                execution_time_ms=0.5,
                timestamp="2026-05-03T14:30:00",
                uuid=f"550e8400-e29b-41d4-a716-{str(i).zfill(12)}",
            )
            for i in range(1000)
        ]
        mock_memory_service.retrieve.return_value = entries
        service = StatisticsService(mock_memory_service)

        stats = service.calculate_statistics()

        assert stats.total_calculations == 1000
        assert stats.total_errors == 0
        assert stats.error_rate_percent == 0.0
        assert stats.operations_count == {"add": 1000}
        assert stats.average_execution_time_ms == 0.5


class TestCLIIntegration:
    """Test CalculatorCLI._show_statistics() integration with StatisticsService."""

    def test_show_statistics_displays_output(self, capsys):
        """_show_statistics() displays statistics output."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=10,
            total_errors=2,
            error_rate_percent=20.0,
            operations_count={"add": 5, "divide": 5},
            average_execution_time_ms=1.5,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        assert "Calculation Statistics" in captured.out
        assert "Total Calculations: 10" in captured.out
        assert "Total Errors: 2" in captured.out
        assert "Error Rate: 20.0%" in captured.out
        assert "Average Execution Time: 1.5 ms" in captured.out

    def test_show_statistics_displays_operations_count(self, capsys):
        """_show_statistics() displays operations breakdown."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=5,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={"add": 2, "divide": 3},
            average_execution_time_ms=1.0,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        assert "add: 2" in captured.out
        assert "divide: 3" in captured.out

    def test_show_statistics_empty_operations_count(self, capsys):
        """_show_statistics() handles empty operations_count."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=0,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={},
            average_execution_time_ms=0.0,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        assert "(none)" in captured.out

    def test_show_statistics_single_operation_type(self, capsys):
        """_show_statistics() displays single operation correctly."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=1,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={"multiply": 1},
            average_execution_time_ms=0.5,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        assert "multiply: 1" in captured.out

    def test_show_statistics_all_error_scenario(self, capsys):
        """_show_statistics() displays 100% error rate."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=5,
            total_errors=5,
            error_rate_percent=100.0,
            operations_count={"divide": 5},
            average_execution_time_ms=0.8,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        assert "Error Rate: 100.0%" in captured.out
        assert "Total Errors: 5" in captured.out

    def test_show_statistics_operations_count_sorted(self, capsys):
        """_show_statistics() displays operations sorted by name."""
        mock_service = MagicMock()
        mock_stats_service = MagicMock()
        mock_stats_service.calculate_statistics.return_value = CalculationStatistics(
            total_calculations=6,
            total_errors=0,
            error_rate_percent=0.0,
            operations_count={"multiply": 2, "add": 1, "subtract": 3},
            average_execution_time_ms=1.0,
        )
        cli = CalculatorCLI(mock_service, mock_stats_service)

        cli._show_statistics()

        captured = capsys.readouterr()
        # Verify all operations are present
        assert "add: 1" in captured.out
        assert "subtract: 3" in captured.out
        assert "multiply: 2" in captured.out
        # Verify they appear in alphabetical order by checking positions
        lines = captured.out.split('\n')
        # Find the lines that contain the operation counts
        op_lines = [line for line in lines if ': ' in line and any(op in line for op in ['add:', 'subtract:', 'multiply:'])]
        assert len(op_lines) >= 3
        # Check order in the output
        assert op_lines[0].strip().startswith('add')
        assert op_lines[1].strip().startswith('multiply')
        assert op_lines[2].strip().startswith('subtract')


class TestMemoryEntryExecutionTimeField:
    """Test execution_time_ms field in MemoryEntry."""

    def test_execution_time_ms_default(self):
        """execution_time_ms defaults to 0.0."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert entry.execution_time_ms == 0.0

    def test_execution_time_ms_explicit_value(self):
        """execution_time_ms can be set explicitly."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
            execution_time_ms=5.5,
        )
        assert entry.execution_time_ms == 5.5

    def test_from_dict_preserves_execution_time_ms(self):
        """from_dict() preserves execution_time_ms when present."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "error": None,
            "error_type": None,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "execution_time_ms": 2.75,
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.execution_time_ms == 2.75

    def test_from_dict_defaults_execution_time_ms_to_zero(self):
        """from_dict() defaults execution_time_ms to 0.0 when absent."""
        data = {
            "operation": "divide",
            "operand_a": 10,
            "operand_b": 2,
            "result": 5,
            "error": None,
            "error_type": None,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.execution_time_ms == 0.0

    def test_to_dict_includes_execution_time_ms(self):
        """to_dict() includes execution_time_ms field."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
            execution_time_ms=3.2,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = entry.to_dict()
        assert d["execution_time_ms"] == 3.2

    def test_round_trip_preserves_execution_time_ms(self):
        """Round-trip through to_dict() and from_dict() preserves execution_time_ms."""
        original = MemoryEntry(
            operation="multiply",
            operand_a=4,
            operand_b=5,
            result=20,
            error=None,
            error_type=None,
            execution_time_ms=1.23,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = original.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.execution_time_ms == original.execution_time_ms

    def test_execution_time_ms_high_precision(self):
        """execution_time_ms can store high-precision values."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
            execution_time_ms=0.123456789,
        )
        assert entry.execution_time_ms == 0.123456789
