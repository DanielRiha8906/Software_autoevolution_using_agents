import time

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.json_storage import JsonStorage
from ..core.calculator import Calculator
from ..core.interfaces import CalculationEngine
from ..storage.interfaces import StorageBackend


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start = time.time()
        result = self.calculator.calculate(operation, a, b)
        end = time.time()
        execution_time_ms = (end - start) * 1000

        calc_result = CalculationResult(
            operation=operation.value,
            operand_a=a,
            operand_b=b,
            result=result,
            execution_time_ms=execution_time_ms,
        )
        self.storage.save(calc_result)
        return calc_result

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
