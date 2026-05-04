import time
from ..models.memory_entry import MemoryEntry
from ..models.operation import Operation
from ..storage.json_storage import JsonStorage
from .calculator_service import CalculatorService


class MemoryService:
    def __init__(self, calculator_service: CalculatorService, storage: JsonStorage) -> None:
        self.calculator_service = calculator_service
        self.storage = storage

    def record(self, operation: str, operand_a: float, operand_b: float) -> MemoryEntry:
        try:
            operation_enum = Operation.from_string(operation)
        except ValueError as e:
            raise ValueError(f"Invalid operation: {e}")

        start_time = time.perf_counter()
        try:
            result = self.calculator_service.execute(operation, operand_a, operand_b)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            entry = MemoryEntry(
                operation_name=operation_enum.value,
                operand_a=operand_a,
                operand_b=operand_b,
                result=result,
                success=True,
                error_message=None,
                execution_time_ms=execution_time_ms,
            )
        except Exception as exc:
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            entry = MemoryEntry(
                operation_name=operation_enum.value,
                operand_a=operand_a,
                operand_b=operand_b,
                result=None,
                success=False,
                error_message=str(exc),
                execution_time_ms=execution_time_ms,
            )

        self.storage.save(entry)
        return entry

    def get_all_entries(self) -> list[MemoryEntry]:
        all_records = self.storage.load_all()
        return [r for r in all_records if isinstance(r, MemoryEntry)]

    def filter_by_operation(self, operation_name: str) -> list[MemoryEntry]:
        """Filter memory entries by operation name (case-insensitive).

        Args:
            operation_name: The operation name to filter by.

        Returns:
            List of MemoryEntry objects matching the operation.
        """
        all_entries = self.get_all_entries()
        return [e for e in all_entries if e.operation_name.lower() == operation_name.lower()]

    def filter_by_success(self, success: bool) -> list[MemoryEntry]:
        """Filter memory entries by success status.

        Args:
            success: True to return successful entries, False for failed entries.

        Returns:
            List of MemoryEntry objects matching the success status.
        """
        all_entries = self.get_all_entries()
        return [e for e in all_entries if e.success == success]

    def filter(self, operation_name: str | None = None, success: bool | None = None) -> list[MemoryEntry]:
        """Filter memory entries by operation name and/or success status.

        Both filters use AND logic. If both are None, returns all entries.

        Args:
            operation_name: Optional operation name to filter by (case-insensitive).
            success: Optional success status to filter by.

        Returns:
            List of MemoryEntry objects matching all provided criteria.
        """
        if operation_name is None and success is None:
            return self.get_all_entries()

        entries = self.get_all_entries()

        if operation_name is not None:
            entries = [e for e in entries if e.operation_name.lower() == operation_name.lower()]

        if success is not None:
            entries = [e for e in entries if e.success == success]

        return entries

    def export_memory_entries(self, output_path: str) -> int:
        """Export memory entries to a file.

        Delegates to the storage layer for the actual export operation.

        Args:
            output_path: Path to the output file.

        Returns:
            Number of entries exported.

        Raises:
            IOError: If there is a problem writing to the file.
        """
        return self.storage.export_memory_entries(output_path)

    def import_memory_entries(
        self, input_path: str, overwrite: bool = False
    ) -> tuple[int, int]:
        """Import memory entries from a file.

        Delegates to the storage layer for the actual import operation.

        Args:
            input_path: Path to the input file.
            overwrite: If True, overwrite existing entries with matching IDs.

        Returns:
            Tuple of (imported_count, skipped_count).

        Raises:
            FileNotFoundError: If the input file does not exist.
            IOError: If there is a problem reading from the file.
        """
        return self.storage.import_memory_entries(input_path, overwrite)
