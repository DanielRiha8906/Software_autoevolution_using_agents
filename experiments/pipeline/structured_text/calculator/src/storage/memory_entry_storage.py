import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry


class MemoryEntryStorage:
    """Handles persistence of MemoryEntry objects to JSON file."""

    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)

    def save(self, entry: MemoryEntry) -> None:
        """Persist a MemoryEntry to storage.

        Args:
            entry: The MemoryEntry object to persist
        """
        records = self._read_raw()
        records.append(entry.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            A list of MemoryEntry objects loaded from storage
        """
        return [MemoryEntry.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
        """Read raw JSON data from file.

        Returns:
            A list of raw dictionaries from the JSON file, or empty list if
            file doesn't exist or is invalid
        """
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_raw(self, records: list) -> None:
        """Write raw JSON data to file.

        Args:
            records: The list of dictionaries to persist
        """
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
