from ...services.statistics_service import StatisticsService
from ..formatters.output_formatter import OutputFormatter
from ..formatters.statistics_formatter import StatisticsFormatter
from .command import Command


class StatisticsCommand(Command):
    """Command to display calculation statistics."""

    def __init__(
        self,
        statistics_service: StatisticsService,
        formatter: OutputFormatter | None = None,
    ) -> None:
        """Initialize statistics command.

        Args:
            statistics_service: StatisticsService to calculate statistics.
            formatter: OutputFormatter for statistics. Uses StatisticsFormatter if None.
        """
        self.statistics_service = statistics_service
        self.formatter = formatter or StatisticsFormatter()

    def execute(self) -> None:
        """Execute the command and print formatted statistics."""
        stats = self.statistics_service.calculate_statistics()
        output = self.formatter.format(stats)
        print(output)
