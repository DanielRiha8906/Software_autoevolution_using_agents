import sys

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService


class CalculatorCLI:
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

    def __init__(self, service: CalculatorService, memory_service: MemoryService | None = None) -> None:
        self.service = service
        self.memory_service = memory_service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            memory_opt  = len(self._MENU) + 2
            filter_op_opt = len(self._MENU) + 3
            filter_status_opt = len(self._MENU) + 4
            exit_opt    = len(self._MENU) + 5

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(memory_opt):
                self._show_memory()
                continue

            if choice == str(filter_op_opt):
                self._filter_memory_by_operation()
                continue

            if choice == str(filter_status_opt):
                self._filter_memory_by_status()
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. View memory")
        print(f"  {len(self._MENU) + 3}. Filter memory by operation")
        print(f"  {len(self._MENU) + 4}. Filter memory by status")
        print(f"  {len(self._MENU) + 5}. Exit")

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

    def show_memory(self) -> None:
        """Display all stored memory entries (used in one-shot CLI mode)."""
        if self.memory_service is None:
            print("Memory service not available.")
            return
        self._show_memory()

    def _show_memory(self) -> None:
        """Display all memory entries (internal method for interactive menu)."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        entries = self.memory_service.retrieve_all()
        if not entries:
            print("\n  No memory entries recorded yet.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()

    def _filter_memory_by_operation(self) -> None:
        """Filter and display memory entries by operation name."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        operation_name = input("\n  Enter operation name (add, subtract, multiply, divide, square, sqrt, power, modulo): ").strip()
        entries = self.memory_service.filter_by_operation(operation_name)
        if not entries:
            print(f"\n  No memory entries match operation '{operation_name}'.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()

    def _filter_memory_by_status(self) -> None:
        """Filter and display memory entries by success status."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        print("\n  Filter by status:")
        print("    1. Successful")
        print("    2. Failed")
        choice = input("  Choose: ").strip()
        if choice == "1":
            success = True
            status_label = "successful"
        elif choice == "2":
            success = False
            status_label = "failed"
        else:
            print("  Invalid choice.\n")
            return
        entries = self.memory_service.filter_by_success(success)
        if not entries:
            print(f"\n  No memory entries match status '{status_label}'.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()
