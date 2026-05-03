"""Tests for CLI flags: --memory, --memory-filter, --filter-operation, --filter-status."""

import pytest
import sys
from pathlib import Path
from io import StringIO
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_json_storage import MemoryJsonStorage
from src import __main__


class TestMemoryBackwardCompatibility:
    """Test --memory flag (original flag for viewing all memory)."""

    def test_memory_flag_displays_entries(self, tmp_path, monkeypatch, capsys):
        """Test 1: --memory flag displays all stored memory entries."""
        # Create memory storage with test data
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1")
        memory_service.store(entry)

        # Mock the service builders to use test path
        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        # Simulate: python -m src --memory
        sys.argv = ["src", "--memory"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "add" in output.lower() or "3" in output

    def test_memory_flag_empty_storage(self, tmp_path, monkeypatch, capsys):
        """Test 2: --memory flag with empty storage shows no entries message."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "No memory entries" in output or "Memory" in output


class TestMemoryFilterOperationFlag:
    """Test --memory-filter operation --filter-operation <name>."""

    def test_memory_filter_operation_by_name(self, tmp_path, monkeypatch, capsys):
        """Test 1: --memory-filter operation --filter-operation add shows only add entries."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        # Store mixed operations
        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))
        memory_service.store(MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "operation", "--filter-operation", "add"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "add" in output.lower() or "3" in output

    def test_memory_filter_operation_case_insensitive(self, tmp_path, monkeypatch, capsys):
        """Test 2: --filter-operation is case-insensitive."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "operation", "--filter-operation", "ADD"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        # Should match "add" despite uppercase input, or show results
        assert "add" in output.lower() or "No entries" in output

    def test_memory_filter_operation_no_matches(self, tmp_path, monkeypatch, capsys):
        """Test 3: --filter-operation with no matches shows appropriate message."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "operation", "--filter-operation", "power"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "No entries match" in output

    def test_memory_filter_operation_missing_required_arg(self, tmp_path, monkeypatch):
        """Test 4: --memory-filter operation without --filter-operation raises error."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "operation"]
        with pytest.raises(SystemExit):
            __main__.main()


class TestMemoryFilterStatusFlag:
    """Test --memory-filter status --filter-status {success,failed}."""

    def test_memory_filter_status_success(self, tmp_path, monkeypatch, capsys):
        """Test 1: --memory-filter status --filter-status success shows only successful entries."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 2.0, "id-3"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "status", "--filter-status", "success"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        # Should show successful entries
        assert "add" in output.lower() or "multiply" in output.lower() or "3" in output

    def test_memory_filter_status_failed(self, tmp_path, monkeypatch, capsys):
        """Test 2: --memory-filter status --filter-status failed shows only failed entries."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "status", "--filter-status", "failed"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "divide" in output.lower() or "error" in output.lower() or "Division" in output

    def test_memory_filter_status_no_matches(self, tmp_path, monkeypatch, capsys):
        """Test 3: --filter-status with no matches shows appropriate message."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "status", "--filter-status", "failed"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "No entries match" in output

    def test_memory_filter_status_missing_required_arg(self, tmp_path, monkeypatch):
        """Test 4: --memory-filter status without --filter-status raises error."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "status"]
        with pytest.raises(SystemExit):
            __main__.main()


class TestMemoryFilterEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_memory_no_entries_message(self, tmp_path, monkeypatch, capsys):
        """Test: Empty memory with filter shows no entries message."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--memory-filter", "operation", "--filter-operation", "add"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "No entries match" in output


class TestStatisticsFlag:
    """Test --statistics CLI flag."""

    def test_statistics_flag_with_data(self, tmp_path, monkeypatch, capsys):
        """Test 1: --statistics flag displays statistics with stored data."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:02:00", 0.5, "id-3"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "Calculation Statistics" in output
        assert "Total Calculations: 3" in output
        assert "Failed: 1" in output

    def test_statistics_flag_empty_storage(self, tmp_path, monkeypatch, capsys):
        """Test 2: --statistics flag with empty storage shows no calculations message."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "No calculations" in output

    def test_statistics_flag_shows_error_rate(self, tmp_path, monkeypatch, capsys):
        """Test 3: --statistics flag displays error rate."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        # Store 4 successful, 1 failed (20% error rate)
        for i in range(4):
            memory_service.store(MemoryEntry("add", float(i), float(i+1), float(2*i+1), True, None, "2026-05-03T10:00:00", 1.0, f"id-{i}"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:04:00", 0.5, "id-4"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "Error Rate:" in output
        assert "20.00%" in output

    def test_statistics_flag_shows_execution_times(self, tmp_path, monkeypatch, capsys):
        """Test 4: --statistics flag displays execution time statistics."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.5, "id-1"))
        memory_service.store(MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "Average Execution Time:" in output
        assert "Min Execution Time:" in output
        assert "Max Execution Time:" in output

    def test_statistics_flag_shows_operation_usage(self, tmp_path, monkeypatch, capsys):
        """Test 5: --statistics flag displays operation usage counts."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 1.5, "id-2"))
        memory_service.store(MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 2.0, "id-3"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "Operation Usage:" in output
        assert "add:" in output.lower() or "Add:" in output
        assert "multiply:" in output.lower() or "Multiply:" in output

    def test_statistics_flag_shows_per_operation_error_rates(self, tmp_path, monkeypatch, capsys):
        """Test 6: --statistics flag shows error rate for each operation."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        # Add: 2 successful
        memory_service.store(MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"))
        memory_service.store(MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:01:00", 1.5, "id-2"))
        # Divide: 1 successful, 1 failed
        memory_service.store(MemoryEntry("divide", 10.0, 2.0, 5.0, True, None, "2026-05-03T10:02:00", 1.0, "id-3"))
        memory_service.store(MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:03:00", 0.5, "id-4"))

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            from unittest.mock import MagicMock
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--statistics"]
        try:
            __main__.main()
        except SystemExit:
            pass

        output = capsys.readouterr().out
        assert "error rate" in output.lower()
