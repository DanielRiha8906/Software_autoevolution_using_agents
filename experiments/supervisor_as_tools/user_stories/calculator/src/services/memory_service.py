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
            result = self.calculator_service.calculator.calculate(operation_enum, operand_a, operand_b)
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
