from typing import Protocol

from ..models.calculation_result import CalculationResult


class StorageBackend(Protocol):
    def save(self, result: CalculationResult) -> None: ...
    def load_all(self) -> list[CalculationResult]: ...
