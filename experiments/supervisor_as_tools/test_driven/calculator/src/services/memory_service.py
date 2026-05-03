from typing import List
from src.models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing MemoryEntry lifecycle."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory."""
        self._entries.append(entry)

    def retrieve(self) -> List[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects."""
        return self._entries
