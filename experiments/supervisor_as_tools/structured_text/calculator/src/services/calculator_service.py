import time

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator import Calculator
from .memory_service import MemoryService


class CalculatorService:
    def __init__(
        self,
        calculator: Calculator,
        storage: JsonStorage,
        memory_service: MemoryService | None = None,
    ) -> None:
        self.calculator = calculator
        self.storage = storage
        self.memory_service = memory_service

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start = time.perf_counter()
        try:
            result = self.calculator.calculate(operation, a, b)
            elapsed_ms = (time.perf_counter() - start) * 1000
            calc_result = CalculationResult(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result,
                execution_time_ms=elapsed_ms,
            )
            self.storage.save(calc_result)

            # Record successful operation to memory
            if self.memory_service:
                memory_entry = MemoryEntry(
                    operation=operation.value,
                    operand_a=a,
                    operand_b=b,
                    success=True,
                    execution_time_ms=elapsed_ms,
                    result=result,
                )
                self.memory_service.store(memory_entry)

            return calc_result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Record failed operation to memory
            if self.memory_service:
                memory_entry = MemoryEntry(
                    operation=operation.value,
                    operand_a=a,
                    operand_b=b,
                    success=False,
                    execution_time_ms=elapsed_ms,
                    error_message=str(exc),
                )
                self.memory_service.store(memory_entry)

            # Re-raise the exception so failure is still raised to caller
            raise

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
