from typing import Optional

from ..models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing MemoryEntry domain objects in-memory.

    Provides store() and retrieve() methods for lifecycle management without
    any persistence logic. All file I/O responsibilities are delegated to the
    storage layer (JsonStorage).

    This is a stateful service that accumulates entries for the duration of
    the application session.
    """

    def __init__(self) -> None:
        """Initialize MemoryService with an empty entry list.

        Constructor takes no arguments. Internal state is initialized here.
        """
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory.

        Args:
            entry: A MemoryEntry domain object with auto-generated id and timestamp.

        Returns:
            None

        Behavior:
            - Accepts the entry as-is (does not modify id or timestamp)
            - Appends entry to internal list
            - Does NOT validate, serialize, or persist to any storage
            - Does NOT raise exceptions on duplicate IDs (allows identical entries)
        """
        self._entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            list[MemoryEntry]: A list of all entries in order of insertion.
                              Returns empty list if no entries have been stored.

        Behavior:
            - Returns a reference to the internal list (not a copy)
            - Preserves insertion order
            - Preserves all fields (id, timestamp, operation, operands, result, success, execution_time_ms)
            - Does NOT filter, sort, or transform entries
        """
        return self._entries

    def query(self, operation: Optional[str] = None, success: Optional[bool] = None) -> list[MemoryEntry]:
        """Filter stored entries by operation type and/or success state.

        Enables querying the in-memory entry collection using optional filters on
        operation type and success state. Filters combine with AND logic: if both
        parameters are provided, results must match both conditions.

        Args:
            operation: Optional operation type filter (e.g., "add", "multiply").
                       Performs case-sensitive exact string matching.
                       None means no filter on operation.
            success: Optional success state filter (True or False).
                     Performs exact boolean matching.
                     None means no filter on success state.

        Returns:
            list[MemoryEntry]: List of entries matching ALL provided filters.
                              Returns empty list if no matches found.
                              Returns copy of all entries if both parameters are None.
                              Preserves insertion order from internal _entries list.

        Filter Logic (AND Combination):
        - Both parameters None → return all entries (same as retrieve())
        - operation only → return entries where entry.operation == operation
        - success only → return entries where entry.success == success
        - both provided → return entries where BOTH conditions match

        Example:
            service.query()                    # all entries
            service.query(operation="add")     # entries with "add" operations
            service.query(success=True)        # successful entries
            service.query(operation="multiply", success=False)  # failed multiply ops
        """
        return [
            entry for entry in self._entries
            if (operation is None or entry.operation == operation)
            and (success is None or entry.success == success)
        ]
