import time
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.json_storage import JsonStorage
from .calculator import Calculator


class CalculatorService:
    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        self.calculator = calculator
        self.storage = storage

    def execute(self, operation: str, a: float, b: float) -> float:
        """Execute a calculation and return the raw float result.

        This is the bare execution method that performs the operation without
        wrapping the result. It converts the string operation name to an Operation
        enum and delegates to the calculator.

        Args:
            operation: Operation name as a string (e.g., "add", "subtract").
            a: First operand.
            b: Second operand.

        Returns:
            Raw float result of the calculation.

        Raises:
            ValueError: If the operation is invalid or the calculation fails.
        """
        operation_enum = Operation.from_string(operation)
        return self.calculator.calculate(operation_enum, a, b)

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        start_time = time.perf_counter()
        result = self.calculator.calculate(operation, a, b)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
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
        all_records = self.storage.load_all()
        return [r for r in all_records if isinstance(r, CalculationResult)]
