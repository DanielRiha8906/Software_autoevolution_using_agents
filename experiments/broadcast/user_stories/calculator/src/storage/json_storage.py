import json
from pathlib import Path

from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry


class JsonStorage:
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)
        self._memory_filepath = Path(str(filepath).replace(".json", "_memory.json"))

    def save(self, item: CalculationResult | MemoryEntry) -> None:
        """Save either a CalculationResult or MemoryEntry."""
        if isinstance(item, MemoryEntry):
            records = self._read_memory_raw()
            records.append(item.to_dict())
            self._write_memory_raw(records)
        else:
            records = self._read_raw()
            records.append(item.to_dict())
            self._write_raw(records)

    def load_all(self) -> list[CalculationResult]:
        return [CalculationResult.from_dict(r) for r in self._read_raw()]

    def load_memory_all(self) -> list[MemoryEntry]:
        """Load all memory entries (both ResultEntry and ErrorEntry)."""
        return [MemoryEntry.from_dict(r) for r in self._read_memory_raw()]

    def _read_raw(self) -> list:
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _read_memory_raw(self) -> list:
        if not self._memory_filepath.exists():
            return []
        try:
            with open(self._memory_filepath) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_raw(self, records: list) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)

    def _write_memory_raw(self, records: list) -> None:
        self._memory_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self._memory_filepath, "w") as f:
            json.dump(records, f, indent=2)
