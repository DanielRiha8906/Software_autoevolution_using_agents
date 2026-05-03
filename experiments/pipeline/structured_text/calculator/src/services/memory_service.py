from ..models.memory_entry import MemoryEntry
from ..storage.memory_json_storage import MemoryJsonStorage


class MemoryService:
    """
    Manages the lifecycle of MemoryEntry objects.

    Coordinates storage and retrieval of calculation memory entries,
    delegating persistence to MemoryJsonStorage. Provides a clean
    separation between service logic and storage implementation.
    """

    def __init__(self, storage: MemoryJsonStorage) -> None:
        """
        Initialize the memory service with a storage backend.

        Args:
            storage: MemoryJsonStorage instance for persisting entries.
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
