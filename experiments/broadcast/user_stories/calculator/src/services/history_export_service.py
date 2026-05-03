"""HistoryExportService handles export and import of calculation history to/from JSON files.

This service provides functionality to:
- Export memory entries to a JSON file
- Import memory entries from a JSON file with validation
- Validate imported data structure before applying
- Skip invalid/duplicate entries during import without full failure
"""

import json
from pathlib import Path
from typing import Optional

from ..models.memory_entry import MemoryEntry, ResultEntry, ErrorEntry


class HistoryExportService:
    """Service for exporting and importing calculation history to/from JSON files.

    Supports validation of imported data and graceful handling of invalid entries.
    """

    @staticmethod
    def export_history(entries: list[MemoryEntry], filepath: str | Path) -> None:
        """Export memory entries to a JSON file.

        Args:
            entries: List of MemoryEntry objects (ResultEntry or ErrorEntry)
            filepath: Path to the output JSON file

        Raises:
            IOError: If the file cannot be written
            ValueError: If entries list is invalid
        """
        if not isinstance(entries, list):
            raise ValueError("Entries must be a list of MemoryEntry objects")

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = [entry.to_dict() for entry in entries]

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to write to {filepath}: {e}")

    @staticmethod
    def import_history(
        filepath: str | Path,
        skip_duplicates: bool = True,
        existing_ids: Optional[set[int]] = None,
    ) -> tuple[list[MemoryEntry], list[str]]:
        """Import memory entries from a JSON file with validation.

        Args:
            filepath: Path to the input JSON file
            skip_duplicates: If True, skip entries with IDs that already exist
            existing_ids: Set of existing entry IDs to check against for duplicates.
                         If None, no duplicate checking is performed.

        Returns:
            A tuple of:
            - List of successfully imported MemoryEntry objects
            - List of validation error messages for skipped entries

        Raises:
            IOError: If the file cannot be read
            ValueError: If the JSON structure is invalid
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise IOError(f"File not found: {filepath}")

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to read from {filepath}: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {filepath}: {e}")

        if not isinstance(data, list):
            raise ValueError("JSON root must be an array of entries")

        entries: list[MemoryEntry] = []
        errors: list[str] = []
        existing_ids = existing_ids or set()

        for idx, item in enumerate(data):
            try:
                if not isinstance(item, dict):
                    errors.append(f"Entry {idx}: Not a dictionary")
                    continue

                # Check for duplicate entry_id
                if skip_duplicates and existing_ids:
                    entry_id = item.get("entry_id")
                    if entry_id in existing_ids:
                        errors.append(f"Entry {idx}: Duplicate entry_id {entry_id}")
                        continue

                # Validate required fields
                entry_type = item.get("type")
                if entry_type not in ("result", "error"):
                    errors.append(f"Entry {idx}: Invalid type '{entry_type}' (must be 'result' or 'error')")
                    continue

                if "operation" not in item or not isinstance(item.get("operation"), str):
                    errors.append(f"Entry {idx}: Missing or invalid 'operation' field")
                    continue

                if "operands" not in item or not isinstance(item.get("operands"), list):
                    errors.append(f"Entry {idx}: Missing or invalid 'operands' field (must be a list)")
                    continue

                if "timestamp" not in item or not isinstance(item.get("timestamp"), str):
                    errors.append(f"Entry {idx}: Missing or invalid 'timestamp' field")
                    continue

                if entry_type == "result":
                    if "result" not in item:
                        errors.append(f"Entry {idx}: Missing 'result' field for result entry")
                        continue
                    try:
                        result_val = float(item["result"])
                    except (ValueError, TypeError):
                        errors.append(f"Entry {idx}: 'result' must be numeric")
                        continue

                elif entry_type == "error":
                    if "error_message" not in item or not isinstance(item.get("error_message"), str):
                        errors.append(f"Entry {idx}: Missing or invalid 'error_message' field")
                        continue

                # Try to deserialize
                try:
                    entry = MemoryEntry.from_dict(item)
                    entries.append(entry)
                    if skip_duplicates and existing_ids:
                        existing_ids.add(entry.entry_id)
                except (ValueError, KeyError, TypeError) as e:
                    errors.append(f"Entry {idx}: Deserialization error: {e}")
                    continue

            except Exception as e:
                errors.append(f"Entry {idx}: Unexpected error: {e}")
                continue

        return entries, errors
