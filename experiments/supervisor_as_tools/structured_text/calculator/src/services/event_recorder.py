from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..storage.storage_protocol import StorageInterface
from .memory_repository import MemoryRepository


class EventRecorder:
    """Records calculation results and failures to configured storage backends.

    This class encapsulates the business logic for persisting calculation
    outcomes to multiple storage systems (calculation storage and memory service).
    It preserves the exact business logic from CalculatorService.perform().
    """

    def __init__(
        self,
        calculation_storage: StorageInterface,
        memory_repo: MemoryRepository | None = None,
    ) -> None:
        """Initialize the event recorder with storage backends.

        Args:
            calculation_storage: Storage backend for CalculationResult objects.
            memory_repo: Optional MemoryRepository for recording operations to memory.
        """
        self.calculation_storage = calculation_storage
        self.memory_repo = memory_repo

    def record_success(self, result: CalculationResult, elapsed_ms: float) -> None:
        """Record a successful calculation.

        Args:
            result: The CalculationResult object to store.
            elapsed_ms: Execution time in milliseconds (already computed).
        """
        # Save to calculation storage
        self.calculation_storage.save(result)

        # Record successful operation to memory
        if self.memory_repo:
            memory_entry = MemoryEntry(
                operation=result.operation,
                operand_a=result.operand_a,
                operand_b=result.operand_b,
                success=True,
                execution_time_ms=elapsed_ms,
                result=result.result,
            )
            self.memory_repo.store(memory_entry)

    def record_failure(
        self,
        operation: str,
        operand_a: float,
        operand_b: float,
        elapsed_ms: float,
        error_message: str,
    ) -> None:
        """Record a failed calculation.

        Args:
            operation: The operation name that was attempted.
            operand_a: The first operand.
            operand_b: The second operand.
            elapsed_ms: Execution time in milliseconds.
            error_message: The error message from the exception.
        """
        # Record failed operation to memory only
        if self.memory_repo:
            memory_entry = MemoryEntry(
                operation=operation,
                operand_a=operand_a,
                operand_b=operand_b,
                success=False,
                execution_time_ms=elapsed_ms,
                error_message=error_message,
            )
            self.memory_repo.store(memory_entry)
