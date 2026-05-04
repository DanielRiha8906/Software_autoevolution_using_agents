"""User interface protocol and base classes.

This module defines the contract for user interfaces and provides
a base class for CLI-based interactions.
"""

from typing import Protocol

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult


class UserInterface(Protocol):
    """Protocol for user interface implementations.

    Any implementation must support both interactive and command modes.
    """

    def run_interactive(self) -> None:
        """Run the interface in interactive mode (menus, prompts, etc)."""
        ...

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        """Run the interface in command mode (one-shot operation)."""
        ...


class CLIBase:
    """Base class for command-line interfaces.

    Provides common utilities for CLI implementations, such as menu
    rendering, number prompts, and operation resolution.
    """

    def _resolve_menu_choice(self, choice: str, menu_length: int) -> int | None:
        """Resolve a user's numeric menu choice to an index.

        Args:
            choice: The raw user input (should be a string number)
            menu_length: Number of items in the menu

        Returns:
            The 0-based index if valid, None otherwise
        """
        try:
            idx = int(choice) - 1
            if 0 <= idx < menu_length:
                return idx
        except ValueError:
            pass
        return None

    def _prompt_number(self, prompt: str) -> float | None:
        """Prompt the user for a number input.

        Args:
            prompt: The prompt text to display

        Returns:
            The parsed float if valid, None if user input is invalid
        """
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  Invalid number: '{raw}' — please enter a numeric value.")
            return None
