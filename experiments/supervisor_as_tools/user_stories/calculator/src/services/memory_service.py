from ..models.memory_entry import MemoryEntry


class MemoryService:
    def __init__(self, storage) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        return self.storage.load_all()
