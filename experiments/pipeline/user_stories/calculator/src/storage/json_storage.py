import json
from pathlib import Path

from ..models.calculation_result import CalculationResult


class JsonStorage:
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)

    def save(self, result: CalculationResult) -> None:
        records = self._read_raw()
        records.append(result.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[CalculationResult]:
        return [CalculationResult.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
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
