from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import ResultEntry, ErrorEntry, MemoryEntry
from ..storage.json_storage import JsonStorage
from .calculator import Calculator
from .calculation_layer import CalculationLayer
from .memory_layer import MemoryLayer
from .interface_layer import InterfaceLayer


class CalculatorService:
    """Service for calculator operations using layered architecture.

    This service orchestrates three distinct layers:
    - CalculationLayer: Pure arithmetic logic
    - MemoryLayer: Data persistence and history management
    - InterfaceLayer: Coordinates the above layers

    All operations delegate to InterfaceLayer, which ensures clean separation
    of concerns while maintaining backward compatibility.
    """

    def __init__(self, calculator: Calculator, storage: JsonStorage) -> None:
        """Initialize with a calculator engine and storage.

        Args:
            calculator: Calculator instance for pure arithmetic
            storage: JsonStorage instance for persistence
        """
        # Create the three layers
        self.calculation_layer = CalculationLayer(calculator)
        self.memory_layer = MemoryLayer(storage)
        self.interface_layer = InterfaceLayer(self.calculation_layer, self.memory_layer, storage)

        # Keep references for backward compatibility
        self.calculator = calculator
        self.storage = storage

    def perform(self, operation: Operation, a: float, b: float | None = None) -> CalculationResult:
        """Perform a calculation and persist the result.

        Args:
            operation: The Operation to perform
            a: First operand
            b: Second operand (optional, defaults to 0 for unary operations)

        Returns:
            CalculationResult with operation, operands, result, and timing

        Raises:
            ValueError: If the operation fails or is unsupported
        """
        return self.interface_layer.perform(operation, a, b)

    def perform_with_memory(self, operation: Operation, a: float, b: float | None = None) -> ResultEntry | ErrorEntry:
        """Perform a calculation and return a memory entry (success or error).

        This method captures both successful and failed operations.

        Args:
            operation: The Operation to perform
            a: First operand
            b: Second operand (optional)

        Returns:
            ResultEntry on success, ErrorEntry on failure

        Raises:
            ValueError: If the operation fails (after storing as ErrorEntry)
        """
        return self.interface_layer.perform_with_memory(operation, a, b)

    def get_history(self) -> list[CalculationResult]:
        """Get the calculation history.

        Returns:
            List of CalculationResult objects
        """
        return self.storage.load_all()

    def get_memory_history(self) -> list[MemoryEntry]:
        """Get the full memory entry history (both results and errors).

        Returns:
            List of MemoryEntry objects
        """
        return self.storage.load_memory_all()
