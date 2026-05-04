"""Service integration bridge for the GUI.

This module provides the GUIController class which bridges GUI components
to business logic services (CalculatorService, MemoryService, StatisticsService).
All actual calculation and history logic is delegated to services.
"""

from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService
from ..services.statistics_service import StatisticsService


class GUIController:
    """Bridge between GUI components and business logic services.

    No business logic is implemented here; all operations delegate to services.
    """

    def __init__(
        self,
        calculator_service: CalculatorService,
        memory_service: MemoryService,
        statistics_service: StatisticsService,
    ) -> None:
        """Initialize the controller with service dependencies.

        Args:
            calculator_service: Service for calculations.
            memory_service: Service for history management.
            statistics_service: Service for statistics calculation.
        """
        self.calculator_service = calculator_service
        self.memory_service = memory_service
        self.statistics_service = statistics_service

    def perform_calculation(self, operation_str: str, a: float, b: float) -> MemoryEntry:
        """Perform a calculation via the calculator service.

        Args:
            operation_str: Operation name (e.g., 'add', 'subtract').
            a: First operand.
            b: Second operand.

        Returns:
            MemoryEntry with result or error information.

        Raises:
            ValueError: If operation_str is not a valid operation.
        """
        operation = Operation.from_string(operation_str)
        return self.calculator_service.perform(operation, a, b)

    def get_history(self) -> list[MemoryEntry]:
        """Get all calculation history.

        Returns:
            List of all MemoryEntry objects.
        """
        return self.calculator_service.get_history()

    def filter_history(
        self,
        operations: list[str] | None = None,
        state: str | None = None,
    ) -> list[MemoryEntry]:
        """Filter calculation history by operations and/or state.

        Args:
            operations: List of operation names to filter by. None means include all.
            state: One of 'success', 'error', or 'both'. None is treated as 'both'.

        Returns:
            List of MemoryEntry objects matching criteria.

        Raises:
            ValueError: If state is invalid.
        """
        return self.calculator_service.filter_history(operations, state)

    def get_statistics(self):
        """Get calculation statistics.

        Returns:
            CalculationStatistics object with aggregated metrics.
        """
        return self.statistics_service.calculate_statistics()
