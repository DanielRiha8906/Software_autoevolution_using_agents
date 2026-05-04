import json
import re
from pathlib import Path
from json import JSONDecodeError

from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class ImportExportService:
    """Service for exporting and importing calculation history."""

    # Valid operation names
    _VALID_OPERATIONS = {
        "add", "subtract", "multiply", "divide",
        "square", "sqrt", "power", "modulo"
    }

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize the service with a memory service instance.

        Args:
            memory_service: MemoryService instance for retrieving/storing entries
        """
        self.memory_service = memory_service

    def export_history(
        self,
        filepath: Path | str,
        entries: list[MemoryEntry] | None = None,
    ) -> dict[str, int]:
        """Export entries to a JSON file.

        Args:
            filepath: Destination JSON file path
            entries: Entries to export (None = export all from memory_service)

        Returns:
            {"exported_count": int, "file_path": str}

        Raises:
            ValueError: If filepath does not end with .json
            OSError: If file cannot be written
        """
        filepath = Path(filepath)

        # Validate file extension
        if not filepath.name.endswith(".json"):
            raise ValueError(
                f"Export file must have .json extension, got: {filepath.name}"
            )

        # Get entries to export
        if entries is None:
            entries = self.memory_service.retrieve()

        # Convert to dicts
        data = [entry.to_dict() for entry in entries]

        # Write to file
        filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise OSError(f"Failed to write export file '{filepath}': {e}")

        return {
            "exported_count": len(data),
            "file_path": str(filepath),
        }

    def import_history(
        self,
        filepath: Path | str,
        mode: str = "merge",
    ) -> dict[str, int | list]:
        """Import entries from a JSON file with validation.

        Args:
            filepath: Source JSON file path
            mode: "merge" (append) or "replace" (overwrite all)

        Returns:
            {
                "imported_count": int,
                "skipped_count": int,
                "skipped_entries": list[dict],
                "duplicates_count": int,
                "invalid_count": int
            }

        Raises:
            ValueError: If filepath does not end with .json
            OSError: If file cannot be read
            JSONDecodeError: If file is not valid JSON
        """
        filepath = Path(filepath)

        # Validate file extension
        if not filepath.name.endswith(".json"):
            raise ValueError(
                f"Import file must have .json extension, got: {filepath.name}"
            )

        # Read and parse JSON
        if not filepath.exists():
            raise OSError(f"Import file not found: {filepath}")

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise JSONDecodeError(
                f"Invalid JSON in import file '{filepath}': {e.msg}",
                e.doc,
                e.pos,
            )
        except OSError as e:
            raise OSError(f"Failed to read import file '{filepath}': {e}")

        # Ensure data is a list
        if not isinstance(data, list):
            raise ValueError("Import file must contain a JSON array of entries")

        # Apply mode: clear storage first if replace mode
        if mode == "replace":
            # Clear all existing entries
            self.memory_service.clear()

        # Get existing entries for duplicate detection
        existing_entries = self.memory_service.retrieve()

        # Process entries
        imported_entries = []
        skipped_entries = []
        duplicates_count = 0
        invalid_count = 0

        for entry_dict in data:
            # Validate entry
            is_valid, error_msg = self._validate_entry(entry_dict)
            if not is_valid:
                skipped_entries.append(entry_dict)
                invalid_count += 1
                continue

            # Try to create MemoryEntry
            try:
                entry = MemoryEntry.from_dict(entry_dict)
            except (TypeError, KeyError, ValueError) as e:
                skipped_entries.append(entry_dict)
                invalid_count += 1
                continue

            # Check for duplicates (against existing entries in current db + already imported in this batch)
            if self._detect_duplicate(entry, existing_entries + imported_entries):
                skipped_entries.append(entry_dict)
                duplicates_count += 1
                continue

            imported_entries.append(entry)

        # Store imported entries
        for entry in imported_entries:
            self.memory_service.store(entry)

        return {
            "imported_count": len(imported_entries),
            "skipped_count": len(skipped_entries),
            "skipped_entries": skipped_entries,
            "duplicates_count": duplicates_count,
            "invalid_count": invalid_count,
        }

    def _validate_entry(self, data: dict) -> tuple[bool, str | None]:
        """Validate a single entry dict against MemoryEntry schema.

        Returns:
            (is_valid, error_message_or_none)
        """
        if not isinstance(data, dict):
            return False, "Entry must be a dictionary"

        # Check required fields
        required = [
            "operation", "operand_a", "operand_b",
            "result", "error", "error_type",
            "execution_time_ms", "timestamp", "uuid"
        ]
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Validate operation
        operation = data.get("operation")
        if not isinstance(operation, str) or operation not in self._VALID_OPERATIONS:
            return False, f"Invalid operation: {operation}"

        # Validate operands
        try:
            operand_a = float(data.get("operand_a"))
            operand_b = float(data.get("operand_b"))
        except (TypeError, ValueError):
            return False, "operand_a and operand_b must be numeric"

        # Validate result (can be None or float)
        result = data.get("result")
        if result is not None:
            try:
                float(result)
            except (TypeError, ValueError):
                return False, "result must be numeric or null"

        # Validate error and error_type (can be None or str)
        error = data.get("error")
        if error is not None and not isinstance(error, str):
            return False, "error must be string or null"

        error_type = data.get("error_type")
        if error_type is not None and not isinstance(error_type, str):
            return False, "error_type must be string or null"

        # Validate execution_time_ms
        try:
            exec_time = float(data.get("execution_time_ms"))
            if exec_time < 0:
                return False, "execution_time_ms must be >= 0"
        except (TypeError, ValueError):
            return False, "execution_time_ms must be numeric"

        # Validate timestamp (ISO 8601 format)
        timestamp = data.get("timestamp")
        if not isinstance(timestamp, str):
            return False, "timestamp must be a string"
        # Basic ISO 8601 check: YYYY-MM-DDTHH:MM:SS...
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        if not re.match(iso_pattern, timestamp):
            return False, f"timestamp must be ISO 8601 format, got: {timestamp}"

        # Validate uuid (UUID format)
        uuid_val = data.get("uuid")
        if not isinstance(uuid_val, str):
            return False, "uuid must be a string"
        # Basic UUID check: 36 characters with 4 hyphens
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(uuid_pattern, uuid_val, re.IGNORECASE):
            return False, f"uuid must be valid UUID format, got: {uuid_val}"

        return True, None

    def _detect_duplicate(
        self,
        entry: MemoryEntry,
        existing: list[MemoryEntry],
    ) -> bool:
        """Check if entry already exists by UUID or by (operation, operand_a, operand_b, timestamp).

        Args:
            entry: Entry to check
            existing: List of existing entries to compare against

        Returns:
            True if a duplicate is detected, False otherwise
        """
        for existing_entry in existing:
            # Check UUID match first
            if entry.uuid == existing_entry.uuid:
                return True

            # Check (operation, operand_a, operand_b, timestamp) tuple match
            if (
                entry.operation == existing_entry.operation
                and entry.operand_a == existing_entry.operand_a
                and entry.operand_b == existing_entry.operand_b
                and entry.timestamp == existing_entry.timestamp
            ):
                return True

        return False
