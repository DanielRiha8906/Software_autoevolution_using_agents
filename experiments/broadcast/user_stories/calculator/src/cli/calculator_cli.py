import sys

from ..models.operation import Operation
from ..models.memory_entry import ErrorEntry, ResultEntry
from ..services.calculator_service import CalculatorService


class CalculatorCLI:
    _MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    def __init__(self, service: CalculatorService) -> None:
        self.service = service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            memory_history_opt = len(self._MENU) + 1
            history_opt        = len(self._MENU) + 2
            exit_opt           = len(self._MENU) + 3

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(memory_history_opt):
                self._show_memory_history()
                continue

            if choice == str(history_opt):
                self._show_history()
                continue

            operation = self._resolve_menu_choice(choice)
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
            except ValueError as exc:
                print(f"\n  Error: {exc}\n")

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        try:
            operation = Operation.from_string(operation_str)
            result = self.service.perform(operation, a, b)
            print(result)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    def show_memory_history_command(self) -> None:
        """Show memory history and exit (one-shot mode)."""
        self._show_memory_history()

    def show_history_command(self) -> None:
        """Show calculation history and exit (one-shot mode)."""
        self._show_history()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View memory history")
        print(f"  {len(self._MENU) + 2}. View calculation history")
        print(f"  {len(self._MENU) + 3}. Exit")

    def _resolve_menu_choice(self, choice: str) -> Operation | None:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self._MENU):
                return self._MENU[idx][0]
        except ValueError:
            pass
        return None

    def _prompt_number(self, prompt: str) -> float | None:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  Invalid number: '{raw}' — please enter a numeric value.")
            return None

    def _show_history(self) -> None:
        history = self.service.get_history()
        if not history:
            print("\n  No calculations recorded yet.\n")
            return
        print()
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry}  [{entry.timestamp}]")
        print()

    def _show_memory_history(self) -> None:
        """Display the memory entry history (both results and errors)."""
        history = self.service.get_memory_history()
        if not history:
            print("\n  No operations recorded yet.\n")
            return
        print()
        for entry in history:
            self._print_memory_entry(entry)
        print()

    def _print_memory_entry(self, entry: ResultEntry | ErrorEntry) -> None:
        """Format and print a single memory entry."""
        operands_str = " ".join(str(op) for op in entry.operands)
        if isinstance(entry, ResultEntry):
            print(
                f"  #{entry.entry_id}. {entry.operation}({operands_str}) = {entry.result} "
                f"[{entry.timestamp}] ({entry.execution_time_ms:.2f}ms)"
            )
        elif isinstance(entry, ErrorEntry):
            print(
                f"  #{entry.entry_id}. {entry.operation}({operands_str}) -> ERROR: {entry.error_message} "
                f"[{entry.timestamp}] ({entry.execution_time_ms:.2f}ms)"
            )
