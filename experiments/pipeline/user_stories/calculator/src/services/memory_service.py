from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage


class MemoryService:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        return self.storage.load_all()

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

    def filter(
        self,
        operations: list[str] | None = None,
        state: str | None = None,
    ) -> list[MemoryEntry]:
        """Filter history by operations and/or state.

        Args:
            operations: List of operation names to filter by. None or empty list means include all.
            state: One of 'success', 'error', or 'both'. None is treated as 'both'.

        Returns:
            List of MemoryEntry objects matching all specified criteria, in chronological order.

        Raises:
            ValueError: If state is provided and not one of 'success', 'error', or 'both'.
        """
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
