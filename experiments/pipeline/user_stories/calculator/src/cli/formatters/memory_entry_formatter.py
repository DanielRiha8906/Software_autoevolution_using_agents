from ...models.memory_entry import MemoryEntry
from .output_formatter import OutputFormatter


class MemoryEntryFormatter(OutputFormatter):
    """Formats a single MemoryEntry for console output."""

    def format(self, entry: MemoryEntry) -> str:
        """Format a single entry.

        Args:
            entry: MemoryEntry to format.

        Returns:
            Formatted string like "2 + 3 = 5  [timestamp]" or error message.
        """
        return str(entry)


class MemoryEntryListFormatter(OutputFormatter):
    """Formats a list of MemoryEntry objects for console output."""

    def __init__(self, entry_formatter: MemoryEntryFormatter | None = None) -> None:
        """Initialize with an optional entry formatter.

        Args:
            entry_formatter: Formatter for individual entries. Uses default if None.
        """
        self.entry_formatter = entry_formatter or MemoryEntryFormatter()

    def format(self, entries: list[MemoryEntry]) -> str:
        """Format a list of entries.

        Args:
            entries: List of MemoryEntry objects to format.

        Returns:
            Formatted string with numbered list of entries.
        """
        if not entries:
            return "\n  No calculations recorded yet.\n"

        lines = [""]
        for i, entry in enumerate(entries, 1):
            if entry.error:
                lines.append(
                    f"  {i}. {entry.operation} ({entry.operand_a}, {entry.operand_b}) = ERROR: {entry.error}"
                )
            else:
                formatted_entry = self.entry_formatter.format(entry)
                lines.append(f"  {i}. {formatted_entry}  [{entry.timestamp}]")
        lines.append("")

        return "\n".join(lines)
