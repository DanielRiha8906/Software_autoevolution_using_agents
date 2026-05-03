"""Service for querying stored calculations with filtering capabilities."""

from typing import Optional
from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class QueryService:
    """Service for querying and filtering MemoryEntry records.

    Supports filtering by:
    - operation_type: specific operation name (e.g., "add", "subtract")
    - result_state: "success", "failed", or "all"
    - Can combine multiple filters in a single query
    """

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize QueryService with a MemoryService backend.

        Args:
            memory_service: MemoryService instance containing MemoryEntry objects.
        """
        self.memory_service = memory_service

    def query(
        self,
        operation_type: Optional[str] = None,
        result_state: str = "all",
    ) -> list[MemoryEntry]:
        """Query stored calculations with optional filters.

        Args:
            operation_type: Filter by operation name (e.g., "add"). None = no filter.
            result_state: Filter by result state ("success", "failed", or "all").
                         Defaults to "all" (no filter).

        Returns:
            List of matching MemoryEntry objects, in storage order.

        Raises:
            ValueError: If result_state is not "success", "failed", or "all".
        """
        if result_state not in ("success", "failed", "all"):
            raise ValueError(
                f"Invalid result_state '{result_state}'. "
                "Must be 'success', 'failed', or 'all'."
            )

        all_entries = self.memory_service.retrieve()
        results = []

        for entry in all_entries:
            # Apply operation_type filter
            if operation_type is not None:
                if entry.operation_name != operation_type.lower():
                    continue

            # Apply result_state filter
            if result_state == "success":
                if not entry.success:
                    continue
            elif result_state == "failed":
                if entry.success:
                    continue

            results.append(entry)

        return results

    def query_by_operation(self, operation_type: str) -> list[MemoryEntry]:
        """Query calculations by operation type.

        Args:
            operation_type: Operation name to filter by (e.g., "add").

        Returns:
            List of matching MemoryEntry objects.
        """
        return self.query(operation_type=operation_type)

    def query_by_state(self, result_state: str) -> list[MemoryEntry]:
        """Query calculations by result state.

        Args:
            result_state: "success", "failed", or "all".

        Returns:
            List of matching MemoryEntry objects.

        Raises:
            ValueError: If result_state is invalid.
        """
        return self.query(result_state=result_state)

    def format_results(self, results: list[MemoryEntry]) -> str:
        """Format query results for display.

        Args:
            results: List of MemoryEntry objects to format.

        Returns:
            Formatted string representation of results.
        """
        if not results:
            return "No calculations found matching the query."

        output = []
        for i, entry in enumerate(results, 1):
            status = "SUCCESS" if entry.success else "FAILED"
            if entry.success:
                output.append(
                    f"  {i}. {entry.operation_name}: {entry.operand_a} "
                    f"op {entry.operand_b} → {entry.result} "
                    f"[{status}, {entry.execution_time_ms:.2f}ms, {entry.execution_timestamp}]"
                )
            else:
                output.append(
                    f"  {i}. {entry.operation_name}: {entry.operand_a} "
                    f"op {entry.operand_b} → ERROR: {entry.error_message} "
                    f"[{status}, {entry.execution_time_ms:.2f}ms, {entry.execution_timestamp}]"
                )
        return "\n".join(output)
