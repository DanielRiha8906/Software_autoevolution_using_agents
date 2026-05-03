import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry


class MemoryImportExportService:
    """Service for importing and exporting memory entries to/from JSON files."""

    def validate_entry(self, entry_dict: dict) -> bool:
        """
        Validate that an entry dictionary has all required fields and correct types.

        Args:
            entry_dict: Dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = {"operation", "operand_a", "operand_b", "success"}

        # Check required fields exist
        if not required_fields.issubset(entry_dict.keys()):
            return False

        # Check types
        try:
            operation = entry_dict.get("operation")
            operand_a = entry_dict.get("operand_a")
            operand_b = entry_dict.get("operand_b")
            success = entry_dict.get("success")

            if not isinstance(operation, str):
                return False
            if not isinstance(operand_a, (int, float)):
                return False
            if not isinstance(operand_b, (int, float)):
                return False
            if not isinstance(success, bool):
                return False

            return True
        except (TypeError, ValueError):
            return False

    def find_duplicates(
        self, entries: list[MemoryEntry], existing: list[MemoryEntry]
    ) -> set[str]:
        """
        Find duplicate entries by comparing (operation, operand_a, operand_b, timestamp).

        Args:
            entries: List of entries to check
            existing: List of existing entries to check against

        Returns:
            Set of entry IDs from `entries` that are duplicates
        """
        existing_keys = {
            (e.operation, e.operand_a, e.operand_b, e.timestamp) for e in existing
        }

        duplicates = set()
        for entry in entries:
            key = (entry.operation, entry.operand_a, entry.operand_b, entry.timestamp)
            if key in existing_keys:
                duplicates.add(entry.id)

        return duplicates

    def export_memory(self, filepath: Path | str, entries: list[MemoryEntry]) -> int:
        """
        Export memory entries to a JSON file.

        Args:
            filepath: Path to write JSON file to
            entries: List of MemoryEntry objects to export

        Returns:
            Number of entries exported
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        records = [entry.to_dict() for entry in entries]

        with open(filepath, "w") as f:
            json.dump(records, f, indent=2)

        return len(records)

    def import_from_file(
        self, filepath: Path | str
    ) -> tuple[list[MemoryEntry], int, int]:
        """
        Import memory entries from a JSON file.

        Validates each entry and skips invalid ones. Detects duplicates but includes
        them in the result for the caller to decide what to do.

        Args:
            filepath: Path to JSON file to import from

        Returns:
            Tuple of (valid_entries, skipped_count, duplicate_count)
            - valid_entries: List of valid MemoryEntry objects
            - skipped_count: Number of entries skipped due to validation errors
            - duplicate_count: Number of entries that are duplicates
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(filepath) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filepath}: {exc}")
        except OSError as exc:
            raise IOError(f"Error reading {filepath}: {exc}")

        if not isinstance(data, list):
            raise ValueError(f"JSON root must be a list, got {type(data).__name__}")

        valid_entries = []
        skipped_count = 0

        for entry_dict in data:
            if not isinstance(entry_dict, dict):
                skipped_count += 1
                continue

            if not self.validate_entry(entry_dict):
                skipped_count += 1
                continue

            try:
                entry = MemoryEntry.from_dict(entry_dict)
                valid_entries.append(entry)
            except (TypeError, ValueError, KeyError):
                skipped_count += 1
                continue

        return valid_entries, skipped_count, 0
