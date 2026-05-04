import time
from typing import TYPE_CHECKING, Optional
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from ..protocols import CalculationEngine, HistoryStorage

if TYPE_CHECKING:
    pass


class CalculatorService:
    """Orchestrates the three core components: calculation, history, and storage.

    Uses protocol-based dependency injection to decouple from concrete implementations.
    Depends on CalculationEngine and HistoryStorage protocols, not concrete classes.
    """

    def __init__(
        self,
        calculator: CalculationEngine,
        storage: JsonStorage,
        memory_service: Optional[HistoryStorage] = None,
    ) -> None:
        self.calculator = calculator
        self.storage = storage
        self.memory_service = memory_service

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start_time = time.perf_counter()
        try:
            result = self.calculator.calculate(operation, a, b)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            calc_result = CalculationResult(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result,
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(calc_result)

            # Also store as MemoryEntry if memory_service is available
            if self.memory_service is not None:
                memory_entry = MemoryEntry(
                    operation_name=operation.value,
                    operand_a=a,
                    operand_b=b,
                    result=result,
                    success=True,
                    error_message=None,
                    execution_time_ms=execution_time_ms,
                )
                self.memory_service.store(memory_entry)

            return calc_result
        except Exception as exc:
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            # Store as MemoryEntry even on failure if memory_service is available
            if self.memory_service is not None:
                memory_entry = MemoryEntry(
                    operation_name=operation.value,
                    operand_a=a,
                    operand_b=b,
                    result=None,
                    success=False,
                    error_message=str(exc),
                    execution_time_ms=execution_time_ms,
                )
                self.memory_service.store(memory_entry)

            # Re-raise to preserve original error handling
            raise

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
