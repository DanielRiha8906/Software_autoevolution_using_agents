import json
from pathlib import Path

from ..models.memory_entry import MemoryEntry
from ..models.calculation_statistics import CalculationStatistics
from ..protocols import Storage


class MemoryService:
    """
    Manages the lifecycle of MemoryEntry objects.

    Coordinates storage and retrieval of calculation memory entries,
    delegating persistence to Storage backend. Provides a clean
    separation between service logic and storage implementation.
    """

    def __init__(self, storage: Storage[MemoryEntry]) -> None:
        """
        Initialize the memory service with a storage backend.

        Args:
            storage: Storage[MemoryEntry] instance for persisting entries.
        """
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in persistent storage.

        Args:
            entry: MemoryEntry object to persist.
        """
        self.storage.save(entry)

    def retrieve_all(self) -> list[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            List of all MemoryEntry objects in storage. Returns empty
            list if no entries have been stored or storage is empty.
        """
        return self.storage.load_all()

    def filter_by_operation(self, operation_name: str) -> list[MemoryEntry]:
        """
        Filter memory entries by operation name (case-insensitive).

        Args:
            operation_name: Name of the operation to filter by (e.g., "add", "sqrt").
                           Comparison is case-insensitive.

        Returns:
            List of entries matching the operation, in insertion order.
            Returns empty list if no matches found.
        """
        entries = self.retrieve_all()
        operation_lower = operation_name.lower()
        return [entry for entry in entries if entry.operation.lower() == operation_lower]

    def filter_by_success(self, success: bool) -> list[MemoryEntry]:
        """
        Filter memory entries by success/failure status.

        Args:
            success: True to return only successful calculations,
                     False to return only failed calculations.

        Returns:
            List of entries matching the success status, in insertion order.
            Returns empty list if no matches found.
        """
        entries = self.retrieve_all()
        return [entry for entry in entries if entry.success == success]

    def filter_by_execution_time(
        self, min_ms: float = 0.0, max_ms: float = float('inf')
    ) -> list[MemoryEntry]:
        """
        Filter memory entries by execution time range (milliseconds).

        Args:
            min_ms: Minimum execution time (inclusive). Defaults to 0.0.
            max_ms: Maximum execution time (inclusive). Defaults to infinity.

        Returns:
            List of entries with execution_time_ms in [min_ms, max_ms],
            in insertion order. Returns empty list if no matches found.
        """
        entries = self.retrieve_all()
        return [
            entry
            for entry in entries
            if min_ms <= entry.execution_time_ms <= max_ms
        ]

    def compute_statistics(self) -> CalculationStatistics:
        """
        Compute and return aggregated statistics over all stored MemoryEntry objects.

        Returns:
            CalculationStatistics object with:
            - operation_counts: dict mapping operation name to usage count
            - total_calculations: total number of calculations
            - error_count: total number of failed calculations
            - error_percentage: percentage of all calculations that failed
            - average_execution_time_ms: mean execution time across all calculations
            - min_execution_time_ms: minimum execution time across all calculations
            - max_execution_time_ms: maximum execution time across all calculations
            - per_operation_stats: dict with per-operation breakdown containing
              count, error_count, error_rate, avg_time_ms, min_time_ms, max_time_ms
        """
        entries = self.retrieve_all()

        # Handle empty storage
        if not entries:
            return CalculationStatistics(
                operation_counts={},
                total_calculations=0,
                error_count=0,
                error_percentage=0.0,
                average_execution_time_ms=0.0,
                min_execution_time_ms=0.0,
                max_execution_time_ms=0.0,
                per_operation_stats={},
            )

        # Global statistics
        total_count = len(entries)
        error_count = sum(1 for e in entries if not e.success)
        error_percentage = (error_count / total_count * 100) if total_count > 0 else 0.0
        avg_time = sum(e.execution_time_ms for e in entries) / total_count if total_count > 0 else 0.0
        min_time = min(e.execution_time_ms for e in entries) if entries else 0.0
        max_time = max(e.execution_time_ms for e in entries) if entries else 0.0

        # Operation counts
        operation_counts: dict[str, int] = {}
        for entry in entries:
            operation_counts[entry.operation] = operation_counts.get(entry.operation, 0) + 1

        # Per-operation statistics
        per_operation_stats: dict[str, dict] = {}
        for operation in operation_counts:
            op_entries = [e for e in entries if e.operation == operation]
            op_error_count = sum(1 for e in op_entries if not e.success)
            op_error_rate = (op_error_count / len(op_entries) * 100) if op_entries else 0.0
            op_avg_time = sum(e.execution_time_ms for e in op_entries) / len(op_entries) if op_entries else 0.0
            op_min_time = min(e.execution_time_ms for e in op_entries) if op_entries else 0.0
            op_max_time = max(e.execution_time_ms for e in op_entries) if op_entries else 0.0

            per_operation_stats[operation] = {
                "count": len(op_entries),
                "error_count": op_error_count,
                "error_rate": op_error_rate,
                "avg_time_ms": op_avg_time,
                "min_time_ms": op_min_time,
                "max_time_ms": op_max_time,
            }

        return CalculationStatistics(
            operation_counts=operation_counts,
            total_calculations=total_count,
            error_count=error_count,
            error_percentage=error_percentage,
            average_execution_time_ms=avg_time,
            min_execution_time_ms=min_time,
            max_execution_time_ms=max_time,
            per_operation_stats=per_operation_stats,
        )

    def export_to_file(self, filepath: Path | str) -> int:
        """
        Export all memory entries to a JSON file.

        Creates parent directories if they don't exist. Overwrites any
        existing file at the given path.

        Args:
            filepath: Destination file path for the JSON export.

        Returns:
            Count of entries exported.

        Raises:
            OSError: If file cannot be written (permission denied, etc.)
        """
        filepath = Path(filepath)
        entries = self.retrieve_all()
        records = [entry.to_dict() for entry in entries]

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(filepath, "w") as f:
            json.dump(records, f, indent=2)

        return len(entries)

    def import_from_file(
        self, filepath: Path | str, skip_invalid: bool = False
    ) -> tuple[int, list[dict]]:
        """
        Import memory entries from a JSON file and append to storage.

        Validates the file and each entry before storing. If skip_invalid
        is True, invalid entries are skipped and reported. If False, the
        first invalid entry raises an exception.

        Args:
            filepath: Source JSON file path (must exist and contain valid JSON array).
            skip_invalid: If True, skip malformed entries and continue.
                         If False, raise on first invalid entry.

        Returns:
            Tuple of (count_imported, list_of_skipped_entries).
            Each skipped entry is a dict with keys: "data" and "error".

        Raises:
            FileNotFoundError: If file does not exist.
            json.JSONDecodeError: If JSON is malformed and skip_invalid=False.
            ValueError: If JSON is not an array, or on first invalid entry
                       and skip_invalid=False.
        """
        filepath = Path(filepath)

        # Check file exists
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read and parse JSON
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {filepath}: {e.msg}",
                e.doc,
                e.pos,
            ) from e

        # Validate it's an array
        if not isinstance(data, list):
            raise ValueError(f"JSON must be an array, got {type(data).__name__}")

        # Process entries
        skipped: list[dict] = []
        imported_count = 0

        for idx, entry_data in enumerate(data):
            try:
                # Validate and create MemoryEntry
                if not isinstance(entry_data, dict):
                    raise ValueError(f"Entry {idx} is not a dict")

                entry = MemoryEntry.from_dict(entry_data)
                self.store(entry)
                imported_count += 1

            except Exception as e:
                error_msg = str(e)
                skipped.append({"data": entry_data, "error": error_msg})

                if not skip_invalid:
                    raise ValueError(
                        f"Invalid entry at index {idx}: {error_msg}"
                    ) from e

        return (imported_count, skipped)
