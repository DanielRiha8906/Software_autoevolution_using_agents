from ..models.memory_entry import MemoryEntry
from ..storage.storage import StorageBackend
from .memory.history_filter import HistoryFilter


class MemoryService:
    """Manages storage and retrieval of calculation history.

    Depends on StorageBackend abstraction, not concrete implementations.
    Delegates filtering to HistoryFilter implementations.
    """

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """Store a single entry.

        Args:
            entry: MemoryEntry to persist.
        """
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored entries.

        Returns:
            List of all MemoryEntry objects in chronological order.
        """
        return self.storage.load_all()

    def filter(
        self,
        filters: list[HistoryFilter] | None = None,
        operations: list[str] | None = None,
        state: str | None = None,
    ) -> list[MemoryEntry]:
        """Filter history using HistoryFilter objects or legacy keyword arguments.

        Supports both new API (filters list) and legacy API (operations/state keywords).
        If both are provided, filters take precedence.

        Args:
            filters: List of HistoryFilter objects to apply. None or empty list means no filtering.
            operations: (Legacy) List of operation names to filter by. Ignored if filters is provided.
            state: (Legacy) One of 'success', 'error', or 'both'. Ignored if filters is provided.

        Returns:
            Filtered list of MemoryEntry objects.

        Raises:
            ValueError: If state is provided (via legacy API) and not one of 'success', 'error', or 'both'.
        """
        # If new API (filters) is used, use it directly
        if filters:
            entries = self.retrieve()
            result = entries
            for f in filters:
                result = f.apply(result)
            return result

        # Fall back to legacy API for backward compatibility
        # Normalize inputs
        if state is None:
            state = "both"
        if operations is None:
            operations = []

        # Validate state
        if state not in ["success", "error", "both"]:
            raise ValueError(
                f"Invalid state: '{state}'. Must be one of: 'success', 'error', 'both'"
            )

        history = self.retrieve()

        # Filter by operations
        if operations:
            history = [e for e in history if e.operation in operations]

        # Filter by state
        if state != "both":
            filtered = []
            for entry in history:
                is_success = entry.result is not None and entry.error is None
                is_error = entry.result is None and entry.error is not None

                if state == "success" and is_success:
                    filtered.append(entry)
                elif state == "error" and is_error:
                    filtered.append(entry)
            history = filtered

        return history

    def clear(self) -> None:
        """Clear all stored entries.

        Used for import "replace" mode and other bulk operations.
        """
        self.storage.save_all([])

    # Legacy methods for backward compatibility with existing tests/callers
    def filter_by_operation(self, operation_name: str) -> list[MemoryEntry]:
        """Filter history by a single operation name.

        Args:
            operation_name: The operation to filter by (e.g., 'add', 'divide').

        Returns:
            List of MemoryEntry objects matching the operation, in chronological order.
        """
        return [entry for entry in self.retrieve() if entry.operation == operation_name]

    def filter_by_operations(self, operation_names: list[str]) -> list[MemoryEntry]:
        """Filter history by multiple operation names.

        Args:
            operation_names: List of operations to filter by.

        Returns:
            List of MemoryEntry objects matching any of the operations, in chronological order.
        """
        return [entry for entry in self.retrieve() if entry.operation in operation_names]

    def filter_by_state(self, state: str) -> list[MemoryEntry]:
        """Filter history by success/error state.

        Args:
            state: One of 'success', 'error', or 'both'.
                  - 'success': entries where result is not None and error is None
                  - 'error': entries where result is None and error is not None
                  - 'both': all entries

        Returns:
            List of MemoryEntry objects matching the state, in chronological order.

        Raises:
            ValueError: If state is not one of 'success', 'error', or 'both'.
        """
        if state not in ["success", "error", "both"]:
            raise ValueError(
                f"Invalid state: '{state}'. Must be one of: 'success', 'error', 'both'"
            )

        history = self.retrieve()
        if state == "both":
            return history

        filtered = []
        for entry in history:
            is_success = entry.result is not None and entry.error is None
            is_error = entry.result is None and entry.error is not None

            if state == "success" and is_success:
                filtered.append(entry)
            elif state == "error" and is_error:
                filtered.append(entry)

        return filtered
