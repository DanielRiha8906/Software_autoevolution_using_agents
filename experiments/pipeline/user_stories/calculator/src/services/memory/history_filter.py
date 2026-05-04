from abc import ABC, abstractmethod

from ...models.memory_entry import MemoryEntry


class HistoryFilter(ABC):
    """Abstract interface for filtering MemoryEntry objects.

    Allows different filtering strategies to be composed and applied
    without modifying MemoryService or memory-dependent code.
    """

    @abstractmethod
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Filter a list of entries.

        Args:
            entries: List of MemoryEntry objects to filter.

        Returns:
            Filtered list of MemoryEntry objects.
        """


class OperationFilter(HistoryFilter):
    """Filter entries by operation name(s)."""

    def __init__(self, operations: list[str]) -> None:
        """Initialize with operation names to filter by.

        Args:
            operations: List of operation names (e.g., ['add', 'subtract']).
        """
        self.operations = operations

    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Return entries matching any of the specified operations."""
        return [e for e in entries if e.operation in self.operations]


class StateFilter(HistoryFilter):
    """Filter entries by success/error state."""

    def __init__(self, state: str) -> None:
        """Initialize with state to filter by.

        Args:
            state: One of 'success', 'error', or 'both'.

        Raises:
            ValueError: If state is not one of the valid values.
        """
        if state not in ["success", "error", "both"]:
            raise ValueError(
                f"Invalid state: '{state}'. Must be one of: 'success', 'error', 'both'"
            )
        self.state = state

    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Return entries matching the specified state."""
        if self.state == "both":
            return entries

        filtered = []
        for entry in entries:
            is_success = entry.result is not None and entry.error is None
            is_error = entry.result is None and entry.error is not None

            if self.state == "success" and is_success:
                filtered.append(entry)
            elif self.state == "error" and is_error:
                filtered.append(entry)

        return filtered


class CompositeFilter(HistoryFilter):
    """Compose multiple filters, applying them sequentially."""

    def __init__(self, filters: list[HistoryFilter]) -> None:
        """Initialize with a list of filters to apply in order.

        Args:
            filters: List of HistoryFilter objects.
        """
        self.filters = filters

    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Apply filters sequentially, each filter operating on the result of the previous."""
        result = entries
        for f in self.filters:
            result = f.apply(result)
        return result
