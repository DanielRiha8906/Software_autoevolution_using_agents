from pathlib import Path

from .calculator import Calculator
from .calculator_service import CalculatorService
from .memory_service import MemoryService
from ..storage.json_storage import JsonStorage
from ..storage.memory_json_storage import MemoryJsonStorage


def build_service() -> tuple[CalculatorService, MemoryService]:
    """Build and wire the calculator service with its dependencies.

    This factory function orchestrates the dependency injection for the calculator
    application. It creates and wires:
    - JsonStorage for calculation results (artifacts/calculations.json)
    - MemoryJsonStorage for operation memory (artifacts/memory.json)
    - MemoryService using the memory storage
    - CalculatorService with Calculator, JsonStorage, and MemoryService

    The paths are relative to the src/ directory parent (the project root).

    Returns:
        Tuple of (CalculatorService, MemoryService) ready for use.
    """
    storage_path = Path(__file__).parent.parent.parent / "artifacts" / "calculations.json"
    memory_storage_path = Path(__file__).parent.parent.parent / "artifacts" / "memory.json"

    memory_storage = MemoryJsonStorage(memory_storage_path)
    memory_service = MemoryService(memory_storage)
    calc_service = CalculatorService(
        Calculator(), JsonStorage(storage_path), memory_service
    )
    return calc_service, memory_service
