from typing import Protocol


class Executable(Protocol):
    """Protocol for services that execute operations and return results."""

    def execute(self, operation: str, a: float, b: float) -> float:
        """Execute a calculation. Returns raw float result."""
        ...
