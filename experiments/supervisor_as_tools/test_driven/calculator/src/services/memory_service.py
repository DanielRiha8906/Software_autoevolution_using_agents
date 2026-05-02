from ..models.memory_entry import MemoryEntry


class MemoryService:
    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        return self._entries.copy()
