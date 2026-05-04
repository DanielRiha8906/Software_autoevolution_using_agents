"""Import/Export service - data serialization for memory entries.

This module provides import/export functionality for memory entries,
part of the history/memory management component.
"""

import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class ImportExportService:
    """Service for importing and exporting memory entries to/from JSON files.

    Part of the history/memory management component, providing data
    persistence and interchange capabilities.
    """

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize the ImportExportService.

        Args:
            memory_service: The MemoryService to read from and write to.
        """
        self._memory_service = memory_service

    def export(self, filepath: str) -> None:
        """Export all stored memory entries to a JSON file.

        The file is written as a JSON list of MemoryEntry dictionaries.

        Args:
            filepath: Path to the JSON file to write to.
        """
        entries = self._memory_service.retrieve()
        data = [entry.to_dict() for entry in entries]

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def import_from(self, filepath: str) -> None:
        """Import memory entries from a JSON file.

        Loads entries from JSON, validates structure, skips duplicates,
        and preserves existing entries.

        Args:
            filepath: Path to the JSON file to read from.

        Raises:
            Exception: If the JSON structure is invalid (not a list of dicts
                      with required fields).
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        # Validate that data is a list
        if not isinstance(data, list):
            raise Exception("JSON must be a list of MemoryEntry objects")

        # Get existing IDs to check for duplicates
        existing_ids = {entry.id for entry in self._memory_service.retrieve()}

        # Process each entry
        for item in data:
            if not isinstance(item, dict):
                raise Exception("Each entry in the list must be a dictionary")

            # Validate required fields
            required_fields = {"id", "operation", "operands", "result", "success", "execution_time_ms"}
            if not required_fields.issubset(set(item.keys())):
                raise Exception(f"Missing required fields. Required: {required_fields}")

            # Skip duplicates
            if item.get("id") in existing_ids:
                continue

            # Create and store the entry
            try:
                entry = MemoryEntry.from_dict(item)
                self._memory_service.store(entry)
                existing_ids.add(entry.id)
            except (TypeError, ValueError) as e:
                raise Exception(f"Failed to create MemoryEntry from data: {e}")
