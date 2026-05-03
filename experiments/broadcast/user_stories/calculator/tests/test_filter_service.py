"""Tests for FilterService filtering functionality."""

import pytest
from src.services.filter_service import FilterService
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter


@pytest.fixture
def filter_service():
    """Provide a FilterService instance."""
    return FilterService()


@pytest.fixture
def sample_entries():
    """Provide a sample set of memory entries for testing."""
    _reset_id_counter()
    return [
        ResultEntry(operation="add", operands=[2.0, 3.0], result=5.0),
        ResultEntry(operation="subtract", operands=[10.0, 4.0], result=6.0),
        ErrorEntry(operation="add", operands=[1.0, 2.0], error_message="Test error 1"),
        ResultEntry(operation="multiply", operands=[3.0, 4.0], result=12.0),
        ErrorEntry(operation="divide", operands=[10.0, 0.0], error_message="Division by zero"),
        ResultEntry(operation="add", operands=[5.0, 5.0], result=10.0),
        ResultEntry(operation="divide", operands=[10.0, 2.0], result=5.0),
        ErrorEntry(operation="subtract", operands=[5.0, 10.0], error_message="Subtraction error"),
    ]


class TestFilterServiceFilterByOperation:
    """Test filtering by operation type."""

    def test_filter_by_operation_add(self, filter_service, sample_entries):
        """Filter entries by 'add' operation."""
        result = filter_service.filter_entries(sample_entries, operation="add")
        assert len(result) == 3
        assert all(e.operation == "add" for e in result)

    def test_filter_by_operation_subtract(self, filter_service, sample_entries):
        """Filter entries by 'subtract' operation."""
        result = filter_service.filter_entries(sample_entries, operation="subtract")
        assert len(result) == 2
        assert all(e.operation == "subtract" for e in result)

    def test_filter_by_operation_multiply(self, filter_service, sample_entries):
        """Filter entries by 'multiply' operation."""
        result = filter_service.filter_entries(sample_entries, operation="multiply")
        assert len(result) == 1
        assert result[0].operation == "multiply"

    def test_filter_by_operation_divide(self, filter_service, sample_entries):
        """Filter entries by 'divide' operation."""
        result = filter_service.filter_entries(sample_entries, operation="divide")
        assert len(result) == 2
        assert all(e.operation == "divide" for e in result)

    def test_filter_by_nonexistent_operation(self, filter_service, sample_entries):
        """Filter by operation that doesn't exist."""
        result = filter_service.filter_entries(sample_entries, operation="power")
        assert len(result) == 0


class TestFilterServiceFilterByState:
    """Test filtering by result state."""

    def test_filter_by_state_success(self, filter_service, sample_entries):
        """Filter entries by 'success' state (ResultEntry instances)."""
        result = filter_service.filter_entries(sample_entries, state="success")
        assert len(result) == 5
        assert all(isinstance(e, ResultEntry) for e in result)
        assert all(not e.is_error() for e in result)

    def test_filter_by_state_error(self, filter_service, sample_entries):
        """Filter entries by 'error' state (ErrorEntry instances)."""
        result = filter_service.filter_entries(sample_entries, state="error")
        assert len(result) == 3
        assert all(isinstance(e, ErrorEntry) for e in result)
        assert all(e.is_error() for e in result)

    def test_filter_by_invalid_state(self, filter_service, sample_entries):
        """Filter by invalid state raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state"):
            filter_service.filter_entries(sample_entries, state="invalid")

    def test_filter_by_state_case_sensitive(self, filter_service, sample_entries):
        """State filter is case-sensitive."""
        with pytest.raises(ValueError, match="Invalid state"):
            filter_service.filter_entries(sample_entries, state="SUCCESS")


class TestFilterServiceCombinedFilters:
    """Test combining multiple filters."""

    def test_filter_by_operation_and_state_success(self, filter_service, sample_entries):
        """Filter by operation and state (success)."""
        result = filter_service.filter_entries(sample_entries, operation="add", state="success")
        assert len(result) == 2
        assert all(e.operation == "add" for e in result)
        assert all(isinstance(e, ResultEntry) for e in result)

    def test_filter_by_operation_and_state_error(self, filter_service, sample_entries):
        """Filter by operation and state (error)."""
        result = filter_service.filter_entries(sample_entries, operation="add", state="error")
        assert len(result) == 1
        assert result[0].operation == "add"
        assert isinstance(result[0], ErrorEntry)

    def test_filter_by_operation_with_no_errors(self, filter_service, sample_entries):
        """Filter by operation and state error when operation has no errors."""
        result = filter_service.filter_entries(sample_entries, operation="multiply", state="error")
        assert len(result) == 0

    def test_filter_by_operation_with_no_successes(self, filter_service, sample_entries):
        """Filter by operation and state success when operation has no successes."""
        # First modify entries so an operation has no successes
        test_entries = [
            ErrorEntry(operation="sqrt", operands=[-1.0], error_message="Negative number"),
        ]
        result = filter_service.filter_entries(test_entries, operation="sqrt", state="success")
        assert len(result) == 0

    def test_no_filters_returns_all(self, filter_service, sample_entries):
        """No filters returns all entries."""
        result = filter_service.filter_entries(sample_entries)
        assert len(result) == len(sample_entries)

    def test_combined_filters_empty_result(self, filter_service, sample_entries):
        """Combined filters can result in empty list."""
        result = filter_service.filter_entries(
            sample_entries, operation="power", state="success"
        )
        assert len(result) == 0


class TestFilterServiceGetValidOperations:
    """Test retrieving valid operations."""

    def test_get_valid_operations_sorted(self, filter_service, sample_entries):
        """Get all unique operations in sorted order."""
        operations = filter_service.get_valid_operations(sample_entries)
        expected = ["add", "divide", "multiply", "subtract"]
        assert operations == expected

    def test_get_valid_operations_empty_list(self, filter_service):
        """Empty entries list returns empty operations list."""
        operations = filter_service.get_valid_operations([])
        assert operations == []

    def test_get_valid_operations_with_empty_operation(self, filter_service):
        """Entries with empty operation field are skipped."""
        entries = [
            ResultEntry(operation="", operands=[], result=0.0),
            ResultEntry(operation="add", operands=[1.0, 2.0], result=3.0),
        ]
        operations = filter_service.get_valid_operations(entries)
        assert operations == ["add"]


class TestFilterServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_filter_empty_list(self, filter_service):
        """Filter empty list returns empty list."""
        result = filter_service.filter_entries([], operation="add")
        assert result == []

    def test_filter_preserves_entry_data(self, filter_service):
        """Filtering preserves all entry data."""
        entries = [
            ResultEntry(operation="add", operands=[2.0, 3.0], result=5.0),
        ]
        result = filter_service.filter_entries(entries, operation="add")
        assert len(result) == 1
        assert result[0].operation == "add"
        assert result[0].operands == [2.0, 3.0]
        assert result[0].result == 5.0

    def test_multiple_operations_same_type(self, filter_service):
        """Multiple entries of same operation type are all returned."""
        entries = [
            ResultEntry(operation="add", operands=[1.0, 1.0], result=2.0),
            ResultEntry(operation="add", operands=[2.0, 2.0], result=4.0),
            ResultEntry(operation="add", operands=[3.0, 3.0], result=6.0),
        ]
        result = filter_service.filter_entries(entries, operation="add")
        assert len(result) == 3
        assert all(e.operation == "add" for e in result)

    def test_filter_maintains_original_order(self, filter_service):
        """Filtering maintains the original order of entries."""
        _reset_id_counter()
        entries = [
            ResultEntry(operation="add", operands=[1.0, 1.0], result=2.0),
            ErrorEntry(operation="subtract", operands=[1.0, 2.0], error_message="Error"),
            ResultEntry(operation="add", operands=[2.0, 2.0], result=4.0),
            ResultEntry(operation="multiply", operands=[2.0, 3.0], result=6.0),
        ]
        result = filter_service.filter_entries(entries, operation="add")
        assert result[0].entry_id < result[1].entry_id
        assert all(e.operation == "add" for e in result)
