from ..models.memory_entry import MemoryEntry
from ..models.memory_statistics import MemoryStatistics
from ..storage.memory_json_storage import MemoryJsonStorage


class MemoryService:
    def __init__(self, storage: MemoryJsonStorage) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        self.storage.save(entry)

    def retrieve_by_id(self, entry_id: str) -> MemoryEntry | None:
        all_entries = self.storage.load_all()
        for entry in all_entries:
            if entry.id == entry_id:
                return entry
        return None

    def retrieve_all(self) -> list[MemoryEntry]:
        return self.storage.load_all()

    def retrieve_by_operation(self, operation: str) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if e.operation == operation]

    def retrieve_successes(self) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if e.success]

    def retrieve_failures(self) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if not e.success]

    def clear(self) -> None:
        self.storage.clear()

    def count(self) -> int:
        return len(self.storage.load_all())

    def count_by_status(self) -> dict[str, int]:
        all_entries = self.storage.load_all()
        success_count = sum(1 for e in all_entries if e.success)
        failure_count = sum(1 for e in all_entries if not e.success)
        return {"success": success_count, "failure": failure_count}

    def count_by_operation(self) -> dict[str, int]:
        all_entries = self.storage.load_all()
        counts: dict[str, int] = {}
        for entry in all_entries:
            counts[entry.operation] = counts.get(entry.operation, 0) + 1
        return counts

    def retrieve_by_filter(
        self,
        operation: str | None = None,
        success: bool | None = None
    ) -> list[MemoryEntry]:
        """
        Retrieve memory entries with optional filtering.

        Args:
            operation: Filter by operation name (e.g., "add"). If None, no operation filter.
            success: Filter by status. True = successes only, False = failures only, None = all.

        Returns:
            List of MemoryEntry objects matching all non-None filters (AND semantics).
            Returns empty list if no matches or if memory is empty.
        """
        all_entries = self.storage.load_all()
        results = all_entries

        if operation is not None:
            results = [e for e in results if e.operation == operation]

        if success is not None:
            results = [e for e in results if e.success == success]

        return results

    def get_operation_error_rates(self) -> dict[str, float]:
        """
        Calculate error rate (percentage) for each operation type.

        Returns:
            Dictionary mapping operation names to error rates (0-100).
            Operations with no entries have 0.0 error rate.
        """
        all_entries = self.storage.load_all()
        operation_counts: dict[str, int] = {}
        operation_errors: dict[str, int] = {}

        for entry in all_entries:
            operation_counts[entry.operation] = operation_counts.get(entry.operation, 0) + 1
            if not entry.success:
                operation_errors[entry.operation] = operation_errors.get(entry.operation, 0) + 1

        error_rates: dict[str, float] = {}
        for op, count in operation_counts.items():
            error_count = operation_errors.get(op, 0)
            error_rate = (error_count / count * 100) if count > 0 else 0.0
            error_rates[op] = error_rate

        return error_rates

    def compute_statistics(self, filter_operation: str | None = None) -> MemoryStatistics:
        """
        Compute aggregated statistics from memory entries.

        Args:
            filter_operation: If provided, compute statistics only for this operation type.
                            If None, compute statistics for all entries.

        Returns:
            MemoryStatistics object with computed values. Returns all zeros if memory is empty.
        """
        entries = self.retrieve_by_filter(operation=filter_operation)

        # Count totals
        total_entries = len(entries)
        total_errors = sum(1 for e in entries if not e.success)

        # Calculate error rate
        error_rate = (total_errors / total_entries * 100) if total_entries > 0 else 0.0

        # Calculate average execution time
        if entries:
            total_time = sum(e.execution_time_ms for e in entries)
            avg_execution_time_ms = total_time / total_entries
        else:
            avg_execution_time_ms = 0.0

        # Find min/max execution times
        if entries:
            execution_times = [e.execution_time_ms for e in entries]
            min_execution_time_ms = min(execution_times)
            max_execution_time_ms = max(execution_times)
        else:
            min_execution_time_ms = None
            max_execution_time_ms = None

        # Count operations
        operation_counts: dict[str, int] = {}
        for entry in entries:
            operation_counts[entry.operation] = operation_counts.get(entry.operation, 0) + 1

        # Get operation error rates (use filtered list if applicable)
        if filter_operation:
            operation_error_rates = {filter_operation: error_rate}
        else:
            operation_error_rates = self.get_operation_error_rates()

        return MemoryStatistics(
            operation_counts=operation_counts,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_execution_time_ms=avg_execution_time_ms,
            total_entries=total_entries,
            min_execution_time_ms=min_execution_time_ms,
            max_execution_time_ms=max_execution_time_ms,
            operation_error_rates=operation_error_rates,
        )
