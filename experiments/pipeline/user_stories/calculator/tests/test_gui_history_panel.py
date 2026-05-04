"""Tests for HistoryPanel GUI component - Unit testing with mocks."""

import pytest
from unittest.mock import MagicMock, patch, call
from src.gui.history_panel import HistoryPanel
from src.gui.constants import (
    COLOR_ERROR_TEXT, COLOR_ERROR_BACKGROUND,
    COLOR_SUCCESS_TEXT, COLOR_SUCCESS_BACKGROUND
)
from src.models.memory_entry import MemoryEntry


class TestHistoryPanelLogic:
    """Test suite for HistoryPanel logic without requiring display."""

    def setup_method(self):
        """Set up test fixtures with mocked tkinter."""
        self.mock_root = MagicMock()

        with patch("src.gui.history_panel.tk.Frame.__init__", return_value=None):
            with patch.object(HistoryPanel, "_setup_ui"):
                self.panel = HistoryPanel(self.mock_root)

        self.panel.history_listbox = MagicMock()
        self.panel.entries = []

    def teardown_method(self):
        """Clean up."""
        pass

    def test_history_panel_initialization(self):
        """Test that HistoryPanel initializes with empty entries."""
        assert self.panel.entries == []

    def test_refresh_with_single_entry(self):
        """Test refreshing history with a single entry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            error=None,
            error_type=None,
        )
        self.panel.refresh([entry])

        assert len(self.panel.entries) == 1
        # Verify delete was called to clear
        self.panel.history_listbox.delete.assert_called()
        # Verify insert was called
        self.panel.history_listbox.insert.assert_called()

    def test_refresh_with_multiple_entries(self):
        """Test refreshing history with multiple entries."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.panel.refresh(entries)

        assert len(self.panel.entries) == 3
        assert self.panel.history_listbox.insert.call_count == 3

    def test_refresh_numbering_is_sequential(self):
        """Test that refresh numbers entries sequentially."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.panel.refresh(entries)

        # Check that insert was called with numbered entries
        insert_calls = self.panel.history_listbox.insert.call_args_list
        texts = [call[0][1] for call in insert_calls]  # Get the text arguments
        assert any("1. " in str(t) for t in texts)
        assert any("2. " in str(t) for t in texts)
        assert any("3. " in str(t) for t in texts)

    def test_refresh_successful_entries_use_success_colors(self):
        """Test that successful entries use success colors."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
        ]
        self.panel.refresh(entries)

        # itemconfig should be called with success colors for success entries
        self.panel.history_listbox.itemconfig.assert_called()
        call_args = self.panel.history_listbox.itemconfig.call_args_list[0]
        assert call_args[1].get("fg") == COLOR_SUCCESS_TEXT
        assert call_args[1].get("bg") == COLOR_SUCCESS_BACKGROUND

    def test_refresh_error_entries_use_error_colors(self):
        """Test that error entries use error colors."""
        entries = [
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
        ]
        self.panel.refresh(entries)

        self.panel.history_listbox.itemconfig.assert_called()
        call_args = self.panel.history_listbox.itemconfig.call_args_list[0]
        assert call_args[1].get("fg") == COLOR_ERROR_TEXT
        assert call_args[1].get("bg") == COLOR_ERROR_BACKGROUND

    def test_refresh_mixed_success_and_error(self):
        """Test refreshing with mixed success and error entries."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("divide", 5.0, 0.0, None, "Division by zero", "ValueError"),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.panel.refresh(entries)

        # itemconfig should be called 3 times (once for each entry)
        assert self.panel.history_listbox.itemconfig.call_count == 3

        # Check that colors are applied correctly
        calls = self.panel.history_listbox.itemconfig.call_args_list
        # Entry 0: success
        assert calls[0][1].get("fg") == COLOR_SUCCESS_TEXT
        # Entry 1: error
        assert calls[1][1].get("fg") == COLOR_ERROR_TEXT
        # Entry 2: success
        assert calls[2][1].get("fg") == COLOR_SUCCESS_TEXT

    def test_refresh_clears_previous_entries(self):
        """Test that refresh clears previous entries."""
        entries1 = [MemoryEntry("add", 1.0, 2.0, 3.0, None, None)]
        self.panel.refresh(entries1)
        assert len(self.panel.entries) == 1

        entries2 = [
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.panel.refresh(entries2)

        assert len(self.panel.entries) == 2
        # delete should have been called again
        assert self.panel.history_listbox.delete.call_count == 2

    def test_refresh_with_empty_list(self):
        """Test refreshing with empty entries."""
        self.panel.refresh([])

        assert len(self.panel.entries) == 0
        self.panel.history_listbox.delete.assert_called()

    def test_clear_empties_history(self):
        """Test that clear empties the history display."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
        ]
        self.panel.refresh(entries)
        assert len(self.panel.entries) == 2

        self.panel.clear()

        assert self.panel.history_listbox.delete.called
        assert self.panel.entries == []

    def test_get_entries_returns_current_entries(self):
        """Test that get_entries returns the current entries."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
        ]
        self.panel.refresh(entries)

        retrieved = self.panel.get_entries()
        assert len(retrieved) == 2
        assert retrieved == entries

    def test_get_entries_empty(self):
        """Test get_entries when history is empty."""
        retrieved = self.panel.get_entries()
        assert retrieved == []

    def test_refresh_preserves_entry_data(self):
        """Test that refresh preserves the original entry data."""
        original_entry = MemoryEntry(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            error=None,
            error_type=None,
        )
        self.panel.refresh([original_entry])

        retrieved = self.panel.get_entries()[0]
        assert retrieved.operation == original_entry.operation
        assert retrieved.operand_a == original_entry.operand_a
        assert retrieved.operand_b == original_entry.operand_b
        assert retrieved.result == original_entry.result
        assert retrieved.error == original_entry.error

    def test_refresh_large_history(self):
        """Test refreshing with a large number of entries."""
        entries = [
            MemoryEntry(f"add" if i % 2 == 0 else "subtract", float(i), float(i + 1), float(i * 2), None, None)
            for i in range(100)
        ]
        self.panel.refresh(entries)

        assert self.panel.history_listbox.insert.call_count == 100
        assert len(self.panel.entries) == 100

    def test_refresh_with_division_operations(self):
        """Test refreshing with division operations and results."""
        entries = [
            MemoryEntry("divide", 10.0, 2.0, 5.0, None, None),
            MemoryEntry("divide", 7.0, 3.0, 2.3333333333, None, None),
        ]
        self.panel.refresh(entries)

        # insert should be called with division symbol
        insert_calls = self.panel.history_listbox.insert.call_args_list
        texts = [call[0][1] for call in insert_calls]
        assert any("÷" in str(t) for t in texts)

    def test_refresh_with_unary_operations(self):
        """Test refreshing with unary operations."""
        entries = [
            MemoryEntry("sqrt", 16.0, 0.0, 4.0, None, None),
            MemoryEntry("square", 5.0, 0.0, 25.0, None, None),
        ]
        self.panel.refresh(entries)

        assert self.panel.history_listbox.insert.call_count == 2

    def test_refresh_error_message_display(self):
        """Test that error messages are displayed in history."""
        entries = [
            MemoryEntry(
                operation="divide",
                operand_a=5.0,
                operand_b=0.0,
                result=None,
                error="Division by zero",
                error_type="ValueError",
            ),
        ]
        self.panel.refresh(entries)

        # insert should be called with error text
        insert_calls = self.panel.history_listbox.insert.call_args_list
        text = insert_calls[0][0][1]
        assert "ERROR:" in text
        assert "Division by zero" in text

    def test_clear_then_refresh(self):
        """Test clearing and then refreshing with new entries."""
        entries1 = [MemoryEntry("add", 1.0, 2.0, 3.0, None, None)]
        self.panel.refresh(entries1)

        self.panel.clear()
        assert self.panel.entries == []

        entries2 = [MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None)]
        self.panel.refresh(entries2)
        assert len(self.panel.entries) == 1

    def test_refresh_with_special_characters_in_error(self):
        """Test displaying errors with special characters."""
        entries = [
            MemoryEntry(
                operation="divide",
                operand_a=1.0,
                operand_b=0.0,
                result=None,
                error="Cannot divide: 1/0 = undefined",
                error_type="ValueError",
            ),
        ]
        self.panel.refresh(entries)

        insert_calls = self.panel.history_listbox.insert.call_args_list
        text = insert_calls[0][0][1]
        assert "undefined" in text

    def test_refresh_with_timestamps(self):
        """Test that entries with timestamps are stored."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            error=None,
            error_type=None,
            timestamp="2026-05-04T12:00:00",
        )
        self.panel.refresh([entry])

        retrieved = self.panel.get_entries()[0]
        assert retrieved.timestamp == "2026-05-04T12:00:00"

    def test_refresh_updates_internal_state(self):
        """Test that refresh updates the internal entries list."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
        ]
        self.panel.refresh(entries)

        assert self.panel.entries == entries

    def test_multiple_refreshes_with_different_sizes(self):
        """Test multiple refreshes with varying entry counts."""
        self.panel.refresh([MemoryEntry("add", 1.0, 2.0, 3.0, None, None)])
        assert len(self.panel.entries) == 1

        self.panel.refresh([
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ])
        assert len(self.panel.entries) == 3

        self.panel.refresh([
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
        ])
        assert len(self.panel.entries) == 1

    def test_error_entries_all_colored_consistently(self):
        """Test that all error entries get the same error coloring."""
        entries = [
            MemoryEntry("divide", 1.0, 0.0, None, "Error 1", "ValueError"),
            MemoryEntry("divide", 2.0, 0.0, None, "Error 2", "ValueError"),
            MemoryEntry("divide", 3.0, 0.0, None, "Error 3", "ValueError"),
        ]
        self.panel.refresh(entries)

        calls = self.panel.history_listbox.itemconfig.call_args_list
        for call_obj in calls:
            assert call_obj[1].get("fg") == COLOR_ERROR_TEXT
            assert call_obj[1].get("bg") == COLOR_ERROR_BACKGROUND

    def test_success_entries_all_colored_consistently(self):
        """Test that all success entries get the same success coloring."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, None, None),
            MemoryEntry("subtract", 5.0, 2.0, 3.0, None, None),
            MemoryEntry("multiply", 3.0, 4.0, 12.0, None, None),
        ]
        self.panel.refresh(entries)

        calls = self.panel.history_listbox.itemconfig.call_args_list
        for call_obj in calls:
            assert call_obj[1].get("fg") == COLOR_SUCCESS_TEXT
            assert call_obj[1].get("bg") == COLOR_SUCCESS_BACKGROUND
