from ...services.memory_service import MemoryService
from ...services.memory.history_filter import HistoryFilter
from ..formatters.output_formatter import OutputFormatter
from ..formatters.memory_entry_formatter import MemoryEntryListFormatter
from .command import Command


class FilterCommand(Command):
    """Command to display filtered calculation history."""

    def __init__(
        self,
        memory_service: MemoryService,
        filters: list[HistoryFilter],
        formatter: OutputFormatter | None = None,
    ) -> None:
        """Initialize filter command.

        Args:
            memory_service: MemoryService to retrieve history from.
            filters: List of HistoryFilter objects to apply.
            formatter: OutputFormatter for history. Uses MemoryEntryListFormatter if None.
        """
        self.memory_service = memory_service
        self.filters = filters
        self.formatter = formatter or MemoryEntryListFormatter()

    def execute(self) -> None:
        """Execute the command and print filtered history."""
        history = self.memory_service.filter(self.filters)

        if not history:
            print("\n  No matching calculations found.\n")
            return

        output = self.formatter.format(history)
        print(output)
