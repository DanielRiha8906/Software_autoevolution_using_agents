import time

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator_service import CalculatorService


class MemoryService:
    """
    Service that wraps CalculatorService with memory persistence for both success and error cases.

    Tracks all calculation attempts (successful and failed) in persistent storage,
    providing a complete history of calculator operations with error details.
    """

    def __init__(self, calculator_service: CalculatorService, storage: JsonStorage) -> None:
        """
        Initialize MemoryService with a calculator service and storage backend.

        Args:
            calculator_service: CalculatorService instance for performing calculations
            storage: JsonStorage instance for persisting memory entries
        """
        self.calculator_service = calculator_service
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
        """
        Perform a calculation and record the outcome (success or error) to memory.

        On successful calculation:
        - Calls calculator_service.perform() to get result
        - Creates MemoryEntry with status="success"
        - Saves entry to storage
        - Returns the CalculationResult

        On ValueError (e.g., division by zero):
        - Creates MemoryEntry with status="error"
        - Saves entry to storage
        - Re-raises the ValueError

        Args:
            operation: Operation to perform (add, subtract, multiply, divide)
            a: First operand
            b: Second operand

        Returns:
            CalculationResult from the calculator_service

        Raises:
            ValueError: If the operation fails (e.g., division by zero)
        """
        start_time = time.perf_counter()
        try:
            result = self.calculator_service.perform(operation, a, b)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Create and save successful memory entry
            entry = MemoryEntry.success(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                result=result.result,
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(entry)

            return result
        except ValueError as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Create and save error memory entry
            entry = MemoryEntry.error(
                operation=operation.value,
                operand_a=a,
                operand_b=b,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
            )
            self.storage.save(entry)

            raise

    def store(self, entry: MemoryEntry) -> None:
        """
        Explicitly store a MemoryEntry to persistent storage.

        Args:
            entry: MemoryEntry instance to save
        """
        self.storage.save(entry)

    def retrieve_all(self) -> list[MemoryEntry]:
        """
        Retrieve all memory entries from persistent storage.

        Returns:
            List of MemoryEntry objects, empty list if no entries exist
        """
        raw_entries = self.storage.load_all()
        return [MemoryEntry.from_dict(entry.to_dict()) for entry in raw_entries]

    def get_history(self) -> list[CalculationResult]:
        """
        Get the calculation history by delegating to calculator_service.

        Returns:
            List of CalculationResult objects from the underlying calculator_service
        """
        return self.calculator_service.get_history()
