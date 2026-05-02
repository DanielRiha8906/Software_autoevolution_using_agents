import time
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.json_storage import JsonStorage
from .calculator import Calculator


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, *args: float) -> CalculationResult:
        start_time = time.perf_counter()
        result = self.calculator.calculate(operation, *args)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        # Determine operand_b based on operation type (unary vs binary)
        operand_a = args[0]
        operand_b = args[1] if len(args) > 1 else None

        calc_result = CalculationResult(
            operation=operation.value,
            operand_a=operand_a,
            operand_b=operand_b,
            result=result,
            execution_time_ms=elapsed_ms,
        )
        self.storage.save(calc_result)
        return calc_result

    def get_history(self) -> list[CalculationResult]:
        return self.storage.load_all()
