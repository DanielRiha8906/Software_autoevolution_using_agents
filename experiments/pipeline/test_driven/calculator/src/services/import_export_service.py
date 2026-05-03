import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class ImportExportService:
    """Service for JSON serialization/deserialization of MemoryEntry records.

    Provides export() and import_from() methods to persist and restore
    MemoryEntry objects from JSON files. Handles validation, duplicate
    detection, and safe merging on import.
    """

    def export(self, memory_service: MemoryService, filepath: Path | str) -> None:
        """Export MemoryEntry records from MemoryService to JSON file.

        Retrieves all entries from memory_service, converts each to a dict
        via to_dict(), and writes the list as JSON to the specified filepath.
        Creates parent directories as needed.

        Args:
            memory_service: MemoryService instance containing entries to export.
            filepath: Path to JSON file to write. Can be Path or str.
                     Parent directories are created if they don't exist.

        Returns:
            None

        Raises:
            OSError: If file cannot be written (permission denied, etc.)
        """
        entries = memory_service.retrieve()
        entry_dicts = [entry.to_dict() for entry in entries]

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(entry_dicts, f, indent=2)

    def import_from(self, memory_service: MemoryService, filepath: Path | str) -> None:
        """Import MemoryEntry records from JSON file into MemoryService.

        Reads JSON file and validates structure (must be a list of dicts).
        For each entry dict, creates a MemoryEntry via from_dict(). Skips
        entries whose ID already exists in memory_service (preserves existing
        entries, does not overwrite). Stores new entries via memory_service.store().

        Args:
            memory_service: MemoryService instance to import entries into.
            filepath: Path to JSON file to read. Can be Path or str.

        Returns:
            None

        Raises:
            FileNotFoundError: If file does not exist.
            Exception: If JSON is invalid or structure is not a list of dicts,
                      or if MemoryEntry.from_dict() fails on any entry.
        """
        filepath = Path(filepath)

        try:
            with open(filepath) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise Exception(f"Invalid JSON in file '{filepath}': {exc}")
        except FileNotFoundError:
            raise

        if not isinstance(data, list):
            raise Exception(f"Expected JSON array at top level in '{filepath}', got {type(data).__name__}")

        existing_ids = {entry.id for entry in memory_service.retrieve()}

        for item in data:
            if not isinstance(item, dict):
                raise Exception(f"Expected dict in JSON array, got {type(item).__name__}")

            try:
                entry = MemoryEntry.from_dict(item)
            except (TypeError, KeyError, ValueError) as exc:
                raise Exception(f"Failed to deserialize entry: {exc}")

            if entry.id not in existing_ids:
                memory_service.store(entry)
                existing_ids.add(entry.id)
