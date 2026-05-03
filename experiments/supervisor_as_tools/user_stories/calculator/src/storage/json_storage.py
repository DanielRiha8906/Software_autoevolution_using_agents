import json
from pathlib import Path
from typing import TYPE_CHECKING

from ..models.calculation_result import CalculationResult

if TYPE_CHECKING:
    from ..models.memory_entry import MemoryEntry


class JsonStorage:
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)

    def save(self, record: "CalculationResult | MemoryEntry") -> None:
        raw_records = self._read_raw_dicts()
        raw_records.append(record.to_dict())
        self._write_raw(raw_records)

    def load_all(self) -> list:
        raw_dicts = self._read_raw_dicts()
        result = []
        for record_dict in raw_dicts:
            if "entry_id" in record_dict:
                from ..models.memory_entry import MemoryEntry
                result.append(MemoryEntry.from_dict(record_dict))
            else:
                result.append(CalculationResult.from_dict(record_dict))
        return result

    def _read_raw_dicts(self) -> list:
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_raw(self, records: list) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
