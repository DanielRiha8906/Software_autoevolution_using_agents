import time

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.storage_protocol import StorageInterface
from .calculator import Calculator
from .memory_repository import MemoryRepository
from .event_recorder import EventRecorder


class CalculatorService:
    def __init__(
        self,
        calculator: Calculator,
        storage: StorageInterface,
        memory_service: MemoryRepository | None = None,
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
            recorder = EventRecorder(self.storage, self.memory_service)
            recorder.record_success(calc_result, elapsed_ms)

            return calc_result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            recorder = EventRecorder(self.storage, self.memory_service)
            recorder.record_failure(operation.value, a, b, elapsed_ms, str(exc))

            # Re-raise the exception so failure is still raised to caller
            raise

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
