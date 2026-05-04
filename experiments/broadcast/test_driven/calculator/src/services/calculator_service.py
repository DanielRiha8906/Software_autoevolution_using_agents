"""Calculator service - orchestrates calculation and persistence.

This module orchestrates the interaction between the calculation engine
(core layer) and the storage layer (history/persistence).
"""

import time

from ..core.calculation_engine import BasicCalculationEngine
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..storage.json_storage import JsonStorage


class CalculatorService:
    """Orchestrates calculation engine and storage.

    Acts as a facade between the CLI/user-facing code and the underlying
    calculation engine and storage mechanisms.

    Layer responsibilities:
    - Core: Pure calculation logic (BasicCalculationEngine)
    - Service: Orchestration, timing, persistence coordination
    - Storage: History persistence (JsonStorage)
    """

    def __init__(self, calculator: BasicCalculationEngine, storage: JsonStorage) -> None:
        """Initialize the service with a calculation engine and storage.

        Args:
            calculator: The calculation engine (implements calculation logic)
            storage: The storage backend (persists results)
        """
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        """Perform a calculation and persist the result.

        Args:
            operation: The operation to perform
            a: First operand
            b: Second operand

        Returns:
            CalculationResult containing the operation details and result

        Raises:
            ValueError: If operation is not supported
            Exception: If calculation fails (e.g., division by zero)
        """
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

    def get_history(self) -> list[CalculationResult]:
        """Retrieve all stored calculation results.

        Returns:
            List of all CalculationResult objects in storage
        """
        return self.storage.load_all()
