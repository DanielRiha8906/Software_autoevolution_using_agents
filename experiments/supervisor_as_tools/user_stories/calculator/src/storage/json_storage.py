import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..models.calculation_result import CalculationResult

if TYPE_CHECKING:
    from ..models.memory_entry import MemoryEntry

logger = logging.getLogger(__name__)


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

    def export_memory_entries(self, output_path: str, entries: list = None) -> int:
        """Export memory entries to a JSON file.

        Args:
            output_path: The file path where entries will be exported.
            entries: Optional list of MemoryEntry objects to export.
                    If None, all MemoryEntry objects from storage are exported.

        Returns:
            The number of entries exported.

        Raises:
            IOError: If the file cannot be written.
        """
        if entries is None:
            entries = self._get_all_memory_entries()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        entries_dicts = [entry.to_dict() for entry in entries]

        try:
            with open(output_file, "w") as f:
                json.dump(entries_dicts, f, indent=2)
            return len(entries_dicts)
        except OSError as exc:
            logger.error(f"Failed to export memory entries to {output_path}: {exc}")
            raise IOError(f"Failed to write to {output_path}") from exc

    def import_memory_entries(
        self, input_path: str, overwrite: bool = False
    ) -> tuple[int, int]:
        """Import memory entries from a JSON file.

        Args:
            input_path: The file path to import from.
            overwrite: If True, replace all storage with imported entries.
                      If False, merge imported entries with existing ones.

        Returns:
            A tuple of (imported_count, skipped_invalid_count).

        Raises:
            FileNotFoundError: If the input file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        input_file = Path(input_path)

        if not input_file.exists():
            logger.error(f"Import file not found: {input_path}")
            raise FileNotFoundError(f"Import file not found: {input_path}")

        try:
            with open(input_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in {input_path}: {exc}")
            raise json.JSONDecodeError(f"Invalid JSON in {input_path}", exc.doc, exc.pos) from exc
        except OSError as exc:
            logger.error(f"Failed to read {input_path}: {exc}")
            raise IOError(f"Failed to read {input_path}") from exc

        if not isinstance(data, list):
            logger.error(f"Expected JSON array at root of {input_path}")
            raise json.JSONDecodeError(
                f"Expected JSON array at root of {input_path}",
                "",
                0,
            )

        imported_count = 0
        skipped_invalid_count = 0

        from ..models.memory_entry import MemoryEntry

        # Validate and convert to MemoryEntry objects
        valid_entries = []
        for entry_dict in data:
            is_valid, error_msg = self._validate_memory_entry_dict(entry_dict)
            if is_valid:
                valid_entries.append(MemoryEntry.from_dict(entry_dict))
                imported_count += 1
            else:
                logger.warning(f"Skipped invalid entry: {error_msg}")
                skipped_invalid_count += 1

        # Handle storage: overwrite or merge
        if overwrite:
            self._write_raw([entry.to_dict() for entry in valid_entries])
        else:
            # Merge with existing entries
            existing = self._read_raw_dicts()
            existing.extend([entry.to_dict() for entry in valid_entries])
            self._write_raw(existing)

        return imported_count, skipped_invalid_count

    def _validate_memory_entry_dict(self, data: dict) -> tuple[bool, str]:
        """Validate a dictionary as a valid MemoryEntry.

        Args:
            data: The dictionary to validate.

        Returns:
            A tuple of (is_valid, error_message).
            is_valid is True if the dict can be converted to a MemoryEntry.
            error_message is a string describing the validation failure (empty if valid).
        """
        required_fields = [
            "entry_id",
            "operation_name",
            "operand_a",
            "operand_b",
            "result",
            "success",
            "timestamp",
            "execution_time_ms",
        ]
        optional_fields = ["error_message"]

        if not isinstance(data, dict):
            return False, f"Entry must be a dictionary, got {type(data).__name__}"

        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Basic type validation
        try:
            if not isinstance(data.get("entry_id"), str):
                return False, "entry_id must be a string"
            if not isinstance(data.get("operation_name"), str):
                return False, "operation_name must be a string"
            if not isinstance(data.get("operand_a"), (int, float)):
                return False, "operand_a must be a number"
            if not isinstance(data.get("operand_b"), (int, float)):
                return False, "operand_b must be a number"
            if data.get("result") is not None and not isinstance(data.get("result"), (int, float)):
                return False, "result must be a number or null"
            if not isinstance(data.get("success"), bool):
                return False, "success must be a boolean"
            if not isinstance(data.get("timestamp"), str):
                return False, "timestamp must be a string"
            if not isinstance(data.get("execution_time_ms"), (int, float)):
                return False, "execution_time_ms must be a number"
            if data.get("error_message") is not None and not isinstance(
                data.get("error_message"), str
            ):
                return False, "error_message must be a string or null"
        except (TypeError, AttributeError) as exc:
            return False, f"Type validation error: {exc}"

        return True, ""

    def _get_all_memory_entries(self) -> list:
        """Get all MemoryEntry objects from storage.

        Returns:
            A list of MemoryEntry objects.
        """
        from ..models.memory_entry import MemoryEntry

        all_records = self.load_all()
        return [r for r in all_records if isinstance(r, MemoryEntry)]
