import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry


class MemoryEntryStorage:
    """Storage for MemoryEntry objects using JSON file persistence."""

    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)

    def save(self, entry: MemoryEntry) -> None:
        """Save a single MemoryEntry, appending to existing entries."""
        records = self._read_raw()
        records.append(entry.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[MemoryEntry]:
        """Load all MemoryEntry objects from storage."""
        return [MemoryEntry.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
        """Read raw JSON data from file, returning empty list if file missing or invalid."""
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_raw(self, records: list) -> None:
        """Write raw JSON data to file, creating parent directories if needed."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
