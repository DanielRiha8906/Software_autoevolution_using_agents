from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator import Calculator


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> MemoryEntry:
        try:
            result = self.calculator.calculate(operation, a, b)
            entry = MemoryEntry(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result,
                error=None,
                error_type=None,
            )
        except Exception as e:
            entry = MemoryEntry(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=None,
                error=str(e),
                error_type=type(e).__name__,
            )
        self.storage.save(entry)
        return entry

    def get_history(self) -> list[MemoryEntry]:
        return self.storage.load_all()
