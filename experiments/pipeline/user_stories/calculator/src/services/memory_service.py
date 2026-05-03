from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage


class MemoryService:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        return self.storage.load_all()
