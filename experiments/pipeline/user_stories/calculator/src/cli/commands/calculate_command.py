import sys

from ...models.operation import Operation
from ...services.calculator_service import CalculatorService
from .command import Command


class CalculateCommand(Command):
    """Command to perform a single calculation."""

    def __init__(
        self,
        calculator_service: CalculatorService,
        operation_str: str,
        a: float,
        b: float,
    ) -> None:
        """Initialize calculate command.

        Args:
            calculator_service: CalculatorService to perform the calculation.
            operation_str: Operation name (e.g., "add", "multiply").
            a: First operand.
            b: Second operand.
        """
        self.calculator_service = calculator_service
        self.operation_str = operation_str
        self.a = a
        self.b = b

    def execute(self) -> None:
        """Execute the command and print result."""
        try:
            operation = Operation.from_string(self.operation_str)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        result = self.calculator_service.perform(operation, self.a, self.b)
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)
        else:
            print(result)
