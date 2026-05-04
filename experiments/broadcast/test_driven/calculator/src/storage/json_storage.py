"""JSON storage backend for calculation results.

This module provides persistent JSON storage for calculation results,
decoupled from the service and calculation layers.
"""

import json
from pathlib import Path

from ..models.calculation_result import CalculationResult


class JsonStorage:
    """JSON file-based storage for calculation results.

    Handles persistence of CalculationResult objects to JSON files.
    This storage layer is separate from the calculation engine and
    from the service orchestration layer.
    """

    def __init__(self, filepath: Path | str) -> None:
        """Initialize storage with a file path.

        Args:
            filepath: Path to the JSON file for storage
        """
        self.filepath = Path(filepath)

    def save(self, result: CalculationResult) -> None:
        """Save a calculation result to storage.

        Args:
            result: The CalculationResult to save
        """
        records = self._read_raw()
        records.append(result.to_dict())
        self._write_raw(records)

    def load_all(self) -> list[CalculationResult]:
        """Load all stored calculation results.

        Returns:
            List of CalculationResult objects
        """
        return [CalculationResult.from_dict(r) for r in self._read_raw()]

    def _read_raw(self) -> list:
        """Read raw JSON data from file.

        Returns:
            List of dictionaries, or empty list if file doesn't exist
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
            records: List of dictionaries to write
        """
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)
