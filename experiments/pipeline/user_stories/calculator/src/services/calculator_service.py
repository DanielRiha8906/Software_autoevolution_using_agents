from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from .calculator import Calculator
from .memory_service import MemoryService


class CalculatorService:
    def __init__(self, calculator: Calculator, memory_service: MemoryService) -> None:
        self.calculator = calculator
        self.memory_service = memory_service

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
        self.memory_service.store(entry)
        return entry

    def get_history(self) -> list[MemoryEntry]:
        return self.memory_service.retrieve()

    def filter_history(
        self,
        operations: list[str] | None = None,
        state: str | None = None,
    ) -> list[MemoryEntry]:
        """Filter calculation history by operations and/or state.

        Args:
            operations: List of operation names to filter by. None or empty list means include all.
            state: One of 'success', 'error', or 'both'. None is treated as 'both'.

        Returns:
            List of MemoryEntry objects matching all specified criteria, in chronological order.

        Raises:
            ValueError: If state is provided and not one of 'success', 'error', or 'both'.
        """
        return self.memory_service.filter(operations=operations, state=state)
