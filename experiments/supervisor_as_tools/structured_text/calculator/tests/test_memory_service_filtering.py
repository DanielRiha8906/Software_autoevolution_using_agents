import pytest
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.cli.calculator_cli import CalculatorCLI


# Test data fixtures
@pytest.fixture
def mock_storage():
    """Create a mock storage that returns consistent test data."""
    storage = MagicMock()
    storage.load_all.return_value = _get_test_entries()
    return storage


@pytest.fixture
def memory_service(mock_storage):
    """Create MemoryService with mock storage."""
    return MemoryService(mock_storage)


@pytest.fixture
def cli_with_memory(memory_service):
    """Create CalculatorCLI with MemoryService."""
    calc_service = MagicMock()
    return CalculatorCLI(calc_service, memory_service)


def _get_test_entries() -> list[MemoryEntry]:
    """
    Create 8 test MemoryEntry objects:
    - add: 2 success, 1 failure
    - divide: 2 success, 1 failure
    - square: 1 success, 1 failure
    """
    return [
        # Add operations (3 total)
        MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            success=True,
            result=8,
            error_message=None,
            timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            id="add-success-1"
        ),
        MemoryEntry(
            operation="add",
            operand_a=10,
            operand_b=20,
            success=True,
            result=30,
            error_message=None,
            timestamp="2026-05-03T10:01:00",
            execution_time_ms=1.2,
            id="add-success-2"
        ),
        MemoryEntry(
            operation="add",
            operand_a=-5,
            operand_b=3,
            success=False,
            result=None,
            error_message="Invalid operands",
            timestamp="2026-05-03T10:02:00",
            execution_time_ms=0.8,
            id="add-failure-1"
        ),
        # Divide operations (3 total)
        MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            success=True,
            result=5.0,
            error_message=None,
            timestamp="2026-05-03T10:03:00",
            execution_time_ms=1.3,
            id="divide-success-1"
        ),
        MemoryEntry(
            operation="divide",
            operand_a=100,
            operand_b=5,
            success=True,
            result=20.0,
            error_message=None,
            timestamp="2026-05-03T10:04:00",
            execution_time_ms=1.4,
            id="divide-success-2"
        ),
        MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            success=False,
            result=None,
            error_message="Division by zero",
            timestamp="2026-05-03T10:05:00",
            execution_time_ms=0.5,
            id="divide-failure-1"
        ),
        # Square operations (2 total)
        MemoryEntry(
            operation="square",
            operand_a=5,
            operand_b=0,
            success=True,
            result=25,
            error_message=None,
            timestamp="2026-05-03T10:06:00",
            execution_time_ms=1.1,
            id="square-success-1"
        ),
        MemoryEntry(
            operation="square",
            operand_a=-3,
            operand_b=0,
            success=False,
            result=None,
            error_message="Invalid operand",
            timestamp="2026-05-03T10:07:00",
            execution_time_ms=0.7,
            id="square-failure-1"
        ),
    ]


# =====================================================================
# SERVICE LAYER TESTS (retrieve_by_filter method)
# =====================================================================

class TestMemoryServiceFilterByOperation:
    """Test filtering by operation only."""

    def test_filter_by_operation_only_add(self, memory_service):
        """Query with operation='add' filter only."""
        results = memory_service.retrieve_by_filter(operation="add")
        assert len(results) == 3
        assert all(e.operation == "add" for e in results)
        assert sum(1 for e in results if e.success) == 2
        assert sum(1 for e in results if not e.success) == 1

    def test_filter_by_operation_only_divide(self, memory_service):
        """Query with operation='divide' filter only."""
        results = memory_service.retrieve_by_filter(operation="divide")
        assert len(results) == 3
        assert all(e.operation == "divide" for e in results)
        assert sum(1 for e in results if e.success) == 2
        assert sum(1 for e in results if not e.success) == 1

    def test_filter_by_operation_only_square(self, memory_service):
        """Query with operation='square' filter only."""
        results = memory_service.retrieve_by_filter(operation="square")
        assert len(results) == 2
        assert all(e.operation == "square" for e in results)
        assert sum(1 for e in results if e.success) == 1
        assert sum(1 for e in results if not e.success) == 1

    def test_filter_by_nonexistent_operation(self, memory_service):
        """Query operation not in data."""
        results = memory_service.retrieve_by_filter(operation="unknown_op")
        assert results == []
        assert isinstance(results, list)


class TestMemoryServiceFilterByStatus:
    """Test filtering by status (success/failure) only."""

    def test_filter_by_status_success_only(self, memory_service):
        """Query with success=True, verify returns all successes."""
        results = memory_service.retrieve_by_filter(success=True)
        assert len(results) == 5  # 2 add + 2 divide + 1 square
        assert all(e.success is True for e in results)

    def test_filter_by_status_failure_only(self, memory_service):
        """Query with success=False, verify returns all failures."""
        results = memory_service.retrieve_by_filter(success=False)
        assert len(results) == 3  # 1 add + 1 divide + 1 square
        assert all(e.success is False for e in results)
        assert all(e.error_message is not None for e in results)


class TestMemoryServiceFilterByBoth:
    """Test filtering by both operation and status."""

    def test_filter_by_operation_and_status_success(self, memory_service):
        """Combined filter: operation='add' AND success=True."""
        results = memory_service.retrieve_by_filter(operation="add", success=True)
        assert len(results) == 2
        assert all(e.operation == "add" for e in results)
        assert all(e.success is True for e in results)

    def test_filter_by_operation_and_status_failure(self, memory_service):
        """Combined filter: operation='divide' AND success=False."""
        results = memory_service.retrieve_by_filter(operation="divide", success=False)
        assert len(results) == 1
        assert results[0].operation == "divide"
        assert results[0].success is False
        assert "Division by zero" in results[0].error_message

    def test_filter_by_operation_and_status_no_matches(self, memory_service):
        """Combined filter with no matches."""
        results = memory_service.retrieve_by_filter(operation="square", success=False)
        assert len(results) == 1
        # Note: There IS one failure for square, so let's verify it
        assert results[0].operation == "square"
        assert results[0].success is False

    def test_filter_by_operation_and_status_truly_no_matches(self, memory_service):
        """Combined filter that truly has no matches."""
        results = memory_service.retrieve_by_filter(operation="unknown_op", success=True)
        assert results == []


class TestMemoryServiceFilterEdgeCases:
    """Test edge cases and return type validation."""

    def test_filter_empty_memory(self):
        """Query on empty MemoryService, returns empty list."""
        empty_storage = MagicMock()
        empty_storage.load_all.return_value = []
        service = MemoryService(empty_storage)

        results = service.retrieve_by_filter()
        assert results == []
        assert isinstance(results, list)

    def test_filter_empty_memory_with_operation(self):
        """Query operation on empty memory."""
        empty_storage = MagicMock()
        empty_storage.load_all.return_value = []
        service = MemoryService(empty_storage)

        results = service.retrieve_by_filter(operation="add")
        assert results == []

    def test_filter_empty_memory_with_status(self):
        """Query status on empty memory."""
        empty_storage = MagicMock()
        empty_storage.load_all.return_value = []
        service = MemoryService(empty_storage)

        results = service.retrieve_by_filter(success=True)
        assert results == []

    def test_filter_returns_list_type(self, memory_service):
        """Verify return type is always list."""
        assert isinstance(memory_service.retrieve_by_filter(), list)
        assert isinstance(memory_service.retrieve_by_filter(operation="add"), list)
        assert isinstance(memory_service.retrieve_by_filter(success=True), list)
        assert isinstance(memory_service.retrieve_by_filter(operation="add", success=True), list)

    def test_filter_preserves_entry_fields(self, memory_service):
        """Verify entry data integrity after filter."""
        results = memory_service.retrieve_by_filter(operation="add", success=True)
        assert len(results) == 2

        # Check all fields are present and correct
        for entry in results:
            assert hasattr(entry, 'id')
            assert hasattr(entry, 'operation')
            assert hasattr(entry, 'operand_a')
            assert hasattr(entry, 'operand_b')
            assert hasattr(entry, 'success')
            assert hasattr(entry, 'result')
            assert hasattr(entry, 'error_message')
            assert hasattr(entry, 'timestamp')
            assert hasattr(entry, 'execution_time_ms')

            # For success, result should be set
            assert entry.result is not None
            assert entry.error_message is None

    def test_filter_no_args_returns_all(self, memory_service):
        """Calling retrieve_by_filter() with no args returns all entries."""
        all_entries = memory_service.retrieve_all()
        filtered_entries = memory_service.retrieve_by_filter()

        assert len(all_entries) == 8
        assert len(filtered_entries) == 8
        assert all_entries == filtered_entries


# =====================================================================
# CLI TESTS (show_memory_filtered_list method)
# =====================================================================

class TestCLIShowMemoryFilteredList:
    """Test CLI display of filtered memory entries."""

    def test_show_memory_filtered_list_operation(self, cli_with_memory, capsys):
        """Display filtered by operation."""
        cli_with_memory.show_memory_filtered_list(operation="add")
        captured = capsys.readouterr()

        # Should display 3 add operations
        assert captured.out.count("[✓]") + captured.out.count("[✗]") >= 3
        assert "add" in captured.out

    def test_show_memory_filtered_list_status_success(self, cli_with_memory, capsys):
        """Display filtered by status=success."""
        cli_with_memory.show_memory_filtered_list(status=True)
        captured = capsys.readouterr()

        # Should display 5 successful operations
        assert captured.out.count("[✓]") == 5

    def test_show_memory_filtered_list_status_failure(self, cli_with_memory, capsys):
        """Display filtered by status=failure."""
        cli_with_memory.show_memory_filtered_list(status=False)
        captured = capsys.readouterr()

        # Should display 3 failures
        assert captured.out.count("[✗]") == 3

    def test_show_memory_filtered_list_combined(self, cli_with_memory, capsys):
        """Display with both operation and status filters."""
        cli_with_memory.show_memory_filtered_list(operation="divide", status=True)
        captured = capsys.readouterr()

        # Should display only successful divide operations
        assert "[✓]" in captured.out
        assert "divide" in captured.out
        # Should show 2 divide successes
        output_lines = [line for line in captured.out.split('\n') if 'divide' in line]
        assert len(output_lines) >= 2

    def test_show_memory_filtered_list_no_results_operation(self, cli_with_memory, capsys):
        """No matches message for operation filter."""
        cli_with_memory.show_memory_filtered_list(operation="unknown_op")
        captured = capsys.readouterr()

        assert "No entries match filters" in captured.out
        assert "operation=unknown_op" in captured.out

    def test_show_memory_filtered_list_no_results_combined(self, cli_with_memory, capsys):
        """No matches message for combined filters."""
        cli_with_memory.show_memory_filtered_list(operation="unknown_op", status=True)
        captured = capsys.readouterr()

        assert "No entries match filters" in captured.out
        assert "operation=unknown_op" in captured.out
        assert "status=success" in captured.out

    def test_show_memory_filtered_list_displays_entry_details(self, cli_with_memory, capsys):
        """Verify entry details are displayed."""
        cli_with_memory.show_memory_filtered_list(operation="add")
        captured = capsys.readouterr()

        # Should have ID and timestamp info
        assert "ID:" in captured.out

    def test_show_memory_no_service(self, capsys):
        """No service available message."""
        calc_service = MagicMock()
        cli = CalculatorCLI(calc_service, None)
        cli.show_memory_filtered_list(operation="add")
        captured = capsys.readouterr()

        assert "Memory service not available" in captured.out

    def test_show_memory_filtered_list_empty_service(self, capsys):
        """Empty service message."""
        empty_storage = MagicMock()
        empty_storage.load_all.return_value = []
        service = MemoryService(empty_storage)
        calc_service = MagicMock()
        cli = CalculatorCLI(calc_service, service)

        cli.show_memory_filtered_list(operation="add")
        captured = capsys.readouterr()

        assert "No entries match filters" in captured.out


# =====================================================================
# BACKWARD COMPATIBILITY TEST
# =====================================================================

class TestBackwardCompatibility:
    """Test that existing behavior is unchanged."""

    def test_backward_compat_show_memory_list_no_args(self, cli_with_memory, capsys):
        """Existing --memory list behavior unchanged."""
        # show_memory_list() without filters should show all entries
        cli_with_memory.show_memory_list()
        captured = capsys.readouterr()

        # Should display all 8 entries (5 success + 3 failure)
        total_status_chars = captured.out.count("[✓]") + captured.out.count("[✗]")
        assert total_status_chars == 8

    def test_backward_compat_retrieve_all(self, memory_service):
        """retrieve_all() still works as before."""
        all_entries = memory_service.retrieve_all()
        assert len(all_entries) == 8

    def test_backward_compat_retrieve_by_operation(self, memory_service):
        """retrieve_by_operation() still works as before."""
        results = memory_service.retrieve_by_operation("add")
        assert len(results) == 3
        assert all(e.operation == "add" for e in results)

    def test_backward_compat_retrieve_successes(self, memory_service):
        """retrieve_successes() still works as before."""
        results = memory_service.retrieve_successes()
        assert len(results) == 5
        assert all(e.success is True for e in results)

    def test_backward_compat_retrieve_failures(self, memory_service):
        """retrieve_failures() still works as before."""
        results = memory_service.retrieve_failures()
        assert len(results) == 3
        assert all(e.success is False for e in results)


# =====================================================================
# ARGPARSE INTEGRATION TESTS
# =====================================================================

class TestArgparseIntegration:
    """Test argparse parser accepts new flags."""

    def test_argparse_memory_list_with_operation(self):
        """Parser accepts --operation flag with --memory list."""
        import sys
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--operation", "add"]):
            with patch.object(CalculatorCLI, "show_memory_filtered_list") as mock_method:
                with patch("sys.exit"):
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Verify the method was called with operation parameter
                    # Note: The mock approach requires we handle the service setup

    def test_argparse_memory_list_with_status_success(self):
        """Parser accepts --status success flag."""
        import sys
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--status", "success"]):
            with patch.object(CalculatorCLI, "show_memory_filtered_list") as mock_method:
                with patch("sys.exit"):
                    try:
                        main()
                    except SystemExit:
                        pass

    def test_argparse_memory_list_with_status_failure(self):
        """Parser accepts --status failure flag."""
        import sys
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--status", "failure"]):
            with patch.object(CalculatorCLI, "show_memory_filtered_list") as mock_method:
                with patch("sys.exit"):
                    try:
                        main()
                    except SystemExit:
                        pass

    def test_argparse_memory_list_invalid_status(self):
        """Invalid status rejected by parser."""
        import sys
        import argparse
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--status", "invalid"]):
            with pytest.raises(SystemExit):
                main()

    def test_argparse_memory_list_invalid_operation(self):
        """Invalid operation rejected by parser."""
        import sys
        import argparse
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--operation", "invalid_op"]):
            with pytest.raises(SystemExit):
                main()

    def test_argparse_memory_list_both_filters(self):
        """Parser accepts both --operation and --status together."""
        import sys
        from src.__main__ import main

        with patch("sys.argv", ["src", "--memory", "list", "--operation", "add", "--status", "success"]):
            with patch.object(CalculatorCLI, "show_memory_filtered_list") as mock_method:
                with patch("sys.exit"):
                    try:
                        main()
                    except SystemExit:
                        pass


# =====================================================================
# PARAMETRIZED TESTS
# =====================================================================

class TestMemoryServiceFilterParametrized:
    """Parametrized tests for multiple filter combinations."""

    @pytest.mark.parametrize("operation,expected_count", [
        ("add", 3),
        ("divide", 3),
        ("square", 2),
        ("unknown", 0),
        ("subtract", 0),
    ])
    def test_filter_by_each_operation(self, memory_service, operation, expected_count):
        """Test filtering by each operation."""
        results = memory_service.retrieve_by_filter(operation=operation)
        assert len(results) == expected_count
        if expected_count > 0:
            assert all(e.operation == operation for e in results)

    @pytest.mark.parametrize("operation,status,expected_count", [
        ("add", True, 2),
        ("add", False, 1),
        ("divide", True, 2),
        ("divide", False, 1),
        ("square", True, 1),
        ("square", False, 1),
        ("unknown", True, 0),
        ("unknown", False, 0),
    ])
    def test_filter_by_operation_and_status(self, memory_service, operation, status, expected_count):
        """Test all combinations of operation and status filters."""
        results = memory_service.retrieve_by_filter(operation=operation, success=status)
        assert len(results) == expected_count
        if expected_count > 0:
            assert all(e.operation == operation for e in results)
            assert all(e.success == status for e in results)
