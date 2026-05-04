"""Protocol-based interfaces for calculator components.

This module defines the three core components that separate the calculator
into independent, loosely-coupled layers using Python's typing.Protocol:

1. CalculationEngine: Performs arithmetic and scientific operations
2. HistoryStorage: Manages calculation history and memory entries
3. CalculatorUI: Provides user interface (CLI, GUI, etc.)

Protocols are lightweight structural typing interfaces that enable
loose coupling and substitutability without requiring explicit inheritance.
"""

from typing import Protocol, runtime_checkable

from .models.operation import Operation
from .models.memory_entry import MemoryEntry


@runtime_checkable
class CalculationEngine(Protocol):
    """Protocol for calculation engines.

    Defines the contract that all calculation engines must follow.
    Separates the core calculation logic from orchestration and persistence.
    Any object implementing this protocol can perform calculations.
    """

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        """Execute a calculation.

        Args:
            operation: The operation to perform.
            a: First operand.
            b: Second operand.

        Returns:
            Result of the calculation.

        Raises:
            ValueError: If the operation is invalid or inputs are invalid.
        """
        ...


@runtime_checkable
class HistoryStorage(Protocol):
    """Protocol for history/memory storage backends.

    Defines the contract for storing and retrieving calculation entries.
    Separates the concern of memory persistence from business logic.
    Implementations can vary (in-memory, file-based, database, etc.).
    """

    def store(self, entry: MemoryEntry) -> None:
        """Store a calculation entry.

        Args:
            entry: The MemoryEntry to store.
        """
        ...

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored calculation entries.

        Returns:
            List of all stored MemoryEntry objects.
        """
        ...


@runtime_checkable
class CalculatorUI(Protocol):
    """Protocol for calculator user interfaces.

    Defines the contract for any UI layer (CLI, GUI, web, etc.).
    Enables swapping different interface implementations without
    affecting calculation or storage logic.
    """

    def run_interactive(self) -> None:
        """Run the calculator in interactive mode."""
        ...

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        """Run a single calculation command.

        Args:
            operation_str: The operation name as a string.
            a: First operand.
            b: Second operand.
        """
        ...
