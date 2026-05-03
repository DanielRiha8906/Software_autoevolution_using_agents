import pytest
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.calculator_service import CalculatorService
from src.services.calculator import Calculator
from src.models.operation import Operation


_TS1 = "2026-05-03T10:00:00"
_TS2 = "2026-05-03T10:01:00"
_TS3 = "2026-05-03T10:02:00"
_TS4 = "2026-05-03T10:03:00"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_storage():
    """Create a mock JsonStorage."""
    return MagicMock()


@pytest.fixture
def memory_service(mock_storage):
    """Create a MemoryService with mock storage."""
    return MemoryService(mock_storage)


@pytest.fixture
def empty_storage(mock_storage):
    """Mock storage that returns empty list."""
    mock_storage.load_all.return_value = []
    return mock_storage


@pytest.fixture
def sample_entries():
    """Create sample MemoryEntry objects for testing."""
    return [
        MemoryEntry("add", 5, 3, 8, None, None, _TS1),
        MemoryEntry("subtract", 5, 3, 2, None, None, _TS2),
        MemoryEntry("divide", 10, 0, None, "Division by zero is not allowed", "ZeroDivisionError", _TS3),
        MemoryEntry("multiply", 4, 5, 20, None, None, _TS4),
    ]


@pytest.fixture
def populated_storage(mock_storage, sample_entries):
    """Mock storage that returns sample entries."""
    mock_storage.load_all.return_value = sample_entries
    return mock_storage


# ============================================================================
# Tests for MemoryService.filter_by_operation()
# ============================================================================

class TestFilterByOperation:
    """Test MemoryService.filter_by_operation()"""

    def test_filter_by_operation_single_match(self, memory_service, populated_storage):
        """Filter returns matching operation."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operation("add")

        assert len(result) == 1
        assert result[0].operation == "add"
        assert result[0].operand_a == 5
        assert result[0].operand_b == 3

    def test_filter_by_operation_multiple_matches(self, mock_storage, memory_service):
        """Filter returns all entries matching operation."""
        entries = [
            MemoryEntry("add", 5, 3, 8, None, None, _TS1),
            MemoryEntry("add", 10, 2, 12, None, None, _TS2),
            MemoryEntry("subtract", 5, 3, 2, None, None, _TS3),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_operation("add")

        assert len(result) == 2
        assert all(e.operation == "add" for e in result)
        assert result[0].operand_a == 5
        assert result[1].operand_a == 10

    def test_filter_by_operation_no_matches(self, memory_service, populated_storage):
        """Filter returns empty list when no matches."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operation("power")

        assert result == []

    def test_filter_by_operation_empty_storage(self, memory_service, empty_storage):
        """Filter returns empty list for empty storage."""
        memory_service.storage = empty_storage
        result = memory_service.filter_by_operation("add")

        assert result == []

    def test_filter_by_operation_preserves_order(self, mock_storage, memory_service):
        """Filter preserves chronological order."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("add", 5, 5, 10, None, None, _TS2),
            MemoryEntry("add", 10, 10, 20, None, None, _TS3),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_operation("add")

        assert len(result) == 3
        assert result[0].operand_a == 1
        assert result[1].operand_a == 5
        assert result[2].operand_a == 10

    def test_filter_by_operation_case_sensitive(self, memory_service, populated_storage):
        """Filter is case-sensitive."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operation("ADD")

        assert result == []


# ============================================================================
# Tests for MemoryService.filter_by_operations()
# ============================================================================

class TestFilterByOperations:
    """Test MemoryService.filter_by_operations()"""

    def test_filter_by_operations_single_operation(self, memory_service, populated_storage):
        """Filter with single operation in list."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations(["add"])

        assert len(result) == 1
        assert result[0].operation == "add"

    def test_filter_by_operations_multiple_operations(self, memory_service, populated_storage):
        """Filter with multiple operations returns all matching."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations(["add", "multiply"])

        assert len(result) == 2
        ops = [e.operation for e in result]
        assert "add" in ops
        assert "multiply" in ops

    def test_filter_by_operations_empty_list(self, memory_service, populated_storage):
        """Filter with empty operation list returns all entries."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations([])

        # Empty list means no filtering by operation
        assert len(result) == 0

    def test_filter_by_operations_invalid_operation(self, memory_service, populated_storage):
        """Filter with invalid operation name returns empty."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations(["invalid_op"])

        assert result == []

    def test_filter_by_operations_all_operations(self, memory_service, populated_storage):
        """Filter with all valid operations."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations(["add", "subtract", "divide", "multiply"])

        assert len(result) == 4

    def test_filter_by_operations_duplicates_in_list(self, memory_service, populated_storage):
        """Filter handles duplicate operation names in list."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_operations(["add", "add", "add"])

        # Should still return just one entry
        assert len(result) == 1
        assert result[0].operation == "add"

    def test_filter_by_operations_preserves_order(self, mock_storage, memory_service):
        """Filter preserves chronological order."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("multiply", 5, 5, 25, None, None, _TS2),
            MemoryEntry("add", 10, 10, 20, None, None, _TS3),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_operations(["add", "multiply"])

        assert len(result) == 3
        assert result[0].operation == "add"
        assert result[1].operation == "multiply"
        assert result[2].operation == "add"


# ============================================================================
# Tests for MemoryService.filter_by_state()
# ============================================================================

class TestFilterByState:
    """Test MemoryService.filter_by_state()"""

    def test_filter_by_state_success_only(self, memory_service, populated_storage):
        """Filter by state='success' returns only successful entries."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_state("success")

        assert len(result) == 3
        assert all(e.result is not None and e.error is None for e in result)
        assert all(op in [e.operation for e in result] for op in ["add", "subtract", "multiply"])

    def test_filter_by_state_error_only(self, memory_service, populated_storage):
        """Filter by state='error' returns only error entries."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_state("error")

        assert len(result) == 1
        assert result[0].operation == "divide"
        assert result[0].error is not None
        assert result[0].result is None

    def test_filter_by_state_both(self, memory_service, populated_storage):
        """Filter by state='both' returns all entries."""
        memory_service.storage = populated_storage
        result = memory_service.filter_by_state("both")

        assert len(result) == 4

    def test_filter_by_state_success_empty(self, mock_storage, memory_service):
        """Filter by state='success' with no successful entries returns empty."""
        entries = [
            MemoryEntry("divide", 10, 0, None, "Division by zero", "ValueError", _TS1),
            MemoryEntry("sqrt", -1, 0, None, "Cannot take sqrt", "ValueError", _TS2),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_state("success")

        assert result == []

    def test_filter_by_state_error_empty(self, mock_storage, memory_service):
        """Filter by state='error' with no error entries returns empty."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("multiply", 5, 5, 25, None, None, _TS2),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_state("error")

        assert result == []

    def test_filter_by_state_invalid_state(self, memory_service, populated_storage):
        """Filter with invalid state raises ValueError."""
        memory_service.storage = populated_storage

        with pytest.raises(ValueError) as exc_info:
            memory_service.filter_by_state("invalid")

        assert "Invalid state" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_filter_by_state_case_sensitive(self, memory_service, populated_storage):
        """Filter state is case-sensitive."""
        memory_service.storage = populated_storage

        with pytest.raises(ValueError):
            memory_service.filter_by_state("SUCCESS")

    def test_filter_by_state_preserves_order(self, mock_storage, memory_service):
        """Filter preserves chronological order."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("multiply", 5, 5, 25, None, None, _TS2),
            MemoryEntry("subtract", 10, 3, 7, None, None, _TS3),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter_by_state("success")

        assert len(result) == 3
        assert result[0].operation == "add"
        assert result[1].operation == "multiply"
        assert result[2].operation == "subtract"


# ============================================================================
# Tests for MemoryService.filter() combined
# ============================================================================

class TestFilterCombined:
    """Test MemoryService.filter() with multiple criteria"""

    def test_filter_both_operations_and_state(self, memory_service, populated_storage):
        """Filter by both operations and state."""
        memory_service.storage = populated_storage
        result = memory_service.filter(operations=["add", "divide"], state="success")

        # Only "add" is successful, "divide" is error
        assert len(result) == 1
        assert result[0].operation == "add"
        assert result[0].result == 8

    def test_filter_multiple_operations_and_success(self, mock_storage, memory_service):
        """Filter multiple operations with success state."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("add", 5, 5, 10, None, None, _TS2),
            MemoryEntry("divide", 10, 0, None, "Division by zero", "ValueError", _TS3),
            MemoryEntry("multiply", 2, 3, 6, None, None, _TS4),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter(operations=["add", "multiply"], state="success")

        assert len(result) == 3
        ops = [e.operation for e in result]
        assert ops.count("add") == 2
        assert ops.count("multiply") == 1

    def test_filter_operations_none_state_specified(self, memory_service, populated_storage):
        """Filter with operations=None and state specified."""
        memory_service.storage = populated_storage
        result = memory_service.filter(operations=None, state="success")

        # Should return all successful entries
        assert len(result) == 3
        assert all(e.result is not None for e in result)

    def test_filter_operations_specified_state_none(self, memory_service, populated_storage):
        """Filter with operations specified and state=None."""
        memory_service.storage = populated_storage
        result = memory_service.filter(operations=["add", "divide"], state=None)

        # Should return all add and divide entries (including error)
        assert len(result) == 2
        ops = [e.operation for e in result]
        assert "add" in ops
        assert "divide" in ops

    def test_filter_both_none_returns_all(self, memory_service, populated_storage):
        """Filter with both operations and state as None returns all."""
        memory_service.storage = populated_storage
        result = memory_service.filter(operations=None, state=None)

        assert len(result) == 4

    def test_filter_no_results_match_criteria(self, mock_storage, memory_service):
        """Filter returns empty when no results match all criteria."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("divide", 10, 0, None, "Division by zero", "ValueError", _TS2),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter(operations=["multiply", "power"], state="success")

        assert result == []

    def test_filter_preserves_order(self, mock_storage, memory_service):
        """Filter preserves chronological order."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("add", 5, 5, 10, None, None, _TS2),
            MemoryEntry("divide", 10, 0, None, "Error", "ValueError", _TS3),
            MemoryEntry("add", 10, 10, 20, None, None, _TS4),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter(operations=["add"], state="success")

        assert len(result) == 3
        assert result[0].operand_a == 1
        assert result[1].operand_a == 5
        assert result[2].operand_a == 10

    def test_filter_error_state_no_operations(self, mock_storage, memory_service):
        """Filter by error state without operation filtering."""
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("divide", 10, 0, None, "Division by zero", "ValueError", _TS2),
            MemoryEntry("sqrt", -1, 0, None, "Cannot take sqrt", "ValueError", _TS3),
            MemoryEntry("multiply", 5, 5, 25, None, None, _TS4),
        ]
        mock_storage.load_all.return_value = entries
        memory_service.storage = mock_storage

        result = memory_service.filter(operations=None, state="error")

        assert len(result) == 2
        ops = [e.operation for e in result]
        assert "divide" in ops
        assert "sqrt" in ops

    def test_filter_invalid_state_raises_error(self, memory_service, populated_storage):
        """Filter with invalid state raises ValueError."""
        memory_service.storage = populated_storage

        with pytest.raises(ValueError) as exc_info:
            memory_service.filter(operations=["add"], state="invalid_state")

        assert "Invalid state" in str(exc_info.value)

    def test_filter_empty_operations_list(self, memory_service, populated_storage):
        """Filter with empty operations list acts as no filtering."""
        memory_service.storage = populated_storage
        result = memory_service.filter(operations=[], state="success")

        # Empty operations list means no operation filtering
        assert len(result) == 3
        assert all(e.result is not None for e in result)


# ============================================================================
# Tests for CalculatorService.filter_history()
# ============================================================================

class TestCalculatorServiceFilterHistory:
    """Test CalculatorService.filter_history()"""

    @pytest.fixture
    def calculator_service(self, mock_storage):
        """Create a CalculatorService with mocked dependencies."""
        memory_service = MemoryService(mock_storage)
        calculator = MagicMock(spec=Calculator)
        service = CalculatorService(calculator, memory_service)
        return service, mock_storage

    def test_filter_history_delegates_to_memory_service(self, calculator_service):
        """filter_history delegates to memory_service.filter()."""
        service, mock_storage = calculator_service
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("divide", 10, 0, None, "Error", "ValueError", _TS2),
        ]
        mock_storage.load_all.return_value = entries

        result = service.filter_history(operations=["add"], state="success")

        assert len(result) == 1
        assert result[0].operation == "add"

    def test_filter_history_propagates_errors(self, calculator_service):
        """filter_history propagates ValueError from memory_service."""
        service, mock_storage = calculator_service
        mock_storage.load_all.return_value = []

        with pytest.raises(ValueError) as exc_info:
            service.filter_history(operations=["add"], state="invalid_state")

        assert "Invalid state" in str(exc_info.value)

    def test_filter_history_no_arguments(self, calculator_service):
        """filter_history works with no arguments."""
        service, mock_storage = calculator_service
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("divide", 10, 0, None, "Error", "ValueError", _TS2),
        ]
        mock_storage.load_all.return_value = entries

        result = service.filter_history()

        assert len(result) == 2

    def test_filter_history_operations_only(self, calculator_service):
        """filter_history with operations parameter only."""
        service, mock_storage = calculator_service
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("multiply", 5, 5, 25, None, None, _TS2),
        ]
        mock_storage.load_all.return_value = entries

        result = service.filter_history(operations=["add"])

        assert len(result) == 1
        assert result[0].operation == "add"

    def test_filter_history_state_only(self, calculator_service):
        """filter_history with state parameter only."""
        service, mock_storage = calculator_service
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("divide", 10, 0, None, "Error", "ValueError", _TS2),
        ]
        mock_storage.load_all.return_value = entries

        result = service.filter_history(state="error")

        assert len(result) == 1
        assert result[0].operation == "divide"


# ============================================================================
# Tests for CLI integration with filtering
# ============================================================================

class TestCLIFilterHistoryIntegration:
    """Test CLI integration with filter functionality."""

    def test_prompt_operation_selection_all(self, capsys):
        """Prompt for all operations returns None."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="all"):
            result = cli._prompt_operation_selection()

        assert result is None

    def test_prompt_operation_selection_empty(self, capsys):
        """Prompt with empty input returns None."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value=""):
            result = cli._prompt_operation_selection()

        assert result is None

    def test_prompt_operation_selection_single(self, capsys):
        """Prompt for single operation returns list with one operation."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="1"):
            result = cli._prompt_operation_selection()

        assert len(result) == 1
        assert "add" in result

    def test_prompt_operation_selection_multiple(self, capsys):
        """Prompt for multiple operations returns list."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="1,3,5"):
            result = cli._prompt_operation_selection()

        assert len(result) == 3
        assert "add" in result
        assert "multiply" in result
        assert "square" in result

    def test_prompt_state_selection_success(self, capsys):
        """Prompt for success state returns 'success'."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="1"):
            result = cli._prompt_state_selection()

        assert result == "success"

    def test_prompt_state_selection_error(self, capsys):
        """Prompt for error state returns 'error'."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="2"):
            result = cli._prompt_state_selection()

        assert result == "error"

    def test_prompt_state_selection_both(self, capsys):
        """Prompt for both states returns 'both'."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        with patch("builtins.input", return_value="3"):
            result = cli._prompt_state_selection()

        assert result == "both"

    def test_show_filtered_history_empty(self, capsys):
        """Show filtered history with no results."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        cli.service.filter_history.return_value = []

        cli._show_filtered_history(["add"], "success")

        output = capsys.readouterr().out
        assert "No matching calculations" in output

    def test_show_filtered_history_with_results(self, capsys):
        """Show filtered history with results."""
        from src.cli.calculator_cli import CalculatorCLI

        cli = CalculatorCLI(MagicMock())
        entries = [
            MemoryEntry("add", 1, 1, 2, None, None, _TS1),
            MemoryEntry("add", 5, 5, 10, None, None, _TS2),
        ]
        cli.service.filter_history.return_value = entries

        cli._show_filtered_history(["add"], "success")

        output = capsys.readouterr().out
        assert "1 + 1 = 2" in output
        assert "5 + 5 = 10" in output
