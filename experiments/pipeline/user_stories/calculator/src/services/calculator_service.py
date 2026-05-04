from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from .calculator import Calculator
from .memory_service import MemoryService
from .memory.history_filter import OperationFilter, StateFilter, CompositeFilter


class CalculatorService:
    """Orchestrates calculations and persists results to memory.

    Wraps the pure Calculator engine and delegates memory operations
    to MemoryService. Creates filter objects for the new filter API.
    """

    def __init__(self, calculator: Calculator, memory_service: MemoryService) -> None:
        self.calculator = calculator
        self.memory_service = memory_service

    def perform(self, operation: Operation, a: float, b: float) -> MemoryEntry:
        """Perform a calculation and record the result.

        Args:
            operation: Operation enum value.
            a: First operand.
            b: Second operand.

        Returns:
            MemoryEntry with result or error information.
        """
        try:
            result = self.calculator.calculate(operation, a, b)
            entry = MemoryEntry(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result,
                error=None,
                error_type=None,
            )
        except Exception as e:
            entry = MemoryEntry(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=None,
                error=str(e),
                error_type=type(e).__name__,
            )
        self.memory_service.store(entry)
        return entry

    def get_history(self) -> list[MemoryEntry]:
        """Get all calculation history.

        Returns:
            List of all MemoryEntry objects.
        """
        return self.memory_service.retrieve()

    def filter_history(
        self,
        operations: list[str] | None = None,
        state: str | None = None,
    ) -> list[MemoryEntry]:
        """Filter calculation history by operations and/or state.

        Creates filter objects and applies them via the new filter API.

        Args:
            operations: List of operation names to filter by. None or empty list means include all.
            state: One of 'success', 'error', or 'both'. None is treated as 'both'.

        Returns:
            List of MemoryEntry objects matching all specified criteria, in chronological order.

        Raises:
            ValueError: If state is provided and not one of 'success', 'error', or 'both'.
        """
        # Normalize inputs
        if state is None:
            state = "both"
        if operations is None:
            operations = []

        # Build filter list
        filters: list = []

        # Add operation filter if operations specified
        if operations:
            filters.append(OperationFilter(operations))

        # Add state filter if state is not 'both'
        if state != "both":
            filters.append(StateFilter(state))

        # Apply filters via new API
        return self.memory_service.filter(filters if filters else None)
