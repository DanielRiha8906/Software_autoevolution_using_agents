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
