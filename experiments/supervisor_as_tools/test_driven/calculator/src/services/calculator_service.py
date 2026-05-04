import time
from typing import Optional

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator import Calculator
from .memory_service import MemoryService


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage, memory_service: Optional[MemoryService] = None) -> None:
        self.calculator = calculator
        self.storage = storage
        self.memory_service = memory_service

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start_time = time.perf_counter()
        try:
            result = self.calculator.calculate(operation, a, b)
            elapsed_seconds = time.perf_counter() - start_time
            execution_time_ms = round(elapsed_seconds * 1000, 2)

            # Create MemoryEntry on success
            memory_entry = MemoryEntry(
                operation=operation.value,
                operands=[a, b],
                result=result,
                success=True,
                execution_time_ms=execution_time_ms,
            )
            if self.memory_service is not None:
                self.memory_service.store(memory_entry)

            calc_result = CalculationResult(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result,
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(calc_result)
            return calc_result
        except Exception as exc:
            elapsed_seconds = time.perf_counter() - start_time
            execution_time_ms = round(elapsed_seconds * 1000, 2)

            # Create MemoryEntry on failure
            memory_entry = MemoryEntry(
                operation=operation.value,
                operands=[a, b],
                result=None,
                success=False,
                execution_time_ms=execution_time_ms,
            )
            if self.memory_service is not None:
                self.memory_service.store(memory_entry)

            raise

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
