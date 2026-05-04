import sys
from json import JSONDecodeError

from ...services.import_export_service import ImportExportService
from ..formatters.output_formatter import OutputFormatter
from ..formatters.import_result_formatter import ImportResultFormatter
from .command import Command


class ImportCommand(Command):
    """Command to import calculation history from a JSON file."""

    def __init__(
        self,
        import_export_service: ImportExportService,
        filepath: str,
        mode: str = "merge",
        formatter: OutputFormatter | None = None,
        exit_on_error: bool = True,
    ) -> None:
        """Initialize import command.

        Args:
            import_export_service: ImportExportService to perform import.
            filepath: Source JSON file path.
            mode: "merge" (append) or "replace" (overwrite all).
            formatter: OutputFormatter for results. Uses ImportResultFormatter if None.
            exit_on_error: If True, call sys.exit(1) on error. If False, print to stderr only.
        """
        self.import_export_service = import_export_service
        self.filepath = filepath
        self.mode = mode
        self.formatter = formatter or ImportResultFormatter()
        self.exit_on_error = exit_on_error

    def execute(self) -> None:
        """Execute the command and import history from file.

        Raises:
            SystemExit: If exit_on_error is True and an error occurs.
        """
        try:
            result = self.import_export_service.import_history(
                self.filepath,
                mode=self.mode,
            )
            output = self.formatter.format(result)
            print(output)
        except (ValueError, OSError, JSONDecodeError) as e:
            print(f"Import error: {e}", file=sys.stderr)
            if self.exit_on_error:
                sys.exit(1)
