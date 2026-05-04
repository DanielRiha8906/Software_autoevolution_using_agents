"""Calculator CLI - command-line interface.

This module provides the CLI interface and is decoupled from the
calculation engine and storage layers.
"""

import sys

from ..interface.user_interface import CLIBase
from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.scientific_calculator import ScientificCalculator


class CalculatorCLI(CLIBase):
    """Command-line interface for the calculator.

    Implements the UserInterface protocol and provides both interactive
    and command-mode access to calculator functionality.

    Layer responsibilities:
    - Interface: User interactions, menus, prompts
    - Service: Calculation orchestration (CalculatorService)
    - Core: Pure calculation logic (accessed via CalculatorService)
    """

    _MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square Root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    def __init__(self, service: CalculatorService) -> None:
        """Initialize the CLI with a CalculatorService.

        Args:
            service: The CalculatorService that performs calculations
        """
        self.service = service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        """Run the calculator in interactive mode with menus and prompts."""
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            scientific_opt = len(self._MENU) + 2
            exit_opt    = len(self._MENU) + 3

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(scientific_opt):
                self._run_scientific_menu()
                continue

            operation = self._resolve_menu_choice_as_operation(choice)
            if operation is None:
                print("Invalid choice — try again.\n")
                continue

            a = self._prompt_number("Enter first number: ")
            if a is None:
                continue
            b = self._prompt_number("Enter second number: ")
            if b is None:
                continue

            try:
                result = self.service.perform(operation, a, b)
                print(f"\n  Result: {result}\n")
            except (ValueError, Exception) as exc:
                print(f"\n  Error: {str(exc)}\n")

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        """Run the calculator in command mode (one-shot operation).

        Args:
            operation_str: The operation name (e.g., "add")
            a: First operand
            b: Second operand
        """
        try:
            operation = Operation.from_string(operation_str)
            result = self.service.perform(operation, a, b)
            print(result)
        except (ValueError, Exception) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_scientific_menu(self) -> None:
        """Handle the scientific operations submenu."""
        scientific_ops = ["Sin", "Cos", "Tan", "Log (base 10)", "Ln (natural log)", "Exp"]
        print("\nScientific Operations:")
        for i, op in enumerate(scientific_ops, 1):
            print(f"  {i}. {op}")
        print(f"  {len(scientific_ops) + 1}. Back to main menu")

        choice = input("Choose operation: ").strip()
        try:
            idx = int(choice) - 1
            if idx == len(scientific_ops):
                return
            if 0 <= idx < len(scientific_ops):
                op_name = ["sin", "cos", "tan", "log", "ln", "exp"][idx]
                x = self._prompt_number("Enter value: ")
                if x is None:
                    return
                calc = ScientificCalculator()
                dispatch = {
                    "sin": calc.sin,
                    "cos": calc.cos,
                    "tan": calc.tan,
                    "log": calc.log,
                    "ln": calc.ln,
                    "exp": calc.exp,
                }
                result = dispatch[op_name](x)
                print(f"\n  Result: {result}\n")
            else:
                print("Invalid choice — try again.\n")
        except ValueError:
            print("Invalid choice — try again.\n")
        except Exception as exc:
            print(f"\n  Error: {str(exc)}\n")

    def _print_menu(self) -> None:
        """Display the main menu."""
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. Scientific operations")
        print(f"  {len(self._MENU) + 3}. Exit")

    def _resolve_menu_choice_as_operation(self, choice: str) -> Operation | None:
        """Resolve a menu choice (1-based index) to an Operation.

        Args:
            choice: The user's menu choice

        Returns:
            The Operation if valid, None otherwise
        """
        idx = self._resolve_menu_choice(choice, len(self._MENU))
        if idx is not None:
            return self._MENU[idx][0]
        return None

    def _show_history(self) -> None:
        """Display the calculation history."""
        history = self.service.get_history()
        if not history:
            print("\n  No calculations recorded yet.\n")
            return
        print()
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry}  [{entry.timestamp}]")
        print()
