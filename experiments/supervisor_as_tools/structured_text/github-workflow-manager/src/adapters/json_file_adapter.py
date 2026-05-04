"""JSON file handler for import/export operations."""

import json
from pathlib import Path

from .protocols import FileHandler


class JsonFileAdapter(FileHandler):
    """JSON file handler implementation."""

    def export_to_file(self, data: dict, output_path: str) -> str:
        """Export data to a JSON file.

        Args:
            data: Data to export.
            output_path: Path to write the export file.

        Returns:
            Path to the written file.

        Raises:
            IOError: If file cannot be written.
        """
        # Write to file, creating parent directories as needed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            raise IOError(f"Failed to write export file '{output_path}': {e}")

        return str(output_file)

    def import_from_file(self, input_path: str) -> dict:
        """Import data from a JSON file.

        Args:
            input_path: Path to read the import file from.

        Returns:
            Imported data as dictionary.

        Raises:
            IOError: If file cannot be read.
            ValueError: If file contents are invalid JSON.
        """
        try:
            with open(input_path, "r") as f:
                data = json.load(f)
        except IOError as e:
            raise IOError(f"Failed to read import file '{input_path}': {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{input_path}': {e}")

        return data
