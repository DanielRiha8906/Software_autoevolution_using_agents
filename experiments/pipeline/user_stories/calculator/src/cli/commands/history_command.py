from ...services.memory_service import MemoryService
from ...services.memory.history_filter import HistoryFilter
from ..formatters.output_formatter import OutputFormatter
from ..formatters.memory_entry_formatter import MemoryEntryListFormatter
from .command import Command


class HistoryCommand(Command):
    """Command to display calculation history."""

    def __init__(
        self,
        memory_service: MemoryService,
        formatter: OutputFormatter | None = None,
        filters: list[HistoryFilter] | None = None,
    ) -> None:
        """Initialize history command.

        Args:
            memory_service: MemoryService to retrieve history from.
            formatter: OutputFormatter for history. Uses MemoryEntryListFormatter if None.
            filters: Optional list of HistoryFilter objects to apply.
        """
        self.memory_service = memory_service
        self.formatter = formatter or MemoryEntryListFormatter()
        self.filters = filters

    def execute(self) -> None:
        """Execute the command and print formatted history."""
        history = self.memory_service.filter(self.filters)
        output = self.formatter.format(history)
        print(output)
