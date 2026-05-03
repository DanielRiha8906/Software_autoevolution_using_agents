from ..models.memory_entry import MemoryEntry
from ..storage.memory_json_storage import MemoryJsonStorage


class MemoryService:
    def __init__(self, storage: MemoryJsonStorage) -> None:
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        self.storage.save(entry)

    def retrieve_by_id(self, entry_id: str) -> MemoryEntry | None:
        all_entries = self.storage.load_all()
        for entry in all_entries:
            if entry.id == entry_id:
                return entry
        return None

    def retrieve_all(self) -> list[MemoryEntry]:
        return self.storage.load_all()

    def retrieve_by_operation(self, operation: str) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if e.operation == operation]

    def retrieve_successes(self) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if e.success]

    def retrieve_failures(self) -> list[MemoryEntry]:
        all_entries = self.storage.load_all()
        return [e for e in all_entries if not e.success]

    def clear(self) -> None:
        self.storage.clear()

    def count(self) -> int:
        return len(self.storage.load_all())

    def count_by_status(self) -> dict[str, int]:
        all_entries = self.storage.load_all()
        success_count = sum(1 for e in all_entries if e.success)
        failure_count = sum(1 for e in all_entries if not e.success)
        return {"success": success_count, "failure": failure_count}

    def count_by_operation(self) -> dict[str, int]:
        all_entries = self.storage.load_all()
        counts: dict[str, int] = {}
        for entry in all_entries:
            counts[entry.operation] = counts.get(entry.operation, 0) + 1
        return counts
