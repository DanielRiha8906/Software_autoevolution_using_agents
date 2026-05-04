from .output_formatter import OutputFormatter


class ImportResultFormatter(OutputFormatter):
    """Formats import operation results for console output."""

    def format(self, result: dict) -> str:
        """Format import result.

        Args:
            result: Dictionary with import statistics (imported_count, skipped_count, etc.).

        Returns:
            Formatted string with import summary.
        """
        lines = [
            "",
            f"  Imported {result['imported_count']} entries",
        ]

        if result['skipped_count'] > 0:
            lines.append(f"  Skipped {result['skipped_count']} entries:")
            lines.append(f"    - {result['duplicates_count']} duplicates")
            lines.append(f"    - {result['invalid_count']} invalid entries")

        lines.append("")

        return "\n".join(lines)
