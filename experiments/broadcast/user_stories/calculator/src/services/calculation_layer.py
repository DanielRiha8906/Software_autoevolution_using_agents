"""
Calculation Layer - Orchestrates pure calculations with timing

This layer separates calculation logic from memory/persistence concerns.
It depends on the CalculationEngine (pure arithmetic) but does not handle
memory, history, or storage directly.
"""

import time
from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from .calculation_engine import CalculationEngine


class CalculationLayer:
    """Service layer for performing calculations with execution tracking.

    This layer:
    - Orchestrates calls to the calculation engine
    - Measures execution time
    - Returns raw calculation results without persistence

    It does NOT:
    - Store results in memory or history
    - Interact with storage or persistence
    - Handle memory management
    """

    def __init__(self, engine: CalculationEngine) -> None:
        """Initialize with a calculation engine.

        Args:
            engine: CalculationEngine instance for pure arithmetic
        """
        self.engine = engine

    def perform_calculation(self, operation: Operation, a: float, b: float | None = None) -> CalculationResult:
        """Perform a calculation and return result with timing.

        Args:
            operation: The Operation to perform
            a: First operand
            b: Second operand (optional, defaults to 0 for unary operations)

        Returns:
            CalculationResult with operation, operands, result, and timing

        Raises:
            ValueError: If the operation fails or is unsupported
        """
        start_time = time.perf_counter()
        result = self.engine.calculate(operation, a, b if b is not None else 0)
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        return CalculationResult(
            operation=operation.value,
            operand_a=a,
            operand_b=b,
            result=result,
            execution_time_ms=execution_time_ms,
        )
