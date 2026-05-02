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
        start_time = time.perf_counter()
        if operation.is_unary():
            result = self.calculator.calculate_unary(operation, a)
        else:
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

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
