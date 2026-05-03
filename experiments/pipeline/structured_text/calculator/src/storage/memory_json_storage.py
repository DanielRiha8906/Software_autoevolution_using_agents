import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry


class MemoryJsonStorage:
    """
    Persists and retrieves MemoryEntry objects to/from a JSON file.

    Handles storage of calculation memory entries with support for
    both successful and failed calculations. Provides transparent
    serialization and deserialization using MemoryEntry.to_dict()
    and from_dict().
    """

    def __init__(self, filepath: Path | str) -> None:
        """
        Initialize storage with a file path.

        Args:
            filepath: Path to the JSON file for storing memory entries.
        """
        self.filepath = Path(filepath)

    def save(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry by appending it to the JSON file.

        Args:
            entry: MemoryEntry object to persist.
        """
        records = self._read_raw()
        records.append(entry.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[MemoryEntry]:
        """
        Load all stored MemoryEntry objects from the JSON file.

        Returns:
            List of MemoryEntry objects. Returns empty list if file
            does not exist or is corrupted.
        """
        return [MemoryEntry.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
        """
        Read and parse raw JSON data from the storage file.

        Returns:
            List of dict objects from the JSON file. Returns empty list
            if file doesn't exist or JSON is invalid.
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
        """
        Write raw JSON data to the storage file.

        Creates parent directories if they don't exist.

        Args:
            records: List of dict objects to persist as JSON.
        """
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
