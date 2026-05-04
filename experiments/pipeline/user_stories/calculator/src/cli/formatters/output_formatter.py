from abc import ABC, abstractmethod
from typing import Any


class OutputFormatter(ABC):
    """Abstract interface for formatting data to strings.

    Decouples data models from presentation logic, allowing different
    output formats (console, JSON, HTML, etc.) without changing data layers.
    """

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data into a string representation.

        Args:
            data: Data to format (type depends on concrete formatter).

        Returns:
            Formatted string ready for output.
        """
