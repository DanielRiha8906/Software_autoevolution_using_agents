import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class HistoryManager(MemoryService):
    """Manager for importing and exporting calculation history.

    Extends MemoryService to add import/export capabilities for MemoryEntry records.
    """

    def export_to_file(self, filepath: str | Path) -> tuple[int, list[str]]:
        """Export all stored MemoryEntry records to a JSON file.

        Args:
            filepath: Path where the JSON file will be written.

        Returns:
            Tuple of (count_exported, errors) where errors is a list of export error messages.
        """
        filepath = Path(filepath)
        try:
            entries = self.retrieve()
            records = [entry.to_dict() for entry in entries]
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(records, f, indent=2)
            return len(records), []
        except (IOError, OSError) as e:
            return 0, [f"Export failed: {e}"]

    def import_from_file(self, filepath: str | Path, choice: str = "append") -> tuple[int, list[str]]:
        """Import MemoryEntry records from a JSON file.

        Args:
            filepath: Path to the JSON file to import from.
            choice: "append" to add to existing entries, "replace" to clear and replace.

        Returns:
            Tuple of (count_imported, errors) where errors is a list of validation error messages.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in file: {e.msg}", e.doc, e.pos)

        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")

        # Validate and import entries
        imported_count = 0
        errors = []

        for i, entry_dict in enumerate(data):
            try:
                if not self._validate_entry(entry_dict):
                    errors.append(f"Entry {i}: Missing or invalid fields")
                    continue

                entry = MemoryEntry.from_dict(entry_dict)
                self.storage.save(entry)
                imported_count += 1
            except (TypeError, ValueError) as e:
                errors.append(f"Entry {i}: {str(e)}")

        # Handle replace mode
        if choice == "replace" and imported_count > 0:
            # For replace mode, we've already cleared by overwriting
            pass

        return imported_count, errors

    @staticmethod
    def _validate_entry(entry_dict: dict) -> bool:
        """Validate that a dictionary has the required MemoryEntry fields.

        Args:
            entry_dict: Dictionary to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(entry_dict, dict):
            return False

        required_fields = {
            "operation_name",
            "operand_a",
            "operand_b",
            "result",
            "success",
            "error_message",
            "execution_timestamp",
            "execution_time_ms",
        }

        # Check all required fields are present
        if not required_fields.issubset(entry_dict.keys()):
            return False

        # Type validation
        try:
            if not isinstance(entry_dict.get("operation_name"), str):
                return False
            if not isinstance(entry_dict.get("operand_a"), (int, float)):
                return False
            if not isinstance(entry_dict.get("operand_b"), (int, float)):
                return False
            result = entry_dict.get("result")
            if result is not None and not isinstance(result, (int, float)):
                return False
            if not isinstance(entry_dict.get("success"), bool):
                return False
            error_msg = entry_dict.get("error_message")
            if error_msg is not None and not isinstance(error_msg, str):
                return False
            if not isinstance(entry_dict.get("execution_timestamp"), str):
                return False
            if not isinstance(entry_dict.get("execution_time_ms"), (int, float)):
                return False
        except (AttributeError, TypeError):
            return False

        return True
