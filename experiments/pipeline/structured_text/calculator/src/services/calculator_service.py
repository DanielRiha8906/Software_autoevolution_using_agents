import time
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.json_storage import JsonStorage
from .calculator import Calculator


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start = time.perf_counter()
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
        return calc_result

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
