import time
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import ResultEntry, ErrorEntry, MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator import Calculator


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start_time = time.perf_counter()
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
        return calc_result

    def perform_with_memory(self, operation: Operation, a: float, b: float) -> ResultEntry | ErrorEntry:
        """
        Perform a calculation and return a memory entry (success or error).
        This method captures both successful and failed operations.
        """
        start_time = time.perf_counter()
        try:
            result = self.calculator.calculate(operation, a, b)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            entry = ResultEntry(
                operation=operation.value,
                operands=[a, b],
                result=result,
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(entry)
            return entry
        except ValueError as exc:
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            entry = ErrorEntry(
                operation=operation.value,
                operands=[a, b],
                error_message=str(exc),
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(entry)
            raise

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()

    def get_memory_history(self) -> list[MemoryEntry]:
        """Get the full memory entry history (both results and errors)."""
        return self.storage.load_memory_all()
