from typing import Protocol

from ..models.operation import Operation


class CalculationEngine(Protocol):
    def calculate(self, operation: Operation, a: float, b: float) -> float: ...
