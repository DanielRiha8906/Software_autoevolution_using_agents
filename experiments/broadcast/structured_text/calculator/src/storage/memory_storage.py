import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry


class MemoryStorage:
    """Storage backend for MemoryEntry objects using JSON files."""

    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)

    def save(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry to the JSON file.

        Args:
            entry: MemoryEntry object to store.
        """
        records = self._read_raw()
        records.append(entry.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[MemoryEntry]:
        """Load all MemoryEntry objects from the JSON file.

        Returns:
            List of MemoryEntry objects in storage order.
        """
        return [MemoryEntry.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
        """Read raw JSON data from the file.

        Returns:
            List of dictionaries, or empty list if file doesn't exist or is invalid.
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
        """Write raw JSON data to the file.

        Args:
            records: List of dictionaries to write.
        """
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
