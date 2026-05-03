"""Tests for CalculatorCLI filter commands."""

import pytest
import tempfile
from pathlib import Path
from io import StringIO
import sys
from src.cli.calculator_cli import CalculatorCLI
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
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


@pytest.fixture
def cli_with_data(temp_storage_path):
    """Provide a CalculatorCLI with populated data."""
    service = CalculatorService(Calculator(), JsonStorage(temp_storage_path))
    memory_service = MemoryService(JsonStorage(temp_storage_path))
    cli = CalculatorCLI(service, memory_service)

    # Populate with test data
    _reset_id_counter()
    memory_service.store(ResultEntry(operation="add", operands=[2.0, 3.0], result=5.0))
    memory_service.store(ErrorEntry(operation="add", operands=[1.0, 2.0], error_message="Error 1"))
    memory_service.store(ResultEntry(operation="subtract", operands=[10.0, 4.0], result=6.0))
    memory_service.store(ErrorEntry(operation="divide", operands=[10.0, 0.0], error_message="Div by zero"))
    memory_service.store(ResultEntry(operation="multiply", operands=[3.0, 4.0], result=12.0))

    return cli


class TestCliFilterCommand:
    """Test the filter_command method."""

    def test_filter_command_by_operation(self, cli_with_data, capsys):
        """Filter by operation via CLI command."""
        cli_with_data.filter_command(operation="add")
        captured = capsys.readouterr()
        assert "Found 2 matching entries" in captured.out
        assert "add" in captured.out

    def test_filter_command_by_state_success(self, cli_with_data, capsys):
        """Filter by success state via CLI command."""
        cli_with_data.filter_command(state="success")
        captured = capsys.readouterr()
        assert "Found 3 matching entries" in captured.out

    def test_filter_command_by_state_error(self, cli_with_data, capsys):
        """Filter by error state via CLI command."""
        cli_with_data.filter_command(state="error")
        captured = capsys.readouterr()
        assert "Found 2 matching entries" in captured.out
        assert "ERROR" in captured.out

    def test_filter_command_combined(self, cli_with_data, capsys):
        """Filter by both operation and state via CLI command."""
        cli_with_data.filter_command(operation="add", state="success")
        captured = capsys.readouterr()
        assert "Found 1 matching entries" in captured.out

    def test_filter_command_combined_error(self, cli_with_data, capsys):
        """Filter by operation and error state via CLI command."""
        cli_with_data.filter_command(operation="divide", state="error")
        captured = capsys.readouterr()
        assert "Found 1 matching entries" in captured.out

    def test_filter_command_no_matches(self, cli_with_data, capsys):
        """Filter with no matches."""
        cli_with_data.filter_command(operation="power")
        captured = capsys.readouterr()
        assert "No entries match the specified filters" in captured.out

    def test_filter_command_invalid_state(self, cli_with_data):
        """Filter with invalid state exits with error."""
        with pytest.raises(SystemExit) as exc_info:
            cli_with_data.filter_command(state="invalid")
        assert exc_info.value.code == 1

    def test_filter_command_no_filters(self, cli_with_data, capsys):
        """Filter with no parameters returns all entries."""
        cli_with_data.filter_command()
        captured = capsys.readouterr()
        assert "Found 5 matching entries" in captured.out

    def test_filter_command_empty_storage(self, temp_storage_path, capsys):
        """Filter on empty storage."""
        service = CalculatorService(Calculator(), JsonStorage(temp_storage_path))
        memory_service = MemoryService(JsonStorage(temp_storage_path))
        cli = CalculatorCLI(service, memory_service)

        cli.filter_command(operation="add")
        captured = capsys.readouterr()
        assert "No entries match the specified filters" in captured.out


class TestCliFilterInteractive:
    """Test the interactive filter menu option."""

    def test_filter_interactive_with_operation_only(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with only operation filter."""
        inputs = ["add", ""]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "Filter Calculations" in captured.out
        assert "Found 2 matching entries" in captured.out

    def test_filter_interactive_with_state_only(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with only state filter."""
        inputs = ["", "success"]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "Filter Calculations" in captured.out
        assert "Found 3 matching entries" in captured.out

    def test_filter_interactive_with_both_filters(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with both filters."""
        inputs = ["add", "success"]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "Found 1 matching entries" in captured.out

    def test_filter_interactive_with_no_filters(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with no filters."""
        inputs = ["", ""]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "Found 5 matching entries" in captured.out

    def test_filter_interactive_no_matches(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with no matching results."""
        inputs = ["power", ""]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "No entries match the specified filters" in captured.out

    def test_filter_interactive_empty_storage(self, temp_storage_path, monkeypatch, capsys):
        """Test interactive filter on empty storage."""
        service = CalculatorService(Calculator(), JsonStorage(temp_storage_path))
        memory_service = MemoryService(JsonStorage(temp_storage_path))
        cli = CalculatorCLI(service, memory_service)

        monkeypatch.setattr("builtins.input", lambda _: "")

        cli._filter_interactive()
        captured = capsys.readouterr()

        assert "No operations recorded yet" in captured.out

    def test_filter_interactive_invalid_state_skipped(self, cli_with_data, monkeypatch, capsys):
        """Test interactive filter with invalid state shows warning."""
        inputs = ["", "invalid"]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        assert "Invalid state" in captured.out
        assert "Skipping state filter" in captured.out
        # Should still show all entries since state filter was skipped
        assert "Found 5 matching entries" in captured.out

    def test_filter_interactive_case_sensitive_state(self, cli_with_data, monkeypatch, capsys):
        """Test that state input is case-insensitive."""
        inputs = ["", "SUCCESS"]  # Uppercase
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        cli_with_data._filter_interactive()
        captured = capsys.readouterr()

        # Should process as success (case is converted to lowercase)
        assert "Found 3 matching entries" in captured.out
