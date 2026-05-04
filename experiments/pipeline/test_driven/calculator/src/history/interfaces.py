from typing import Protocol

from ..models.memory_entry import MemoryEntry


class MemoryBackend(Protocol):
    def store(self, entry: MemoryEntry) -> None: ...
    def retrieve(self) -> list[MemoryEntry]: ...
