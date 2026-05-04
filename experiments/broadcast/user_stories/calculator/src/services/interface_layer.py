"""
Interface Layer - Orchestrates calculation and memory services

This layer coordinates calls between the CalculationLayer and MemoryLayer,
serving as the primary interface for the CLI layer. It depends on both
the calculation and memory layers but keeps them independent of each other.
"""

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import ResultEntry, ErrorEntry, MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculation_layer import CalculationLayer
from .memory_layer import MemoryLayer


class InterfaceLayer:
    """Service layer that orchestrates calculation and memory operations.

    This layer:
    - Coordinates the CalculationLayer and MemoryLayer
    - Performs calculations and stores results
    - Provides unified interface for CLI consumption
    - Handles both raw calculation results and memory entry tracking

    It does NOT:
    - Perform calculations directly (delegates to CalculationLayer)
    - Manage memory directly (delegates to MemoryLayer)
    - Define UI/CLI logic
    """

    def __init__(self, calculation_layer: CalculationLayer, memory_layer: MemoryLayer, storage: JsonStorage) -> None:
        """Initialize with calculation and memory layers.

        Args:
            calculation_layer: CalculationLayer for performing calculations
            memory_layer: MemoryLayer for managing memory/history
            storage: JsonStorage for direct persistence of calculation results
        """
        self.calculation_layer = calculation_layer
        self.memory_layer = memory_layer
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float | None = None) -> CalculationResult:
        """Perform a calculation and persist as CalculationResult.

        Args:
            operation: The Operation to perform
            a: First operand
            b: Second operand (optional)

        Returns:
            CalculationResult with operation, operands, result, and timing

        Raises:
            ValueError: If the operation fails or is unsupported
        """
        # Perform pure calculation
        result = self.calculation_layer.perform_calculation(operation, a, b)

        # Store as CalculationResult (not as memory entry)
        self.storage.save(result)

        return result

    def perform_with_memory(self, operation: Operation, a: float, b: float | None = None) -> ResultEntry | ErrorEntry:
        """Perform a calculation, capture both success and error, and return memory entry.

        This method allows the caller to handle errors as memory entries rather than exceptions.

        Args:
            operation: The Operation to perform
            a: First operand
            b: Second operand (optional)

        Returns:
            ResultEntry on success, ErrorEntry on failure

        Raises:
            ValueError: Always re-raised after storing as ErrorEntry
        """
        import time
        start_time = time.perf_counter()
        try:
            result = self.calculation_layer.engine.calculate(operation, a, b if b is not None else 0)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            operands = [a] if b is None else [a, b]
            entry = ResultEntry(
                operation=operation.value,
                operands=operands,
                result=result,
                execution_time_ms=execution_time_ms,
            )
            # Store directly to storage (not just to memory layer)
            self.storage.save(entry)
            return entry
        except ValueError as exc:
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            operands = [a] if b is None else [a, b]
            entry = ErrorEntry(
                operation=operation.value,
                operands=operands,
                error_message=str(exc),
                execution_time_ms=execution_time_ms,
            )
            # Store directly to storage (not just to memory layer)
            self.storage.save(entry)
            raise

    def get_history(self) -> list[CalculationResult]:
        """Get the calculation history.

        Returns:
            List of CalculationResult objects from storage
        """
        from ..storage.json_storage import JsonStorage
        # This gets the raw calculation results (not memory entries)
        # We need to check what storage has
        if hasattr(self.memory_layer.storage, 'load_all'):
            return self.memory_layer.storage.load_all()
        return []

    def get_memory_history(self) -> list[MemoryEntry]:
        """Get the memory entry history.

        Returns:
            List of MemoryEntry objects (both ResultEntry and ErrorEntry)
        """
        return self.memory_layer.retrieve()
