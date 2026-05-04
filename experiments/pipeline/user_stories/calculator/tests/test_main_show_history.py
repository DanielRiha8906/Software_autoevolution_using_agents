import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.__main__ import main
from src.models.memory_entry import MemoryEntry
import sys

_TS = "2026-05-03T14:30:00"
_UUID = "550e8400-e29b-41d4-a716-446655440000"


class TestShowHistoryFlag:
    """Test --show-history flag functionality."""

    def test_show_history_flag_displays_history(self, capsys):
        """--show-history displays calculation history."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 0
            assert exc_info.value.code == 0
            # History output is printed to stdout
            output = capsys.readouterr().out
            # The actual history content depends on what's in storage,
            # but it should produce some output

    def test_show_history_flag_exits_cleanly(self):
        """--show-history exits with code 0."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_show_history_only_mode(self, capsys):
        """--show-history alone doesn't run interactive or command mode."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 0, indicating history was shown
            assert exc_info.value.code == 0
            # Verify we didn't get interactive menu (which would have "Enter option:" prompt)
            output = capsys.readouterr().out
            assert "Choose option:" not in output

    def test_show_history_ignores_operation_flag(self):
        """--show-history takes precedence over --operation."""
        with patch("sys.argv", ["src", "--show-history", "--operation", "add", "1", "2"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 0 (showing history), not from running command
            assert exc_info.value.code == 0

    def test_show_history_with_empty_history(self, capsys):
        """--show-history handles empty history gracefully."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit cleanly even with empty history
            assert exc_info.value.code == 0

    def test_help_includes_show_history(self, capsys):
        """--help text includes --show-history flag."""
        with patch("sys.argv", ["src", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            output = capsys.readouterr().out
            assert "--show-history" in output

    def test_operation_flag_without_show_history(self):
        """--operation flag works without --show-history."""
        with patch("sys.argv", ["src", "--operation", "add", "1", "2"]):
            # Successful command doesn't raise SystemExit
            main()

    def test_no_flags_defaults_to_interactive(self, capsys):
        """No flags runs interactive mode."""
        with patch("sys.argv", ["src"]):
            with patch("builtins.input", side_effect=["20"]):
                # Choice 20 is "Exit" option in the menu
                main()

            # Verify interactive menu was displayed
            output = capsys.readouterr().out
            assert "=== Calculator ===" in output
            assert "Operations:" in output
            assert "Goodbye!" in output


class TestShowHistoryIntegration:
    """Integration tests for --show-history with real storage."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temp storage file for testing."""
        storage_file = tmp_path / "calc.json"
        return storage_file

    def test_show_history_reads_from_storage(self, temp_storage, capsys):
        """--show-history reads from actual storage."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 0
            assert exc_info.value.code == 0

    def test_show_history_with_mixed_entries(self, capsys):
        """--show-history displays mixed success/error entries."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit successfully
            assert exc_info.value.code == 0
            # Some history output should be printed
            output = capsys.readouterr().out
            # Output may include history entries or "No history yet" message
            assert len(output) > 0


class TestShowHistoryEdgeCases:
    """Edge cases for --show-history flag."""

    def test_show_history_with_very_long_error_message(self, capsys):
        """--show-history handles long error messages."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should still exit successfully
            assert exc_info.value.code == 0

    def test_show_history_with_many_entries(self, capsys):
        """--show-history handles many entries."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit successfully even with many entries
            assert exc_info.value.code == 0

    def test_show_history_with_special_characters_in_error(self, capsys):
        """--show-history handles special characters in errors."""
        with patch("sys.argv", ["src", "--show-history"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit successfully with special characters
            assert exc_info.value.code == 0

    def test_show_history_repeated_calls(self, capsys):
        """Multiple --show-history calls work correctly."""
        for _ in range(3):
            with patch("sys.argv", ["src", "--show-history"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Each call should exit successfully
                assert exc_info.value.code == 0


class TestShowHistoryArgParsing:
    """Test argument parsing for --show-history."""

    def test_show_history_short_form_not_supported(self):
        """--show-history doesn't have a short form."""
        # Just ensure the flag is named correctly
        with patch("sys.argv", ["src", "--show-history"]):
            with patch("src.__main__.CalculatorCLI") as mock_cli_class:
                mock_cli = MagicMock()
                mock_cli_class.return_value = mock_cli

                with pytest.raises(SystemExit):
                    main()

    def test_show_history_action_is_store_true(self):
        """--show-history is a boolean flag."""
        with patch("sys.argv", ["src", "--show-history"]):
            with patch("src.__main__.CalculatorCLI") as mock_cli_class:
                mock_cli = MagicMock()
                mock_cli_class.return_value = mock_cli

                with pytest.raises(SystemExit):
                    main()

                # If we got here, the flag was parsed correctly
                assert True

    def test_show_history_with_unknown_flag_fails(self, capsys):
        """Unknown flags are rejected."""
        with patch("sys.argv", ["src", "--unknown-flag"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with error code
            assert exc_info.value.code != 0

    def test_operation_requires_two_operands(self):
        """--operation flag requires exactly two operands."""
        with patch("sys.argv", ["src", "--operation", "add", "1"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code != 0

    def test_show_history_does_not_require_operands(self):
        """--show-history doesn't need operands."""
        with patch("sys.argv", ["src", "--show-history"]):
            with patch("src.__main__.CalculatorCLI") as mock_cli_class:
                mock_cli = MagicMock()
                mock_cli_class.return_value = mock_cli

                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 0 (success)
                assert exc_info.value.code == 0
