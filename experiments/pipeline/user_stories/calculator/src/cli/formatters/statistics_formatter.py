from ...models.statistics import CalculationStatistics
from .output_formatter import OutputFormatter


class StatisticsFormatter(OutputFormatter):
    """Formats CalculationStatistics for console output."""

    def format(self, stats: CalculationStatistics) -> str:
        """Format statistics.

        Args:
            stats: CalculationStatistics object to format.

        Returns:
            Formatted string with statistics table.
        """
        lines = [
            "",
            "  === Calculation Statistics ===",
            f"  Total Calculations: {stats.total_calculations}",
            f"  Total Errors: {stats.total_errors}",
            f"  Error Rate: {stats.error_rate_percent}%",
            f"  Average Execution Time: {stats.average_execution_time_ms} ms",
            "  Operations Count:",
        ]

        if stats.operations_count:
            for op_name in sorted(stats.operations_count.keys()):
                count = stats.operations_count[op_name]
                lines.append(f"    {op_name}: {count}")
        else:
            lines.append("    (none)")

        lines.append("")

        return "\n".join(lines)
