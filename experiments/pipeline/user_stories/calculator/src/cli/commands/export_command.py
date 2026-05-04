import sys
from pathlib import Path

from ...services.import_export_service import ImportExportService
from .command import Command


class ExportCommand(Command):
    """Command to export calculation history to a JSON file."""

    def __init__(
        self,
        import_export_service: ImportExportService,
        filepath: str,
        exit_on_error: bool = True,
    ) -> None:
        """Initialize export command.

        Args:
            import_export_service: ImportExportService to perform export.
            filepath: Destination JSON file path.
            exit_on_error: If True, call sys.exit(1) on error. If False, print to stderr only.
        """
        self.import_export_service = import_export_service
        self.filepath = filepath
        self.exit_on_error = exit_on_error

    def execute(self) -> None:
        """Execute the command and export history to file.

        Raises:
            SystemExit: If exit_on_error is True and an error occurs.
        """
        try:
            result = self.import_export_service.export_history(self.filepath)
            print(f"Exported {result['exported_count']} entries to {result['file_path']}")
        except (ValueError, OSError) as e:
            print(f"Export error: {e}", file=sys.stderr)
            if self.exit_on_error:
                sys.exit(1)
