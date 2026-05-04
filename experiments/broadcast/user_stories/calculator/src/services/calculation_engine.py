"""
Calculation Engine Layer - Pure Arithmetic Logic

This module defines the structural interface for the calculation engine using
Python typing.Protocol, which handles all arithmetic operations without memory
or history concerns. The calculation engine is a stateless, pure function layer
that accepts operands and operations, returning results.
"""

from typing import Protocol
from ..models.operation import Operation


class CalculationEngine(Protocol):
    """Protocol for the calculation engine layer.

    The calculation engine is responsible for:
    - Performing pure arithmetic calculations
    - Validating operands and operations
    - Raising appropriate errors for invalid operations

    It does NOT:
    - Store results in memory or history
    - Track execution time
    - Interact with storage or persistence

    Any implementation must provide a calculate method.
    """

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        """Execute a calculation operation.

        Args:
            operation: The Operation to perform (from Operation enum)
            a: First operand
            b: Second operand (may be ignored for unary operations)

        Returns:
            The result of the operation

        Raises:
            ValueError: If the operation is not supported or parameters are invalid
        """
        ...
