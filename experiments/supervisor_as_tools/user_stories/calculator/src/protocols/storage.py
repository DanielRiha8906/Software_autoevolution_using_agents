from typing import Protocol


class StorageExportable(Protocol):
    """Protocol for services that support memory export."""

    def export_memory_entries(self, output_path: str) -> int:
        """Export memory entries to a file. Returns count exported."""
        ...


class StorageImportable(Protocol):
    """Protocol for services that support memory import."""

    def import_memory_entries(
        self, input_path: str, overwrite: bool = False
    ) -> tuple[int, int]:
        """Import memory entries from a file. Returns (imported, skipped)."""
        ...
