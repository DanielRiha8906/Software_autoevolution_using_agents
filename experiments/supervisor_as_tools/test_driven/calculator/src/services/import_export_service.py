import json
from pathlib import Path
from typing import Union

from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class ImportExportService:
    """Service for importing and exporting MemoryEntry records to/from JSON files."""

    def export(self, memory_service: MemoryService, filepath: Union[str, Path]) -> int:
        """Export all memory entries to a JSON file.

        Args:
            memory_service: MemoryService instance containing entries to export
            filepath: Path to write JSON file to (parent directories created if needed)

        Returns:
            Number of entries exported

        Raises:
            Exception: If any error occurs during file operations
        """
        filepath = Path(filepath)

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Retrieve all entries and convert to dicts
        entries = memory_service.retrieve()
        entry_dicts = [entry.to_dict() for entry in entries]

        # Write JSON file
        with open(filepath, "w") as f:
            json.dump(entry_dicts, f, indent=2)

        return len(entry_dicts)

    def import_from(self, memory_service: MemoryService, filepath: Union[str, Path]) -> int:
        """Import memory entries from a JSON file.

        Args:
            memory_service: MemoryService instance to import entries into
            filepath: Path to JSON file to import

        Returns:
            Number of entries imported

        Raises:
            Exception: If JSON structure is invalid or required fields are missing
        """
        filepath = Path(filepath)

        # Read and parse JSON file
        with open(filepath, "r") as f:
            data = json.load(f)

        # Validate that data is a list
        if not isinstance(data, list):
            raise Exception("JSON must be a list at the root level")

        # Track imported IDs to skip duplicates
        existing_ids = {entry.id for entry in memory_service.retrieve()}
        imported_count = 0

        # Required fields for MemoryEntry
        required_fields = {"operation", "operands", "result", "success", "execution_time_ms", "id", "timestamp"}

        # Process each entry
        for item in data:
            # Validate each item is a dict
            if not isinstance(item, dict):
                raise Exception("Each item in JSON must be a dictionary")

            # Check for required fields
            missing_fields = required_fields - set(item.keys())
            if missing_fields:
                raise Exception(f"Missing required fields: {missing_fields}")

            # Skip duplicate IDs
            if item.get("id") in existing_ids:
                continue

            # Import the entry
            try:
                entry = MemoryEntry.from_dict(item)
                memory_service.store(entry)
                existing_ids.add(entry.id)
                imported_count += 1
            except Exception:
                # Re-raise validation errors from MemoryEntry
                raise

        return imported_count
